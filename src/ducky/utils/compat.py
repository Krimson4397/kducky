"""CircuitPython compatibility shim for missing stdlib modules.

CircuitPython 10.x lacks ``dataclasses`` and has a minimal ``typing``
(no ``Protocol``, no ``runtime_checkable``).  This module provides
minimal substitutes that match the subset of features used by this
project — the real CPython module is preferred when available.
"""

# ruff: noqa: N807 — dunder methods intentionally named for Python protocols

# ── dataclasses ────────────────────────────────────────────────────────────
# CircuitPython 10.x does not ship dataclasses.

try:
    from dataclasses import dataclass as _real_dataclass

    def dataclass(cls=None, *, frozen=False):
        """Wrap real dataclasses.dataclass for uniform import."""
        return _real_dataclass(cls, frozen=frozen) if cls is not None else _real_dataclass(frozen=frozen)  # noqa: E501

except ImportError:
    # Minimal dataclass for CircuitPython — supports frozen=True with
    # type-annotated fields (no field(), no slots, no kw_only).
    _MISSING = object()

    def dataclass(cls=None, *, frozen=False):
        """Minimal ``@dataclass`` for CircuitPython."""

        def _wrap(cls):
            annotations = getattr(cls, "__annotations__", {})
            class_defaults = getattr(cls, "__defaults__", {})
            fields: list[tuple[str, object]] = []

            if annotations:
                for name in annotations:
                    default = class_defaults.get(name, getattr(cls, name, _MISSING))
                    fields.append((name, default))
            else:
                # CircuitPython fallback: __annotations__ not populated
                slot_names = getattr(cls, "__slots__", ())
                if isinstance(slot_names, str):
                    slot_names = (slot_names,)
                seen: set[str] = set()
                for name in slot_names:
                    if not name.startswith('_'):
                        default = class_defaults.get(name, getattr(cls, name, _MISSING))
                        fields.append((name, default))
                        seen.add(name)
                # Fields with defaults stored in __defaults__ but not in __slots__
                # (avoids __slots__ + class variable conflict on CPython)
                for name, value in class_defaults.items():
                    if name not in seen:
                        fields.append((name, value))

            def __init__(self, *args: object, **kwargs: object) -> None:
                if len(args) > len(fields):
                    raise TypeError(
                        f"{cls.__name__} takes at most {len(fields)} positional arguments"
                    )
                for i in range(len(args)):
                    setattr(self, fields[i][0], args[i])
                missing: list[str] = []
                for i in range(len(args), len(fields)):
                    name, default = fields[i]
                    if name in kwargs:
                        setattr(self, name, kwargs[name])
                    elif default is not _MISSING:
                        setattr(self, name, default)
                    else:
                        missing.append(name)
                if missing:
                    raise TypeError(
                        f"{cls.__name__} missing {len(missing)} required "
                        f"argument(s): {', '.join(missing)}"
                    )

            def __repr__(self) -> str:
                parts = [f"{n}={getattr(self, n)!r}" for n, _ in fields]
                return f"{cls.__name__}({', '.join(parts)})"

            def __eq__(self, other: object) -> bool:
                if type(self) is not type(other):
                    return NotImplemented
                return all(getattr(self, n) == getattr(other, n) for n, _ in fields)

            def __hash__(self) -> int:
                return hash(tuple(getattr(self, n) for n, _ in fields))

            cls.__init__ = __init__
            cls.__repr__ = __repr__
            cls.__eq__ = __eq__
            cls.__hash__ = __hash__
            return cls

        if cls is not None:
            return _wrap(cls)
        return _wrap


# ── typing.Protocol / runtime_checkable ──────────────────────────────────
# CircuitPython's typing module lacks these.

try:
    from typing import Protocol, runtime_checkable
except ImportError:

    class Protocol:
        """Minimal Protocol substitute — structural typing not needed at runtime."""
        __slots__ = ()

    def runtime_checkable(cls):
        """No-op fallback — runtime isinstance checks not available."""
        return cls


# ── @enum decorator / auto / unique ─────────────────────────────────────
# CircuitPython 10.x does not support metaclasses or __init_subclass__.
# This decorator-based approach avoids both entirely.

class _auto:  # noqa: N801
    """Sentinel for auto-generated enumeration values."""
    __slots__ = ()

    def __repr__(self):
        return "<auto>"


def auto():
    """Return a sentinel for auto-generated enumeration values.

    Behaves like CPython's enum.auto().
    """
    return _auto()


def unique(cls):
    """Decorate an enum class to validate no duplicate values.

    Must be applied AFTER @enum::

        @unique
        @enum
        class Foo:
            A = 1
            B = 1  # raises ValueError
    """
    seen = {}
    for key in list(cls.__dict__):
        if key.startswith('_'):
            continue
        val = getattr(cls, key)
        if not hasattr(val, '_value_'):
            continue
        v = val._value_
        if v in seen:
            raise ValueError(
                f"Duplicate value {v!r} in {cls.__name__}: "
                f"{seen[v]} and {key}"
            )
        seen[v] = key
    return cls


# ── Helper functions for @enum member methods ─────────────────────────

def _enum_name(self):
    return self._name_


def _enum_value(self):
    return self._value_


def _enum_eq(self, other):
    if type(self) is type(other):
        return self._value_ == other._value_
    return NotImplemented


def _enum_hash(self):
    return hash((type(self), self._value_))


def _enum_str(self):
    return f"{type(self).__name__}.{self._name_}"


def _enum_repr(self):
    return f"<{type(self).__name__}.{self._name_}: {self._value_!r}>"


def _enum_bool(self):
    return True


# ── @enum decorator ───────────────────────────────────────────────────

def enum(cls):
    """Decorate a class to turn it into an enum-like type.

    Replaces auto() sentinels and value assignments with member objects
    having .name and .value properties.

    Usage::

        @enum
        class Color:
            RED = auto()
            GREEN = auto()
            BLUE = auto()
    """
    _last_value = 0
    members = []

    for key, val in list(cls.__dict__.items()):
        if key.startswith('_'):
            continue
        if isinstance(val, _auto):
            _last_value += 1
            val = _last_value
        elif isinstance(val, int):
            _last_value = max(_last_value, val)
        member = object.__new__(cls)
        member._name_ = key
        member._value_ = val
        setattr(cls, key, member)
        members.append(member)

    cls.name = property(_enum_name)
    cls.value = property(_enum_value)
    cls.__eq__ = _enum_eq
    cls.__hash__ = _enum_hash
    cls.__str__ = _enum_str
    cls.__repr__ = _enum_repr
    cls.__bool__ = _enum_bool

    def _by_name(cls, name):
        for m in members:
            if m._name_ == name:
                return m
        raise KeyError(name)

    def _members(cls):
        return tuple(members)

    cls.by_name = classmethod(_by_name)
    cls.members = classmethod(_members)

    return cls
