import importlib
import inspect
import pkgutil

from agents.base import Agent


def _iter_agent_subclasses():
    # Import agents.* modules and collect Agent subclasses by name
    import agents

    mapping = {}

    for m in pkgutil.iter_modules(agents.__path__, agents.__name__ + "."):
        mod = importlib.import_module(m.name)

        for obj in vars(mod).values():
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
                        f"Duplicate agent name {key!r}: "
                        f"{mapping[key].__module__}.{mapping[key].__name__} "
                        f"and {obj.__module__}.{obj.__name__}"
                    )
                mapping[key] = obj

    return mapping


_AGENT_MAP = None


def available_agents():
    # Return cached mapping of agent_name -> agent_class
    global _AGENT_MAP
    if _AGENT_MAP is None:
        _AGENT_MAP = _iter_agent_subclasses()
    return _AGENT_MAP


def _construct(cls, seed=None):
    # Construct agent, passing seed if supported
    try:
        sig = inspect.signature(cls)
        if "seed" in sig.parameters:
            return cls(seed=seed)
        return cls()
    except (TypeError, ValueError):
        return cls()


def load_agent(name_or_spec, seed=None):
    # Load agent by short name or module:Class spec
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
