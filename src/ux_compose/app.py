"""App — progressive composition root and boot façade.

Owns glue only: levels, attach order, Component registration, offline dispatch.
Missing specialists write ``app.attach_notes`` instead of raising.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from ux_compose.component import Component
from ux_compose.attach_notes import AttachNotes, note, using
from ux_compose.progressive import Level


class App:
    """Progressive composition root."""

    def __init__(self, name: str = "App", *, strict_caps: bool = False):
        self.name = name
        self.strict_caps = strict_caps
        self._components: Dict[str, Type[Component]] = {}
        self._instances: Dict[str, Component] = {}
        self._level = Level.L0
        self._behavior = None
        self._channel = None
        self._channel_asgi = None
        self._document = None
        self._author_document = None
        self._motion = False
        self._cek = None
        self._host = "auto"
        self._notes = AttachNotes()

    def _note(self, door: str, wanted: str, reason: Any, *, level_kept: int | None = None):
        kept = int(self._level) if level_kept is None else level_kept
        with using(self._notes):
            return note(door, wanted, reason, level_kept=kept)

    @property
    def attach_notes(self):
        """This App's attach step-downs. Process-wide list is attach_notes()."""
        return self._notes.snapshot()

    @classmethod
    def boot(cls, name: str = "App", *, strict_caps: bool = False, level: int | str = "auto") -> "App":
        app = cls(name, strict_caps=strict_caps)
        auto = isinstance(level, str) and str(level).lower() == "auto"
        if auto:
            app.use_behavior()
            return app
        lv = max(0, min(3, int(level)))
        if lv >= 1:
            app.use_behavior()
        if lv >= 2:
            try:
                app.use_channel()
            except Exception as exc:
                app._note("boot.use_channel", "L2", exc)
        if lv >= 3:
            try:
                app.use_motion()
            except Exception as exc:
                app._note("boot.use_motion", "L3", exc)
        return app

    def use_host(self, host: str = "fastapi") -> "App":
        self._host = (host or "auto").lower().strip()
        return self

    def use_dom(self, document: Any = None, *, author: bool = True) -> "App":
        self._document = document
        if author:
            self._author_document = document
        return self

    def use_behavior(self) -> "App":
        if self._behavior is not None:
            return self
        try:
            from ux_behavior import Behavior
            self._behavior = Behavior.boot(self.name, strict_caps=self.strict_caps)
            self._level = max(self._level, Level.L1)
            try:
                import ux_motion  # noqa: F401
                self._register_motion_stamp()
            except ImportError as exc:
                self._note("use_behavior.motion_stamp", "L3", exc)
        except ImportError as exc:
            self._note("use_behavior", "ux-behavior", exc, level_kept=1)
            self._behavior = _LocalBehavior(self)
            self._level = max(self._level, Level.L1)
        return self

    def use_channel(self, **config) -> "App":
        asgi = config.get("asgi_app")
        if self._channel is not None and asgi is None:
            return self
        if self._channel is not None and asgi is not None:
            if getattr(self, "_channel_asgi", None) is asgi:
                return self
            behavior = self._behavior
            if behavior is not None and getattr(behavior, "_wire", None) is not None:
                behavior._wire = None
            self._channel = None
        self.use_behavior()
        try:
            from ux_compose.wire.boot import attach_channel
            ch = attach_channel(self, **config)
            self._channel = ch
            self._channel_asgi = asgi
            self._level = max(self._level, Level.L2)
        except ImportError as exc:
            self._note("use_channel", "L2", exc)
        return self

    def use_motion(self) -> "App":
        try:
            from ux_compose.wire.boot import attach_motion
            Motion, MotionChannel = attach_motion()
            self._motion = True
            self._level = max(self._level, Level.L3)
            if self._document is not None and hasattr(self._document, "use"):
                self._document.use(Motion, MotionChannel)
            self._register_motion_stamp()
        except ImportError as exc:
            self._note("use_motion", "L3", exc)
        return self

    def use_cek(self, *, mode: str = "adapt") -> "App":
        if self._channel is None:
            self.use_channel()
        try:
            from ux_compose.wire.cek import attach_cek
            self._cek = attach_cek(self._channel, mode=mode)
        except ImportError as exc:
            if mode == "require":
                raise
            self._note("use_cek", "cek_host", exc)
            self._cek = None
        return self

    def mint_cap(self, action: str, args: Optional[dict] = None, **kwargs) -> str:
        if self._channel is None:
            self.use_channel()
        from ux_compose.wire.caps import mint_cap
        return mint_cap(self._channel, action, args, **kwargs)

    def submit_intent(self, action: str, *, cap: Optional[str] = None, mint: bool = False, args: Optional[dict] = None, **kwargs):
        if self._channel is None:
            self.use_channel()
        from ux_compose.wire.caps import submit_intent
        return submit_intent(self._channel, action, cap=cap, mint=mint, args=args, **kwargs)

    async def submit_intent_async(self, action: str, *, cap: Optional[str] = None, mint: bool = False, args: Optional[dict] = None, **kwargs):
        if self._channel is None:
            self.use_channel()
        from ux_compose.wire.caps import async_submit_intent
        return await async_submit_intent(self._channel, action, cap=cap, mint=mint, args=args, **kwargs)

    def _register_motion_stamp(self) -> None:
        behavior = self._behavior
        if behavior is None or not hasattr(behavior, "domain"):
            return
        try:
            behavior.domain("motion", "1", pairs=(("transition", "play"), ("transition", "cancel"), ("transition", "rewind")))
        except Exception as exc:
            self._note("motion_stamp", "transition.play", exc)

    def add(self, *components: Type[Component]) -> "App":
        self.use_behavior()
        for c in components:
            key = getattr(c, "id", None) or c.__name__.lower()
            self._components[key] = c
            if self._behavior is not None and hasattr(self._behavior, "add"):
                self._behavior.add(c)
        if self._channel is not None and self._behavior is not None:
            try:
                from ux_compose.wire.caps import bridge_actions
                bridge_actions(self._behavior, self._channel)
            except Exception as exc:
                self._note("add.bridge_actions", "caps", exc)
        return self

    def mount(self, package_dir, *, asgi_app=None, base: str = "routes", base_directory: str | None = None, fail_closed: bool = True, bind_pages: bool = True, include_directory_router: bool | None = None, on_surface=None, package_name=None, host: str | None = None):
        if include_directory_router is not None:
            bind_pages = include_directory_router
        from ux_compose.surfaces import mount_surfaces
        self.use_behavior()
        return mount_surfaces(package_dir=package_dir, base_directory=base_directory or base, compose_app=self, asgi_app=asgi_app, fail_closed=fail_closed, bind_pages=bind_pages, on_surface=on_surface, package_name=package_name, host=host or getattr(self, "_host", "auto"))

    def dispatch(self, action: str, **kwargs) -> List[Any]:
        self.use_behavior()
        kwargs = _unpack_action_kwargs(kwargs)
        if self._behavior is not None and hasattr(self._behavior, "dispatch"):
            return self._behavior.dispatch(action, **kwargs) or []
        return _local_dispatch(self, action, **kwargs)

    def control(self, action: str, **args) -> dict:
        self.use_behavior()
        if self._behavior is not None and hasattr(self._behavior, "control"):
            return self._behavior.control(action, **args)
        from ux_compose.helpers import control
        return control(action, **args)

    @property
    def level(self) -> Level:
        return self._level

    @property
    def behavior(self):
        self.use_behavior()
        return self._behavior

    def doctor(self, paths=None, *, fail: bool = False):
        from ux_compose.doctor import doctor
        return doctor(paths, fail=fail)


