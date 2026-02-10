#!/usr/bin/env python3
"""
PSX Issuer Scraper -> Excel
==========================

Reads a list of PSX tickers, fetches https://dps.psx.com.pk/company/<TICKER>,
extracts:
- issuer_name
- local sector (text) + local_sector_id (via lookup CSV you exported from your DB)
- fiscal year end month
- headquarters_city (best-effort from address)
- website
- issuer_type (COMPANY/BANK/FUND/...) (heuristic)

Outputs an Excel file that matches your Issuer admin fields so you can review
before inserting into DB.

Usage:
  pip install requests beautifulsoup4 pandas openpyxl

  python psx_scrape_issuers.py \
      --tickers KSENAME.csv \
      --sector-map PSX_Sector_data.csv \
      --country-id 1 \
      --out psx_issuers.xlsx

Notes:
- Respect PSX licensing/terms before using this in production/commercial settings.
- Adds throttling + retries to be polite.
"""

import argparse
import hashlib
import re
import time
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

MONTH_MAP = {
    "JAN": 1, "JANUARY": 1,
    "FEB": 2, "FEBRUARY": 2,
    "MAR": 3, "MARCH": 3,
    "APR": 4, "APRIL": 4,
    "MAY": 5,
    "JUN": 6, "JUNE": 6,
    "JUL": 7, "JULY": 7,
    "AUG": 8, "AUGUST": 8,
    "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
    "OCT": 10, "OCTOBER": 10,
    "NOV": 11, "NOVEMBER": 11,
    "DEC": 12, "DECEMBER": 12,
}

ISSUER_TYPE_HINTS = [
    (re.compile(r"\bBANK\b", re.I), "BANK"),
    (re.compile(r"\bCOMMERCIAL\s+BANK", re.I), "BANK"),
    (re.compile(r"\bISLAMIC\s+BANK", re.I), "BANK"),
    (re.compile(r"\bINSURANCE\b", re.I), "COMPANY"),  # you may later add INSURANCE as a type
    (re.compile(r"\bMODARABA\b", re.I), "COMPANY"),
    (re.compile(r"\bFUND\b|\bMUTUAL\b", re.I), "FUND"),
]

def slug_code(name: str, country_prefix: str = "ISS_PK_", max_len: int = 64) -> str:
    base = re.sub(r"[^A-Za-z0-9]+", "_", name.upper()).strip("_")
    code = f"{country_prefix}{base}"
    if len(code) <= max_len:
        return code
    # Truncate + hash suffix for uniqueness
    h = hashlib.sha1(code.encode("utf-8")).hexdigest()[:6].upper()
    keep = max_len - len(country_prefix) - 7  # '_' + 6 hash
    base_trunc = base[:max(10, keep)]
    return f"{country_prefix}{base_trunc}_{h}"

def best_effort_city(address: str) -> str:
    if not address:
        return ""
    # Try "... Karachi, Pakistan." -> Karachi
    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) >= 2 and parts[-1].lower().startswith("pakistan"):
        return parts[-2].replace(".", "")
    # fallback: last non-empty token
    return parts[-1].replace(".", "") if parts else ""

def load_sector_map(sector_csv: str) -> Tuple[Dict[str, int], Dict[int, str]]:
    df = pd.read_csv(sector_csv)
    name_to_id = {}
    id_to_name = {}
    for _, r in df.iterrows():
        sid = int(r["id"])
        nm = str(r["name"]).strip().upper()
        name_to_id[nm] = sid
        id_to_name[sid] = nm
    return name_to_id, id_to_name

def fetch_company_page(session: requests.Session, ticker: str, timeout: int = 20) -> str:
    url = f"https://dps.psx.com.pk/company/{ticker}"
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_from_text(ticker: str, text_lines: list, sector_name_set: set) -> Dict[str, str]:
    # issuer_name: find first plausible company name after first ticker occurrence
    issuer_name = ""
    try:
        idx = text_lines.index(ticker)
    except ValueError:
        idx = 0

    for j in range(idx, min(idx + 40, len(text_lines))):
        s = text_lines[j]
        if any(x in s.upper() for x in ["QUOTE", "PROFILE", "EQUITY", "ANNOUNCEMENTS", "FINANCIALS", "RATIOS", "PAYOUTS", "REPORTS"]):
            continue
        if len(s) < 4:
            continue
        if s.upper() == s and s in sector_name_set:
            continue
        # Most PSX issuer names contain these patterns
        if re.search(r"\b(LIMITED|LTD|BANK|HOLDINGS|CORP|COMPANY)\b", s, re.I):
            issuer_name = s.strip()
            break

    # sector: pick first line that matches a known local sector name
    sector = ""
    for s in text_lines:
        up = s.strip().upper()
        if up in sector_name_set:
            sector = up
            break

    # fiscal year end: look for "Fiscal Year End" then next non-empty line
    fye = ""
    for i, s in enumerate(text_lines):
        if s.strip().lower() == "fiscal year end":
            if i + 1 < len(text_lines):
                fye = text_lines[i + 1].strip()
            break

    # address: find "ADDRESS" label then next line
    address = ""
    for i, s in enumerate(text_lines):
        if s.strip().upper() == "ADDRESS":
            if i + 1 < len(text_lines):
                address = text_lines[i + 1].strip()
            break

    # website: find "WEBSITE" then next line that looks like a domain/url
    website = ""
    for i, s in enumerate(text_lines):
        if s.strip().upper() == "WEBSITE":
            for j in range(i + 1, min(i + 6, len(text_lines))):
                cand = text_lines[j].strip()
                if re.match(r"^(https?://)?[A-Za-z0-9\.-]+\.[A-Za-z]{2,}(/.*)?$", cand):
                    website = cand if cand.startswith("http") else f"https://{cand}"
                    break
            break

    return {
        "issuer_name": issuer_name,
        "local_sector_name": sector,
        "fiscal_year_end": fye,
        "address": address,
        "website": website,
    }

