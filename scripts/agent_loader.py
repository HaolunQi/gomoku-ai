# scripts/agent_loader.py
from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Optional, Type, Dict

from agents.base import Agent 


def _iter_agent_subclasses() -> Dict[str, Type[Agent]]:
    """
    Import agents.* modules and collect Agent subclasses with a string `name`.
    Returns mapping: agent_name -> agent_class
    """
    import agents  # package

    mapping: Dict[str, Type[Agent]] = {}

    for m in pkgutil.iter_modules(agents.__path__, agents.__name__ + "."):
        mod = importlib.import_module(m.name)

        for _, obj in vars(mod).items():
            if not inspect.isclass(obj):
                continue
            if obj is Agent:
                continue
            if not issubclass(obj, Agent):
                continue

            name = getattr(obj, "name", None)
            if isinstance(name, str) and name.strip():
                key = name.strip().lower()
                if key in mapping and mapping[key] is not obj:
                    raise ValueError(
                        f"Duplicate agent name {key!r}: {mapping[key].__module__}.{mapping[key].__name__} "
                        f"and {obj.__module__}.{obj.__name__}"
                    )
                mapping[key] = obj

    return mapping

_AGENT_MAP: Dict[str, Type[Agent]] | None = None


def available_agents() -> Dict[str, Type[Agent]]:
    global _AGENT_MAP
    if _AGENT_MAP is None:
        _AGENT_MAP = _iter_agent_subclasses()
    return _AGENT_MAP


def _construct(cls: Type[Agent], *, seed: Optional[int] = None) -> Agent:
    try:
        sig = inspect.signature(cls)
        if "seed" in sig.parameters:
            return cls(seed=seed)  # type: ignore[misc]
        return cls()              # type: ignore[misc]
    except (TypeError, ValueError):
        return cls()              # type: ignore[misc]


def load_agent(name_or_spec: str, *, seed: Optional[int] = None) -> Agent:
    s = name_or_spec.strip()

    if ":" in s:
        module_name, class_name = s.split(":", 1)
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        if not inspect.isclass(cls) or not issubclass(cls, Agent):
            raise ValueError(f"{s!r} is not an Agent subclass")
        return _construct(cls, seed=seed)

    key = s.lower()
    amap = available_agents()
    if key not in amap:
        opts = ", ".join(sorted(amap.keys()))
        raise ValueError(f"Unknown agent name: {s!r}. Available: {opts}")
    return _construct(amap[key], seed=seed)