def _unpack_action_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    packed = kwargs.get("args")
    if not isinstance(packed, dict):
        return dict(kwargs)
    out = dict(packed)
    for key, value in kwargs.items():
        if key == "args":
            continue
        out[key] = value
    return out


class _LocalBehavior:
    def __init__(self, app: App):
        self.app = app
        self._registry = {}

    def add(self, comp_cls):
        key = getattr(comp_cls, "id", None) or comp_cls.__name__.lower()
        self._registry[key] = comp_cls

    def dispatch(self, action: str, **kwargs):
        return _local_dispatch(self.app, action, **_unpack_action_kwargs(kwargs))


def _local_dispatch(app: App, action: str, **kwargs) -> List[Any]:
    if "." in action:
        comp_id, method = action.rsplit(".", 1)
    else:
        comp_id = next(iter(app._components), None)
        method = action
    if not comp_id or comp_id not in app._components:
        return []
    cls = app._components[comp_id]
    inst = app._instances.get(comp_id)
    if inst is None:
        inst = cls()
        app._instances[comp_id] = inst
    fn = getattr(inst, method, None)
    if fn is None:
        return []
    caps = getattr(fn, "_ux_caps", ()) or ()
    if getattr(app, "strict_caps", False) and caps and getattr(app, "_channel", None) is None:
        raise PermissionError(
            f"AuthorityError: '{action}' requires Cap {caps} "
            "(offline strict; attach Channel, use trust(), or set strict_caps=False)"
        )
    result = fn(**kwargs)
    if result is None:
        target = getattr(inst, "id", None) or comp_id
        dirty = set(inst.dirty_fields()) if hasattr(inst, "dirty_fields") else set()
        ops = []
        if dirty or target:
            ops.append({"op": "morph", "target": f"#{target}", "strategy": "idiomorph"})
            if hasattr(inst, "clear_dirty"):
                inst.clear_dirty()
        return ops
    if isinstance(result, list):
        return result
    return [result]


__all__ = ["App"]
