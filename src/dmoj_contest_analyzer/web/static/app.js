// Populate the model dropdown from /api/models. External file to satisfy the
// CSP `script-src 'self'` (no inline scripts allowed).
(function () {
  "use strict";
  const select = document.getElementById("model_ref");
  if (!select) return;
  const url = select.dataset.modelsUrl || "/api/models";
  fetch(url, { credentials: "same-origin" })
    .then((r) => (r.ok ? r.json() : { backends: [] }))
    .then((data) => {
      (data.backends || []).forEach((backend) => {
        const group = document.createElement("optgroup");
        group.label = backend.label;
        (backend.models || []).forEach((model) => {
          const option = document.createElement("option");
          option.value = backend.id + "|" + model;
          option.textContent = model;
          group.appendChild(option);
        });
        select.appendChild(group);
      });
    })
    .catch(() => {});
})();
