// Progressive enhancer: kit bind() data-ux-action → POST /act/{name}.
// Isolation: no ux_channel import. Channel may also attach when the
// Document shell is used; this file is for the handmade Atelier pages.
document.addEventListener("click", function (ev) {
  var t = ev.target.closest("[data-ux-action]");
  if (!t || t.tagName === "A") return;
  var action = t.getAttribute("data-ux-action");
  if (!action) return;
  ev.preventDefault();
  var args = {};
  Array.prototype.forEach.call(t.attributes, function (attr) {
    if (attr.name.indexOf("data-ux-arg-") === 0) {
      args[attr.name.slice(12)] = attr.value;
    }
  });
  var stage = document.getElementById("stage");
  fetch("/act/" + action, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "HX-Request": "true",
    },
    body: new URLSearchParams(args),
  })
    .then(function (r) {
      return r.text();
    })
    .then(function (html) {
      if (stage && html) stage.outerHTML = html;
    });
});
