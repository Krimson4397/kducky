"""Standalone CircuitPython Enum Compatibility Test.

Copy this file to a CircuitPython device and run it directly.
Tests individual MicroPython features used by the kducky compat.py Enum implementation.
"""

import sys


def test(description, fn):
    """Run a test and print PASS/FAIL."""
    try:
        fn()
        print(f"  PASS: {description}")
    except Exception as e:
        print(f"  FAIL: {description}")
        print(f"    {type(e).__name__}: {e}")
        # Try to print traceback if available
        if hasattr(sys, "print_exception"):
            sys.print_exception(sys.exc_info()[1])


print("\n=== Enum Compatibility Tests for CircuitPython ===")
print(f"Platform: {sys.platform}")
print(f"Version: {sys.version}")

# ── Test 1: Does 'import enum' work? ──
print("\n1. Can we import enum module?")
test("import enum", lambda: __import__("enum"))

# ── Test 2: Can we subclass type? ──
print("\n2. Metaclass basics (subclassing type):")
test("class Meta(type): pass", lambda: type("Meta", (type,), {}))
Meta = type("Meta", (type,), {})
test("type() with 3 args 'class X():'", lambda: type("X", (), {}))
test("type() with 3 args 'class X(Base):'", lambda: type("X", (object,), {}))

# ── Test 3: Calling a metaclass ──
print("\n3. Can we create classes via metaclass call?")
test("Meta('C', (), {})", lambda: Meta("C", (), {}))
Meta2 = type("Meta2", (type,), {"__iter__": lambda cls: iter([1])})
test("Meta2('C', (), {})", lambda: Meta2("C", (), {}))

# ── Test 4: type.__new__ with various args ──
print("\n4. type.__new__() variations:")
test("type.__new__(Meta, 'A', (), {})", lambda: type.__new__(Meta, "A", (), {}))
try:
    t = type.__new__(Meta, "A", (object,), {})
    print(f"  PASS: type.__new__(Meta, 'A', (object,), {{}}) -> {t}")
except Exception as e:
    print(f"  FAIL: type.__new__(Meta, 'A', (object,), {{}})")
    print(f"    {type(e).__name__}: {e}")

# ── Test 5: class statement with metaclass ──
print("\n5. Class statement with metaclass types:")
test("class C(metaclass=Meta): pass", lambda: type("C", (), {"__class__": type}))

# ── Test 6: __init_subclass__ ──
print("\n6. __init_subclass__ support:")
def _subclass_hook(cls, **kwargs):
    print(f"    init_subclass called for {cls.__name__}")
BaseWithHook = type("BaseWithHook", (), {
    "__init_subclass__": classmethod(_subclass_hook),
})
test("subclass with __init_subclass__", lambda: type("Sub", (BaseWithHook,), {}))
test("nested subclass", lambda: type("Sub2", (type("Sub1", (BaseWithHook,), {}),), {}))

# ── Test 7: __slots__ ──
print("\n7. __slots__ support:")
test("__slots__ in type() call", lambda: type("S", (), {"__slots__": ()}))
test("__slots__ with names", lambda: type("S", (), {"__slots__": ("_name_", "_value_")}))

# ── Test 8: property() ──
print("\n8. property() support:")
test("property in type()", lambda: type("P", (), {"x": property(lambda self: 42)}))

# ── Test 9: isinstance with metaclass types ──
print("\n9. isinstance support:")
A = Meta("A", (), {})
test("isinstance(A, Meta)", lambda: isinstance(A, Meta))
B = type("B", (), {})
test("isinstance(B, type)", lambda: isinstance(B, type))

# ── Test 10: auto() pattern ──
print("\n10. auto() pattern:")
class _auto_sentinel:
    def __repr__(self):
        return "<auto>"
def make_auto():
    return _auto_sentinel()
test("auto() callable", lambda: make_auto())
a = make_auto()
test("auto() returns sentinel", lambda: isinstance(a, _auto_sentinel))
test("two auto() calls return different objects", lambda: make_auto() is not make_auto())

# ── Test 11: Exact compat.py creation order ──
print("\n11. Exact compat.py enum pattern:")
try:
    class _EnumMeta(type):
        """Metaclass with __iter__, __contains__, __getitem__."""
        def __iter__(cls):
            return iter(cls._member_map_.values())
        def __contains__(cls, item):
            if isinstance(item, cls):
                return item is cls._member_map_.get(item._name_)
            return item in cls._member_map_
        def __getitem__(cls, name):
            return cls._member_map_[name]
    print("  PASS: _EnumMeta created")

    def _enum_name(self): return self._name_
    def _enum_value(self): return self._value_
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
    def _enum_init_subclass(cls, **kwargs):
        print(f"    init_subclass for {cls.__name__}")
        members = {}
        auto_count = 0
        for key, val in list(cls.__dict__.items()):
            if key.startswith('_'):
                continue
            if isinstance(val, _auto_sentinel):
                auto_count += 1
                val = auto_count
            member = object.__new__(cls)
            member._name_ = key
            member._value_ = val
            setattr(cls, key, member)
            members[key] = member
        cls._member_map_ = members

    Enum = _EnumMeta("Enum", (), {
        "__slots__": ("_name_", "_value_"),
        "_member_map_": {},
        "name": property(_enum_name),
        "value": property(_enum_value),
        "__eq__": _enum_eq,
        "__hash__": _enum_hash,
        "__str__": _enum_str,
        "__repr__": _enum_repr,
        "__bool__": _enum_bool,
        "__init_subclass__": classmethod(_enum_init_subclass),
    })
    print("  PASS: Enum base created via metacall")
    
    # Test with simple members first
    class TestEnum(Enum):
        A = 1
        B = 2
        C = 3
    print("  PASS: TestEnum created with explicit values")
    print(f"    members: {[k for k in TestEnum._member_map_]}")
    
    # Test auto()
    class AutoEnum(Enum):
        X = make_auto()
        Y = make_auto()
        Z = make_auto()
    print("  PASS: AutoEnum created with auto values")
    print(f"    X = {AutoEnum.X._value_}, Y = {AutoEnum.Y._value_}, Z = {AutoEnum.Z._value_}")
    
    # Test isinstance
    test("isinstance(AutoEnum.X, AutoEnum)", lambda: isinstance(AutoEnum.X, AutoEnum))
    
    # Test name
    test("AutoEnum.X.name", lambda: AutoEnum.X._name_ == "X")
    
    # Test iteration
    test("list(AutoEnum)", lambda: list(AutoEnum))
    
except Exception as e:
    print(f"  FAIL: {type(e).__name__}: {e}")
    if hasattr(sys, "print_exception"):
        sys.print_exception(sys.exc_info()[1])

# ── Test 12: Large enum (like TokenType) ──
print("\n12. Large enum test (140+ members):")
try:
    ns = {}
    for i in range(150):
        ns[f"MEMBER_{i}"] = make_auto() if i % 2 == 0 else i
    LargeEnum = _EnumMeta("LargeEnum", (Enum,), ns)
    print(f"  PASS: LargeEnum with {len(LargeEnum._member_map_)} members")
except Exception as e:
    print(f"  FAIL: Large enum creation: {type(e).__name__}: {e}")

# ── Test 13: Class statement (not type() call) ──
print("\n13. Class statement with Enum base:")
try:
    class MyEnum(Enum):
        ALPHA = 1
        BETA = 2
    print(f"  PASS: MyEnum defined via class statement")
    print(f"    ALPHA = {MyEnum.ALPHA._value_}")
except Exception as e:
    print(f"  FAIL: class statement: {type(e).__name__}: {e}")

print("\n=== Tests complete ===")
