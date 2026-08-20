"""
App — progressive composition root and boot façade.

Owns only glue: progressive levels, attach order, registration of Components,
offline dispatch, and (via wire/) optional Channel + Motion attachment.
Never invents Document, Caps, or Plan IR.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Type

from ux_compose.component import Component
from ux_compose.progressive import Level


class App:
    """
    Progressive composition root.

    Example:
        app = App.boot("Shop")                  # Level 1 by default
        app = App.boot("Shop").use_channel()    # Level 2
        app = App.boot("Shop").use_channel().use_motion()  # Level 3
        app.add(Cart)
        ops = app.dispatch("cart.add", sku="tee")  # works offline and live
    """

    def __init__(self, name: str = "App", *, strict_caps: bool = False):
        self.name = name
        self.strict_caps = strict_caps
        self._components: Dict[str, Type[Component]] = {}
        self._instances: Dict[str, Component] = {}
        self._level = Level.L0
        self._behavior = None
        self._channel = None
        self._document = None
        self._motion = False
        self._cek = None

    @classmethod
    def boot(cls, name: str = "App", *, strict_caps: bool = False, level: int = 1) -> "App":
        """Boot at the requested progressive level (default L1 = Behavior)."""
        app = cls(name, strict_caps=strict_caps)
        if level >= 1:
            app.use_behavior()
        if level >= 2:
            try:
                app.use_channel()
            except Exception:
                pass
        if level >= 3:
            try:
                app.use_motion()
            except Exception:
                pass
        return app

    def use_dom(self, document: Any = None) -> "App":
        """Attach Document (ux-dom). Document SSoT respected."""
        self._document = document
        return self

    def use_behavior(self) -> "App":
        """Unlock Level 1 — offline interactive Behavior + MorphState + @action."""
        if self._behavior is not None:
            return self
        try:
            from ux_behavior import Behavior
            self._behavior = Behavior.boot(self.name, strict_caps=self.strict_caps)
            self._level = max(self._level, Level.L1)
            # If ux-motion is installed, pre-register transition.* on the stamp so
            # authors can return scene Plans from @action without stamp reject.
            # Full L3 still requires use_motion() for MotionChannel peel.
            try:
                import ux_motion  # noqa: F401
                self._register_motion_stamp()
            except ImportError:
                pass
        except ImportError:
            # Offline shim when specialist missing
            self._behavior = _LocalBehavior(self)
            self._level = max(self._level, Level.L1)
        return self

    def use_channel(self, **config) -> "App":
        """Unlock Level 2. Imports only through wire/ (Isolation Law).

        When ux-channel is absent, degrades gracefully and stays at current level.
        Level is only elevated when the wire door successfully imports Channel.

        Pass asgi_app=FastAPI() so Channel.boot mounts /ux-channel on the real
        host. Do not pass a Channel instance as asgi — attach_channel owns
        Behavior.attach(asgi) so include_router lands on FastAPI.
        """
        if self._channel is not None:
            return self
        self.use_behavior()
        try:
            from ux_compose.wire.boot import attach_channel
            ch = attach_channel(self, **config)
            self._channel = ch
            # attach_channel owns Behavior.attach — do NOT re-attach Channel as asgi
            self._level = max(self._level, Level.L2)
        except ImportError:
            # Progressive: stay at current level; offline continues to work
            pass
        return self

    def use_motion(self) -> "App":
        """Unlock Level 3. Motion + MotionChannel via controlled wire door.

        When ux-motion is absent, degrades gracefully and stays at current level.
        Level is only elevated when Motion/MotionChannel import succeeds.
        Registers transition.play on the Behavior session stamp so motion Plans
        are valid Ops under the Cap/stamp model (Composition Algebra).
        """
        try:
            from ux_compose.wire.boot import attach_motion
            Motion, MotionChannel = attach_motion()
            self._motion = True
            self._level = max(self._level, Level.L3)
            if self._document is not None and hasattr(self._document, "use"):
                self._document.use(Motion, MotionChannel)
            # Allow transition.play Ops on the Behavior stamp (Morph-then-Play)
            self._register_motion_stamp()
        except ImportError:
            # Progressive: stay at current level; L1/L2 continue to work
            pass
        return self

    def use_cek(self, *, mode: str = "adapt") -> "App":
        """Optional CEK door via wire/ only. Progressive: degrades if cek_host absent."""
        if self._channel is None:
            self.use_channel()
        try:
            from ux_compose.wire.cek import attach_cek
            self._cek = attach_cek(self._channel, mode=mode)
        except ImportError:
            if mode == "require":
                raise
            self._cek = None
        return self

    def mint_cap(self, action: str, args: Optional[dict] = None, **kwargs) -> str:
        """Thin wrap of wire.caps.mint_cap. Isolation door — product never imports channel."""
        if self._channel is None:
            self.use_channel()
        from ux_compose.wire.caps import mint_cap
        return mint_cap(self._channel, action, args, **kwargs)

    def submit_intent(
        self,
        action: str,
        *,
        cap: Optional[str] = None,
        mint: bool = False,
        args: Optional[dict] = None,
        **kwargs,
    ):
        """Thin wrap of wire.caps.submit_intent. Checkout succeeds only with a real Cap."""
        if self._channel is None:
            self.use_channel()
        from ux_compose.wire.caps import submit_intent
        return submit_intent(
            self._channel, action, cap=cap, mint=mint, args=args, **kwargs
        )

    async def submit_intent_async(
        self,
        action: str,
        *,
        cap: Optional[str] = None,
        mint: bool = False,
        args: Optional[dict] = None,
        **kwargs,
    ):
        """ASGI-safe Intent submit (Channel.registry.async_dispatch)."""
        if self._channel is None:
            self.use_channel()
        from ux_compose.wire.caps import async_submit_intent
        return await async_submit_intent(
            self._channel, action, cap=cap, mint=mint, args=args, **kwargs
        )

    def _register_motion_stamp(self) -> None:
        """Register transition.* pairs so motion Plans pass Behavior stamp checks."""
        behavior = self._behavior
        if behavior is None or not hasattr(behavior, "domain"):
            return
        try:
            behavior.domain(
                "motion",
                "1",
                pairs=(
                    ("transition", "play"),
                    ("transition", "cancel"),
                    ("transition", "rewind"),
                ),
            )
        except Exception:
            # Already registered or Behavior version without domain API
            pass

    def add(self, *components: Type[Component]) -> "App":
        self.use_behavior()  # ensure L1
        for c in components:
            key = getattr(c, "id", None) or c.__name__.lower()
            self._components[key] = c
            if self._behavior is not None and hasattr(self._behavior, "add"):
                self._behavior.add(c)
        if self._channel is not None and self._behavior is not None:
            try:
                from ux_compose.wire.caps import bridge_actions
                bridge_actions(self._behavior, self._channel)
            except Exception:
                pass
        return self

    def dispatch(self, action: str, **kwargs) -> List[Any]:
        """Offline-first dispatch. Same surface for tests, agents, and live."""
        self.use_behavior()
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


class _LocalBehavior:
    """Minimal offline Behavior shim when ux-behavior is absent."""
    def __init__(self, app: App):
        self.app = app
        self._registry = {}

    def add(self, comp_cls):
        key = getattr(comp_cls, "id", None) or comp_cls.__name__.lower()
        self._registry[key] = comp_cls

    def dispatch(self, action: str, **kwargs):
        return _local_dispatch(self.app, action, **kwargs)


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
    # Cap Law — offline fail-closed under strict_caps
    caps = getattr(fn, "_ux_caps", ()) or ()
    if getattr(app, "strict_caps", False) and caps and getattr(app, "_channel", None) is None:
        raise PermissionError(
            f"AuthorityError: '{action}' requires Cap {caps} "
            "(offline strict; attach Channel, use trust(), or set strict_caps=False)"
        )
    result = fn(**kwargs)
    if result is None:
        target = getattr(inst, "id", None) or comp_id
        dirty = set()
        if hasattr(inst, "dirty_fields"):
            dirty = inst.dirty_fields()
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
