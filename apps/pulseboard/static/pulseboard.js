/* Progressive enhancer: data-ux-action → POST /action/{name} + theme sync. */
(function () {
  function syncTheme(root) {
    var scope = root || document;
    var el = scope.querySelector ? scope.querySelector("[data-theme]") : null;
    if (!el && scope.getAttribute) el = scope;
    var theme = el && el.getAttribute && el.getAttribute("data-theme");
    if (!theme) {
      var board = document.getElementById("pulseboard");
      theme = board && board.getAttribute("data-theme");
    }
    if (!theme) return;
    var night = theme === "dark" || theme === "ink";
    document.documentElement.classList.toggle("dark", night);
    if (document.body) document.body.classList.toggle("dark", night);
  }

  function postAction(action, args, target) {
    var body = new URLSearchParams(args || {});
    return fetch("/action/" + action, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "HX-Request": "true",
      },
      body: body,
    }).then(function (r) {
      return r.text();
    }).then(function (html) {
      if (!target) return;
      var wrap = document.createElement("div");
      wrap.innerHTML = html.trim();
      var next = wrap.firstElementChild;
      if (next) {
        target.replaceWith(next);
        syncTheme(next);
      }
    });
  }

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
    var target =
      document.getElementById(surface) ||
      document.getElementById("pulseboard") ||
      document.getElementById("board");
    if (window.htmx) {
      window.htmx.ajax("POST", "/action/" + action, {
        target: target,
        swap: "outerHTML",
        values: args,
        headers: { "HX-Request": "true" },
      });
      return;
    }
    postAction(action, args, target);
  });

  document.addEventListener("change", function (ev) {
    var t = ev.target.closest("[data-ux-action]");
    if (!t || t.type !== "range") return;
    var action = t.getAttribute("data-ux-action");
    if (!action) return;
    var args = { value: t.value };
    Array.prototype.forEach.call(t.attributes, function (attr) {
      if (attr.name.indexOf("data-ux-arg-") === 0) {
        args[attr.name.slice(12)] = attr.value;
      }
    });
    var surface = action.split(".")[0];
    var target = document.getElementById(surface);
    postAction(action, args, target);
  });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { syncTheme(); });
  } else {
    syncTheme();
  }
})();
