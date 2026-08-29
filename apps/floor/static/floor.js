// Progressive enhancer: kit bind() → POST /act/{name} → swap the card + ledger.
// Isolation: no ux_channel import. Clock B is app.dispatch on the process.
(function () {
  function argsOf(el) {
    var args = {};
    Array.prototype.forEach.call(el.attributes, function (attr) {
      if (attr.name.indexOf("data-ux-arg-") === 0) {
        args[attr.name.slice(12)] = attr.value;
      }
    });
    var form = el.form || el.closest("form");
    if (form) {
      var fd = new FormData(form);
      fd.forEach(function (v, k) {
        args[k] = v;
      });
    }
    return args;
  }

  function post(action, args) {
    fetch("/act/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams(args),
    })
      .then(function (r) {
        return r.json();
      })
      .then(function (data) {
        if (data && data.html && data.id) {
          var el = document.getElementById(data.id);
          if (el) el.outerHTML = data.html;
        }
        if (data && data.ledger) {
          var led = document.getElementById("floor-ledger");
          if (led) led.outerHTML = data.ledger;
        }
      });
  }

  document.addEventListener("click", function (ev) {
    var t = ev.target.closest("[data-ux-action]");
    if (!t || t.tagName === "A") return;
    var action = t.getAttribute("data-ux-action");
    if (!action) return;
    ev.preventDefault();
    post(action, argsOf(t));
  });

  document.addEventListener("submit", function (ev) {
    var t = ev.target.querySelector("[data-ux-action]");
    if (!t) return;
    var action = t.getAttribute("data-ux-action");
    if (!action) return;
    ev.preventDefault();
    post(action, argsOf(t));
  });
})();
