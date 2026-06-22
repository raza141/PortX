/*
 * governance/kyc/static/kyc/js/kyc.js
 *
 * Progressive enhancement for the KYC wizard and review queue. Mirrors the
 * existing IBOR formset add/remove UX. No framework; vanilla DOM + fetch.
 */
(function () {
  "use strict";

  function getCookie(name) {
    const match = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return match ? match.pop() : "";
  }

  const CSRF = getCookie("csrftoken");

  function postForm(url, formData) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "X-CSRFToken": CSRF,
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    })
      .then(async (r) => {
        let data = {};
        try {
          data = await r.json();
        } catch (_) {
          data = { ok: false, error: "Invalid server response." };
        }
        return { ok: r.ok, status: r.status, data };
      })
      .catch(() => ({
        ok: false,
        status: 0,
        data: { ok: false, error: "Network error." },
      }));
  }

  function getJSON(url) {
    return fetch(url, {
      method: "GET",
      credentials: "same-origin",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
      },
    })
      .then(async (r) => {
        let data = {};
        try {
          data = await r.json();
        } catch (_) {
          data = { ok: false, error: "Invalid server response." };
        }
        return { ok: r.ok, status: r.status, data };
      })
      .catch(() => ({
        ok: false,
        status: 0,
        data: { ok: false, error: "Network error." },
      }));
  }

  function clearFormErrors(form) {
    form.querySelectorAll(".kyc-error").forEach((el) => el.remove());
    form.querySelectorAll(".is-invalid").forEach((el) => el.classList.remove("is-invalid"));
  }

  function renderFormErrors(form, errors) {
    if (!errors) return;

    Object.keys(errors).forEach((fieldName) => {
      const fieldErrors = errors[fieldName] || [];
      const input =
        form.querySelector(`[name="${fieldName}"]`) ||
        form.querySelector(`[name$="-${fieldName}"]`);

      if (input) {
        input.classList.add("is-invalid");

        const holder = document.createElement("div");
        holder.className = "kyc-error";

        fieldErrors.forEach((err) => {
          const p = document.createElement("p");
          p.className = "kyc-error";
          p.textContent = err.message || "Invalid value.";
          holder.appendChild(p);
        });

        input.insertAdjacentElement("afterend", holder);
      }
    });

    if (errors.__all__) {
      const box = document.createElement("div");
      box.className = "kyc-error";
      errors.__all__.forEach((err) => {
        const p = document.createElement("p");
        p.className = "kyc-error";
        p.textContent = err.message || "Validation error.";
        box.appendChild(p);
      });
      form.prepend(box);
    }
  }

  // --- Section save ------------------------------------------------------- //
  function bindSectionForms(root) {
    root.querySelectorAll("form.kyc-section-form").forEach((form) => {
      if (form.dataset.bound === "1") return;
      form.dataset.bound = "1";

      form.addEventListener("submit", (event) => {
        event.preventDefault();
        clearFormErrors(form);

        const url = form.dataset.saveUrl;
        if (!url) return;

        postForm(url, new FormData(form)).then(({ ok, data }) => {
          if (ok && data.ok) {
            refreshProgress(data.section_status);
            flash(form, "Saved", "ok");
            const wizard = document.querySelector(".kyc-wizard");
            if (wizard) revalidate(wizard);
          } else {
            renderFormErrors(form, data.errors);
            flash(form, data.error || "Check the highlighted fields", "bad");
          }
        });
      });
    });
  }

  // --- Repeating rows: add ------------------------------------------------ //
  function bindAddRow(root) {
    root.querySelectorAll("[data-add-row]").forEach((btn) => {
      if (btn.dataset.bound === "1") return;
      btn.dataset.bound = "1";

      btn.addEventListener("click", () => {
        const group = btn.dataset.addRow;
        const url = btn.dataset.addUrl;
        const container = root.querySelector(`.kyc-rows[data-group="${group}"]`);
        if (!url || !container) return;

        const total = document.querySelector(`input[name="${group}-TOTAL_FORMS"]`);
        const index = total
          ? parseInt(total.value, 10)
          : container.querySelectorAll(".kyc-row").length;

        getJSON(url + "?index=" + index).then(({ ok, data }) => {
          if (ok && data.ok) {
            const tmp = document.createElement("div");
            tmp.innerHTML = data.html.trim();
            if (tmp.firstElementChild) {
              container.appendChild(tmp.firstElementChild);
              bumpTotalForms(group);
              bindSectionForms(container);
            }
          } else {
            window.alert(data.error || "Could not add row.");
          }
        });
      });
    });
  }

  // --- Repeating rows: remove (event delegation) -------------------------- //
  function bindRemoveRow(root) {
    root.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-remove-row]");
      if (!btn) return;
      const row = btn.closest(".kyc-row");
      if (!row) return;

      const del = row.querySelector('input[type="checkbox"][name$="-DELETE"]');
      if (del) {
        del.checked = true;        // saved row -> mark for deletion, keep in DOM
        row.style.display = "none";
      } else {
        row.remove();              // unsaved row -> just drop it
      }
      // TOTAL_FORMS is intentionally NOT changed on remove.
    });
  }

  // Increment TOTAL_FORMS by exactly 1 when adding. Never recompute from DOM.
  function bumpTotalForms(group) {
    const total = document.querySelector(`input[name="${group}-TOTAL_FORMS"]`);
    if (total) total.value = String(parseInt(total.value, 10) + 1);
  }

  // --- Progress indicator ------------------------------------------------- //
  function refreshProgress(sectionStatus) {
    if (!sectionStatus) return;

    Object.keys(sectionStatus).forEach((key) => {
      const step = document.querySelector(`.kyc-step[data-section="${key}"]`);
      if (step) {
        step.classList.toggle("is-complete", !!sectionStatus[key]);
      }
    });
  }

  function revalidate(wizard) {
    const url = wizard.dataset.validateUrl;
    if (!url) return;

    getJSON(url).then(({ ok, data }) => {
      if (!ok || !data) return;

      refreshProgress(data.section_status);

      const submit = document.querySelector('.kyc-wizard__footer button[type="submit"]');
      if (submit) {
        submit.disabled = !data.submittable;
      }

      const box = document.getElementById("kyc-submit-errors");
      if (box) {
        box.innerHTML = "";
        (data.errors || []).forEach((e) => {
          const p = document.createElement("p");
          p.className = "kyc-error";
          p.textContent = e;
          box.appendChild(p);
        });
      }
    });
  }

  // --- Review-queue decisions -------------------------------------------- //
  function bindReviewDecisions(root) {
    const table = root.querySelector("#kyc-review-table");
    if (!table) return;

    table.addEventListener("click", (event) => {
      const btn = event.target.closest("[data-action]");
      if (!btn) return;

      const row = btn.closest("[data-decide-url]");
      if (!row) return;

      let reason = "";
      if (btn.dataset.action === "REJECT" || btn.dataset.action === "REQUEST_INFO") {
        reason = window.prompt("Reason:") || "";
      }

      const fd = new FormData();
      fd.append("action", btn.dataset.action);
      fd.append("reason", reason);

      postForm(row.dataset.decideUrl, fd).then(({ ok, data }) => {
        if (ok && data.ok) {
          window.location.reload();
        } else {
          window.alert(data.error || "Action failed.");
        }
      });
    });
  }

  // --- Misc --------------------------------------------------------------- //
  function flash(el, message, kind) {
    const note = document.createElement("span");
    note.className = "kyc-help kyc-" + (kind === "bad" ? "error" : "muted");
    note.textContent = message;
    el.appendChild(note);
    setTimeout(() => note.remove(), 2500);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const root = document.querySelector(".kyc-shell") || document;
    bindSectionForms(root);
    bindAddRow(root);
    bindRemoveRow(root);
    bindReviewDecisions(root);

    const wizard = root.querySelector(".kyc-wizard");
    if (wizard) {
      revalidate(wizard);
    }
  });
})();