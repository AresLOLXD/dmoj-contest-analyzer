// Two-step upload: PUT the raw .zip with a progress bar. External file to
// satisfy CSP `script-src 'self'` (no inline scripts).
(function () {
  "use strict";
  var box = document.getElementById("upload");
  if (!box) return;
  var jobId = box.dataset.jobId;
  var csrf = box.dataset.csrf;
  var input = document.getElementById("zipfile");
  var btn = document.getElementById("uploadbtn");
  var bar = document.getElementById("uploadprogress");
  var msg = document.getElementById("uploadmsg");

  function fail(text) {
    msg.textContent = text;
    msg.hidden = false;
    btn.disabled = false;
    input.disabled = false;
  }

  btn.addEventListener("click", function () {
    var file = input.files && input.files[0];
    if (!file) { fail("Elige un archivo .zip primero."); return; }
    msg.hidden = true;
    btn.disabled = true;
    input.disabled = true;
    bar.hidden = false;

    var xhr = new XMLHttpRequest();
    xhr.open("PUT", "/jobs/" + jobId + "/upload");
    xhr.setRequestHeader("X-CSRF-Token", csrf);
    xhr.upload.addEventListener("progress", function (e) {
      if (e.lengthComputable) bar.value = Math.round((e.loaded / e.total) * 100);
    });
    xhr.addEventListener("load", function () {
      if (xhr.status === 204) {
        window.location.reload();
      } else if (xhr.status === 413) {
        fail("El archivo es demasiado grande.");
      } else if (xhr.status === 409) {
        fail("Este trabajo ya no acepta una subida. Recarga la página.");
      } else {
        fail("La subida falló (código " + xhr.status + "). Intenta de nuevo.");
      }
    });
    xhr.addEventListener("error", function () {
      fail("Error de red durante la subida. Intenta de nuevo.");
    });
    xhr.send(file);
  });
})();
