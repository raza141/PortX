from __future__ import annotations

import re
from datetime import date

import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from django.db import transaction

# ✅ Adjust this import to your actual path
# Example you showed: refdata/taxonomy/models/...
from refdata.taxonomy.models.gics import (
    GicsEdition,
    GicsSector,
    GicsIndustryGroup,
    GicsIndustry,
    GicsSubIndustry,
)

WIKI_URL = "https://en.wikipedia.org/wiki/Global_Industry_Classification_Standard"



RE_FOOTNOTE = re.compile(r"\[\d+\]")  # remove [1], [2]...
RE_CODE_ONLY = re.compile(r"^\d{2}$|^\d{4}$|^\d{6}$|^\d{8}$")
RE_CODE_AND_NAME = re.compile(r"^(\d{2}|\d{4}|\d{6}|\d{8})\s+(.*)$")


def clean_cell(txt: str) -> str:
    txt = RE_FOOTNOTE.sub("", txt or "").strip()
    txt = re.sub(r"\s+", " ", txt)
    return txt


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def find_gics_table(soup: BeautifulSoup):
    """
    Robustly find the GICS classification table by matching header labels.
    Wikipedia HTML structure changes, so avoid relying on section ids.
    """
    for tbl in soup.find_all("table"):
        # Look at first few rows for header cells
        th_texts = []
        for tr in tbl.find_all("tr", limit=3):
            ths = tr.find_all("th")
            th_texts.extend([norm(th.get_text(" ", strip=True)) for th in ths])

        header_blob = " | ".join(th_texts)
        if (
            "sector" in header_blob
            and "industry group" in header_blob
            and "industry" in header_blob
            and ("sub-industry" in header_blob or "sub industry" in header_blob)
        ):
            return tbl

    # Fallback: find "Classification" headline and take next table
    headline = soup.find("span", class_="mw-headline", string=re.compile(r"^classification$", re.I))
    if headline:
        h = headline.find_parent(["h2", "h3"])
        if h:
            nxt = h.find_next("table")
            if nxt:
                return nxt

    return None


