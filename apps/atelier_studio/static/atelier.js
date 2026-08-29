// Progressive enhancer: kit bind() data-ux-action → POST /act/{name}.
// Isolation: no ux_channel import. Channel may also attach when the
// Document shell is used; this file is for the handmade Atelier pages.
function _uxField(el) {
  var n = (el.tagName || "").toUpperCase();
  return n === "INPUT" || n === "TEXTAREA" || n === "SELECT";
}

function _uxArgs(el) {
  var args = {};
  Array.prototype.forEach.call(el.attributes, function (attr) {
    if (attr.name.indexOf("data-ux-arg-") === 0) {
      args[attr.name.slice(12)] = attr.value;
    }
  });
  if (el.name) args[el.name] = el.value;
  var form = el.form || el.closest("form");
  if (form) {
    var fd = new FormData(form);
    fd.forEach(function (v, k) {
      args[k] = v;
    });
  }
  return args;
}

function _uxPost(action, args, onHtml) {
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
    .then(onHtml);
}

document.addEventListener("click", function (ev) {
  var t = ev.target.closest("[data-ux-action]");
  if (!t || t.tagName === "A" || _uxField(t)) return;
  var action = t.getAttribute("data-ux-action");
  if (!action) return;
  ev.preventDefault();
  var stage = document.getElementById("stage");
  _uxPost(action, _uxArgs(t), function (html) {
    if (stage && html) stage.outerHTML = html;
  });
});

var _uxTimers = {};
document.addEventListener("input", function (ev) {
  var t = ev.target;
  if (!_uxField(t)) return;
  var action = t.getAttribute("data-ux-action");
  if (!action) return;
  var on = t.getAttribute("data-channel-on") || "";
  var delay = 0;
  var m = /delay:(\d+)/.exec(on);
  if (m) delay = parseInt(m[1], 10);
  var target = (t.getAttribute("data-channel-target") || "").replace(/^#/, "");
  var args = _uxArgs(t);
  var key = action + ":" + (t.id || t.name || "");
  clearTimeout(_uxTimers[key]);
  _uxTimers[key] = setTimeout(function () {
    if (!target) return;
    _uxPost(action, args, function (html) {
      var slot = document.getElementById(target);
      if (!slot || !html) return;
      var wrap = document.createElement("div");
      wrap.innerHTML = html.trim();
      var next = wrap.querySelector("#" + target) || wrap.firstElementChild;
      if (next) slot.replaceWith(next);
    });
  }, delay);
});
