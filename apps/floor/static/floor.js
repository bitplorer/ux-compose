// Progressive enhancer: kit bind() → POST /act/{name}.
// Isolation: no ux_channel import.
//
// Fields (input/textarea/select) must stay focusable. A click on a bound
// field must not preventDefault or remorph the card — that ate Typeahead
// and OTP. Live filter morphs only data-channel-target (the hits slot).
// set_field on a keystroke is silent (Host remembers; the DOM keeps typing).
(function () {
  function isField(el) {
    var n = (el.tagName || "").toUpperCase();
    return n === "INPUT" || n === "TEXTAREA" || n === "SELECT";
  }

  function delayOf(el) {
    var on = el.getAttribute("data-channel-on") || "";
    var m = /delay:(\d+)/.exec(on);
    return m ? parseInt(m[1], 10) : 0;
  }

  function argsOf(el) {
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

  function swap(id, html) {
    if (!id || !html) return;
    var el = document.getElementById(id);
    if (el) el.outerHTML = html;
  }

  function post(action, args, mode) {
    if (mode === "slot") args._target = args._target || "";
    if (mode === "none") args._swap = "none";
    fetch("/act/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(args),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (!data) return;
        if (data.swap === "none") {
          if (data.ledger) swap("floor-ledger", data.ledger);
          return;
        }
        if (data.html && data.id) swap(data.id, data.html);
        if (data.ledger) swap("floor-ledger", data.ledger);
      });
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-ux-action]");
    if (!t || t.tagName === "A" || isField(t)) return;
    var action = t.getAttribute("data-ux-action");
    if (!action) return;
    ev.preventDefault();
    post(action, argsOf(t), "card");
  });

  document.addEventListener("submit", function (ev) {
    var t = ev.target.querySelector("[data-ux-action]");
    if (!t) return;
    var action = t.getAttribute("data-ux-action");
    if (!action) return;
    ev.preventDefault();
    post(action, argsOf(t), "card");
  });

  var timers = {};
  document.addEventListener("input", function (ev) {
    var t = ev.target;
    if (!isField(t)) return;
    var action = t.getAttribute("data-ux-action");
    if (!action) return;
    var target = t.getAttribute("data-channel-target") || "";
    var args = argsOf(t);
    var mode = target ? "slot" : "none";
    if (target) args._target = target.replace(/^#/, "");
    var wait = delayOf(t);
    var key = action + ":" + (t.id || t.name || "");
    clearTimeout(timers[key]);
    timers[key] = setTimeout(function () {
      post(action, args, mode);
    }, wait);
  });
})();
