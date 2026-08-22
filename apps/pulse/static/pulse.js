// Progressive enhancer: data-ux-action → htmx POST /action/{name}
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
  var surface = action.split(".")[0];
  var target = document.getElementById(surface) || document.getElementById("main");
  if (window.htmx) {
    htmx.ajax("POST", "/action/" + action, {
      target: target,
      swap: "outerHTML",
      values: args,
      headers: { "HX-Request": "true" }
    });
  } else {
    fetch("/action/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", "HX-Request": "true" },
      body: new URLSearchParams(args)
    }).then(function (r) { return r.text(); }).then(function (html) {
      if (target) target.outerHTML = html;
    });
  }
});