def issuer_type_from_sector(sector_name: str) -> str:
    if not sector_name:
        return "COMPANY"
    for rx, it in ISSUER_TYPE_HINTS:
        if rx.search(sector_name):
            return it
    return "COMPANY"

def month_to_int(month_text: str) -> Optional[int]:
    if not month_text:
        return None
    key = re.sub(r"[^A-Za-z]", "", month_text).upper()
    return MONTH_MAP.get(key)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickers", required=True, help="CSV file with 1 column of tickers (no header preferred).")
    ap.add_argument("--sector-map", required=True, help="CSV export of taxonomy.LocalSector (id,name,...)")
    ap.add_argument("--country-id", type=int, default=1)
    ap.add_argument("--out", default="psx_issuers.xlsx")
    ap.add_argument("--created-by", type=int, default=101)
    ap.add_argument("--sleep", type=float, default=0.8, help="Throttle between requests (seconds).")
    ap.add_argument("--timeout", type=int, default=20)
    args = ap.parse_args()

    tickers = pd.read_csv(args.tickers, header=None)[0].astype(str).str.strip().tolist()
    tickers = [t for t in tickers if t]
    # de-dup
    seen=set()
    tickers_u=[]
    for t in tickers:
        if t not in seen:
            tickers_u.append(t)
            seen.add(t)

    sector_name_to_id, _ = load_sector_map(args.sector_map)
    sector_name_set = set(sector_name_to_id.keys())

    session = requests.Session()
    session.headers.update({
        "User-Agent": "PortX-RefdataBot/0.1 (contact: you@example.com)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })

    rows = []
    for t in tickers_u:
        url = f"https://dps.psx.com.pk/company/{t}"
        row = {
            "ticker": t,
            "psx_company_url": url,
            "issuer_name": "",
            "issuer_code": "",
            "issuer_type": "COMPANY",
            "country_id": args.country_id,
            "local_sector_name": "",
            "local_sector_id": None,
            "fiscal_year_end_month": None,
            "headquarters_city": "",
            "website": "",
            "issuer_lei": "",
            "issuer_status": "ACTIVE",
            "created_by": args.created_by,
            "scrape_status": "PENDING",
            "scrape_error": "",
            "scraped_at": "",
        }
        try:
            html = fetch_company_page(session, t, timeout=args.timeout)
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text("\n")
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

            extracted = extract_from_text(t, lines, sector_name_set)

            row["issuer_name"] = extracted["issuer_name"] or t  # fallback
            row["local_sector_name"] = extracted["local_sector_name"] or ""
            if row["local_sector_name"]:
                row["local_sector_id"] = sector_name_to_id.get(row["local_sector_name"].upper())
            row["issuer_type"] = issuer_type_from_sector(row["local_sector_name"])
            row["website"] = extracted["website"] or ""
            row["headquarters_city"] = best_effort_city(extracted["address"] or "")
            row["fiscal_year_end_month"] = month_to_int(extracted["fiscal_year_end"] or "")

            # internal issuer_code from issuer_name (slug + hash if needed)
            row["issuer_code"] = slug_code(row["issuer_name"], country_prefix="ISS_PK_", max_len=64)

            row["scrape_status"] = "OK"
            row["scraped_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        except Exception as e:
            row["scrape_status"] = "ERROR"
            row["scrape_error"] = f"{type(e).__name__}: {e}"
            row["scraped_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

        rows.append(row)
        time.sleep(args.sleep)

    df = pd.DataFrame(rows)
    # Write excel
    with pd.ExcelWriter(args.out, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="psx_issuer_seed", index=False)

        # include lookup sheet for convenience
        sector_df = pd.read_csv(args.sector_map)
        sector_df.to_excel(writer, sheet_name="local_sector_lookup", index=False)

    print(f"Wrote: {args.out} (rows={len(df)})")

if __name__ == "__main__":
    main()