class Command(BaseCommand):
    help = "Load full GICS hierarchy (Sector/Group/Industry/Sub-Industry) from Wikipedia into ref tables."

    def add_arguments(self, parser):
        parser.add_argument("--edition", default="GICS 2024", help="Edition name (e.g., 'GICS 2024').")
        parser.add_argument("--effective-date", default="2024-01-01", help="Edition effective date YYYY-MM-DD.")
        parser.add_argument("--created-by", type=int, default=101, help="Created_by user id.")
        parser.add_argument("--keep-existing-names", action="store_true",
                            help="If set, will NOT overwrite existing names/links; only inserts missing codes.")

    @transaction.atomic
    def handle(self, *args, **opts):
        edition_name: str = opts["edition"]
        eff_dt = date.fromisoformat(opts["effective_date"])
        created_by: int = opts["created_by"]
        keep_existing: bool = bool(opts["keep_existing_names"])

        # 1) Ensure edition exists & set as current (one-current policy)
        GicsEdition.objects.filter(is_current=True).update(is_current=False)

        edition, _ = GicsEdition.objects.update_or_create(
            name=edition_name,
            defaults={"effective_date": eff_dt, "is_current": True, "created_by": created_by},
        )
        self.stdout.write(self.style.SUCCESS(f"Using edition: {edition.name} (id={edition.id})"))

        # 2) Fetch Wikipedia with headers
        resp = requests.get(
            WIKI_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X) PortX/1.0",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30,
        )
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # 3) Locate classification table robustly
        table = find_gics_table(soup)
        if not table:
            raise RuntimeError(
                "Could not locate the GICS classification table on Wikipedia (page structure changed)."
            )

        # 4) Parse table into leaf rows (sub-industry rows), carrying current context
        current = {
            "sector_code": None,
            "sector_name": None,
            "group_code": None,
            "group_name": None,
            "industry_code": None,
            "industry_name": None,
        }
        leaf_rows: list[dict] = []

        for tr in table.find_all("tr"):
            cells = [clean_cell(td.get_text(" ", strip=True)) for td in tr.find_all(["th", "td"])]
            if not cells:
                continue

            # Skip header row(s)
            if any(norm(c) == "sector" for c in cells[:2]):
                continue

            # Remove empty placeholders
            cells = [c for c in cells if c and c != "—"]

            i = 0
            while i < len(cells):
                val = cells[i]
                nxt = cells[i + 1] if i + 1 < len(cells) else ""

                # A) Code in one cell, Name in next
                if RE_CODE_ONLY.match(val) and nxt and not RE_CODE_ONLY.match(nxt):
                    code = val
                    name = nxt
                    if len(code) == 2:
                        current["sector_code"], current["sector_name"] = code, name
                    elif len(code) == 4:
                        current["group_code"], current["group_name"] = code, name
                    elif len(code) == 6:
                        current["industry_code"], current["industry_name"] = code, name
                    elif len(code) == 8:
                        leaf_rows.append(
                            {
                                **current,
                                "subindustry_code": code,
                                "subindustry_name": name,
                            }
                        )
                    i += 2
                    continue

                # B) "1010 Energy" in one cell
                m = RE_CODE_AND_NAME.match(val)
                if m:
                    code = m.group(1)
                    name = m.group(2).strip()
                    if len(code) == 2:
                        current["sector_code"], current["sector_name"] = code, name
                    elif len(code) == 4:
                        current["group_code"], current["group_name"] = code, name
                    elif len(code) == 6:
                        current["industry_code"], current["industry_name"] = code, name
                    elif len(code) == 8:
                        leaf_rows.append(
                            {
                                **current,
                                "subindustry_code": code,
                                "subindustry_name": name,
                            }
                        )

                i += 1

        if not leaf_rows:
            raise RuntimeError("Parsed 0 sub-industry rows. Wikipedia table format likely changed.")

        # 5) Upsert hierarchy from leaf_rows
        sector_cache: dict[str, GicsSector] = {}
        group_cache: dict[str, GicsIndustryGroup] = {}
        industry_cache: dict[str, GicsIndustry] = {}

        def upsert_or_keep(model_cls, lookup_kwargs, defaults):
            """
            If keep_existing_names is enabled, only create missing entries.
            Otherwise, update existing with defaults.
            """
            if keep_existing:
                obj = model_cls.objects.filter(**lookup_kwargs).first()
                if obj:
                    return obj, False
                obj = model_cls.objects.create(**lookup_kwargs, **defaults)
                return obj, True
            else:
                obj, created = model_cls.objects.update_or_create(**lookup_kwargs, defaults=defaults)
                return obj, created

        # Sectors
        sec_created = sec_updated = 0
        for r in leaf_rows:
            sc, sn = r.get("sector_code"), r.get("sector_name")
            if not sc or not sn:
                continue
            if sc in sector_cache:
                continue

            obj, created = upsert_or_keep(
                GicsSector,
                {"edition": edition, "code": sc},
                {"name": sn, "created_by": created_by},
            )
            sector_cache[sc] = obj
            sec_created += 1 if created else 0
            sec_updated += 0 if created else 1

        # Industry Groups
        grp_created = grp_updated = 0
        for r in leaf_rows:
            gc, gn, sc = r.get("group_code"), r.get("group_name"), r.get("sector_code")
            if not gc or not gn or not sc:
                continue
            if gc in group_cache:
                continue

            sec = sector_cache.get(sc)
            if not sec:
                continue

            obj, created = upsert_or_keep(
                GicsIndustryGroup,
                {"edition": edition, "code": gc},
                {"name": gn, "sector": sec, "created_by": created_by},
            )
            group_cache[gc] = obj
            grp_created += 1 if created else 0
            grp_updated += 0 if created else 1

        # Industries
        ind_created = ind_updated = 0
        for r in leaf_rows:
            ic, inn, gc = r.get("industry_code"), r.get("industry_name"), r.get("group_code")
            if not ic or not inn or not gc:
                continue
            if ic in industry_cache:
                continue

            grp = group_cache.get(gc)
            if not grp:
                continue

            obj, created = upsert_or_keep(
                GicsIndustry,
                {"edition": edition, "code": ic},
                {"name": inn, "group": grp, "created_by": created_by},
            )
            industry_cache[ic] = obj
            ind_created += 1 if created else 0
            ind_updated += 0 if created else 1

        # Sub-industries
        sub_created = sub_updated = 0
        for r in leaf_rows:
            sic, sin, ic = r.get("subindustry_code"), r.get("subindustry_name"), r.get("industry_code")
            if not sic or not sin or not ic:
                continue
            ind = industry_cache.get(ic)
            if not ind:
                continue

            obj, created = upsert_or_keep(
                GicsSubIndustry,
                {"edition": edition, "code": sic},
                {"name": sin, "industry": ind, "created_by": created_by},
            )
            sub_created += 1 if created else 0
            sub_updated += 0 if created else 1

        self.stdout.write(self.style.SUCCESS(
            f"Loaded GICS from Wikipedia into edition '{edition.name}'. "
            f"Sectors={len(sector_cache)} (created={sec_created}) "
            f"Groups={len(group_cache)} (created={grp_created}) "
            f"Industries={len(industry_cache)} (created={ind_created}) "
            f"SubIndustries={sub_created + sub_updated} (created={sub_created}) "
            f"{'[keep-existing-names enabled]' if keep_existing else ''}"
        ))
