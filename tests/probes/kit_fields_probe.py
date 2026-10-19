"""Kit **kwargs field-loss probe (#114 r3). Run from a compose tree with its own src first.
Simulates ux-channel.js fireControl: POST /ux-channel/action with
{action, args=data-channel-args (sealed), cap=data-channel-cap, form=FormData of the closest <form>
 (+ the control's own name/value)}. Records what each action frame actually received (sys.setprofile)."""
import threading, sys, os, json, importlib, inspect, logging, warnings, subprocess
sys.path[:0] = ["src", "."]
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
from html.parser import HTMLParser
from fastapi import FastAPI
from starlette.testclient import TestClient
import ux_behavior
from ux_compose import App, Component

KITS = ["formlayout", "login", "newsletter", "otp", "combobox", "command", "chat",
        "tagsinput", "searchbar", "filterbar", "spinbutton", "colorpicker"]

class Node:
    def __init__(s, tag, attrs, parent): s.tag, s.attrs, s.parent, s.kids = tag, dict(attrs), parent, []
VOID = {"input", "br", "img", "meta", "link", "hr", "area", "base", "col", "embed", "source", "track", "wbr"}
class P(HTMLParser):
    def __init__(s): super().__init__(); s.root = Node("#root", {}, None); s.cur = s.root; s.all = []
    def handle_starttag(s, t, a):
        n = Node(t, a, s.cur); s.cur.kids.append(n); s.all.append(n)
        if t not in VOID: s.cur = n
    def handle_startendtag(s, t, a):
        n = Node(t, a, s.cur); s.cur.kids.append(n); s.all.append(n)
    def handle_endtag(s, t):
        c = s.cur
        while c is not s.root and c.tag != t: c = c.parent
        if c is not s.root: s.cur = c.parent
def walk(n):
    for k in n.kids:
        yield k; yield from walk(k)
def closest_form(n):
    while n is not None and n.tag != "form": n = n.parent
    return n

def find_cls(key):
    mod = importlib.import_module(f"ux_compose.components.{key}")
    for v in vars(mod).values():
        if inspect.isclass(v) and issubclass(v, Component) and v is not Component and v.__module__ == mod.__name__ \
           and (getattr(v, "id", None) == key):
            return v
    for v in vars(mod).values():
        if inspect.isclass(v) and issubclass(v, Component) and v.__module__ == mod.__name__:
            return v

seen = []
def prof(frame, event, arg):
    if event == "call" and frame.f_code in CODES:
        loc = dict(frame.f_locals); loc.pop("self", None)
        seen.append((CODES[frame.f_code], {k: (dict(v) if isinstance(v, dict) else v) for k, v in loc.items()}))

def unwrap(fn):
    for a in ("__wrapped__", "fn", "_fn", "func", "__func__"):
        g = getattr(fn, a, None)
        if g is not None and g is not fn and callable(g): return unwrap(g)
    return fn

out = {"behavior": subprocess.run(["git", "-C", str(os.path.dirname(ux_behavior.__file__)), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(),
       "compose": subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip(), "kits": {}}
for key in KITS:
    try:
        cls = find_cls(key)
    except Exception as e:
        out["kits"][key] = {"error": f"import {e!r}"}; continue
    api = FastAPI(); app = App.boot("Kit_" + key); app.add(cls); app.use_channel(asgi_app=api)
    inst = app._behavior.get(key) if hasattr(app._behavior, "get") else None
    if inst is None: out["kits"][key] = {"error": "no instance"}; continue
    CODES = {}
    for name, m in inspect.getmembers(type(inst)):
        f = unwrap(getattr(m, "__func__", m))
        if hasattr(f, "__code__") and f.__code__.co_filename.endswith(f"{key}.py"):
            CODES[f.__code__] = name
    if key == "command":
        try:
            with app.trust(): app.dispatch("command.open_pal")
        except Exception as e: print("open_pal", e, file=sys.stderr)
    html = str(inst.render())
    p = P(); p.feed(html)
    ctrls = [n for n in p.all if n.attrs.get("data-channel-action")]
    c = TestClient(api, raise_server_exceptions=False)
    res = []
    for n in ctrls:
        act = n.attrs["data-channel-action"]; args = json.loads(n.attrs.get("data-channel-args") or "{}")
        form = {}
        fo = closest_form(n)
        if fo is not None:
            for i in walk(fo):
                if i.tag in ("input", "textarea", "select") and i.attrs.get("name") and i.attrs.get("type") not in ("button", "submit"):
                    form[i.attrs["name"]] = f"V_{i.attrs['name']}"
        if n.tag in ("input", "textarea", "select") and n.attrs.get("name"):
            form.setdefault(n.attrs["name"], f"V_{n.attrs['name']}")
        body = {"v": "1", "action": act, "args": args, "cap": n.attrs.get("data-channel-cap"), "form": form}
        seen.clear(); sys.setprofile(prof); threading.setprofile_all_threads(prof)
        try: r = c.post("/ux-channel/action", json=body)
        finally: sys.setprofile(None); threading.setprofile_all_threads(None)
        meth = act.split(".", 1)[1]
        recv = next((l for nm, l in seen if nm == meth), None)
        fields = {}
        for k, v in form.items():
            if recv is None: fields[k] = "NOT RUN"; continue
            flat = {kk: vv for kk, vv in recv.items() if not isinstance(vv, dict)}
            for vv in recv.values():
                if isinstance(vv, dict): flat.update({f"**{kk}": x for kk, x in vv.items()})
            hit = [kk for kk, x in flat.items() if x == v]
            fields[k] = ("via " + ",".join(hit)) if hit else "LOST"
        kwname = [kk for kk, vv in (recv or {}).items() if isinstance(vv, dict)]
        res.append({"action": act, "sealed": args, "form": sorted(form), "status": r.status_code,
                    "ran": recv is not None, "fields": fields,
                    "kwargs": {kk: sorted((recv or {})[kk]) for kk in kwname}})
    out["kits"][key] = {"class": cls.__name__, "ncodes": len(CODES), "controls": res}
print(json.dumps(out, indent=1))
