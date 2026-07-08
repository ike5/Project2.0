# GLOSSARY

A plain-English dictionary of every term used across the course. Each entry is short; the modules go deep.

## OOP foundations

- **Object** — A bundle of data (attributes) and behavior (methods) living in memory. In Python, almost everything is an object: ints, strings, functions, your own classes.
- **Class** — A blueprint for creating objects. Defines what attributes and methods its instances will have. The `class` keyword creates one.
- **Instance** — A specific object built from a class. `d = Dog()` makes `d` an instance of `Dog`.
- **Method** — A function defined inside a class. The first parameter is conventionally `self`, the instance the method was called on.
- **Attribute** — A value attached to an object (instance) or to a class (class attribute). Accessed with dot notation: `obj.attr`.
- **`self`** — Inside a method, the parameter that refers to the current instance. Python fills it in for you at call time; you never pass it yourself.
- **`__init__`** — The "initializer" method. Runs right after a new instance is created. Used to set up initial state.
- **`__repr__`** — A dunder method that returns the developer-facing string form of an object. Used in the REPL, in debuggers, and inside containers.
- **`__str__`** — A dunder method that returns the user-facing string form. Used by `print()` and `str()`.

## Encapsulation

- **Encapsulation** — Bundling data and the code that operates on that data inside one unit (a class), and controlling how the outside world can touch that data.
- **Public attribute** — An attribute with a normal name like `name`. By convention, the outside world is free to read and write it.
- **"Protected" by convention (`_name`)** — A single leading underscore signals "internal, don't touch from outside." Python doesn't enforce this; it's a social contract.
- **Name-mangled (`__name`)** — A double leading underscore triggers Python's name-mangling. The attribute is renamed to `_ClassName__name` to avoid accidental clashes in subclasses. It's not true privacy.
- **Property** — A method decorated with `@property` so it can be accessed like an attribute (`obj.value`) while still running code on get/set/delete. The Pythonic replacement for getters and setters.
- **`@property.setter`** — The companion decorator that defines what happens when code writes to a property.
- **Read-only attribute** — A property with only a getter. Trying to set it raises `AttributeError`.

## Inheritance & polymorphism

- **Inheritance** — Defining a new class (`Child`) that reuses and extends an existing one (`Parent`). The child gets all the parent's attributes and methods.
- **Base / parent / superclass** — The class being inherited from.
- **Derived / child / subclass** — The class doing the inheriting.
- **`super()`** — A built-in function that returns a proxy to the parent class. Use it to call the parent's methods, typically from `__init__` or overridden methods.
- **Method overriding** — A subclass defines a method with the same name as one in the parent, replacing or extending its behavior.
- **Method resolution order (MRO)** — The order Python searches classes when looking up an attribute or method. Determined by C3 linearization. Inspect with `ClassName.mro()` or `ClassName.__mro__`.
- **`isinstance(obj, Class)`** — True if `obj` is an instance of `Class` or any of its subclasses.
- **`issubclass(Sub, Parent)`** — True if `Sub` is a subclass of `Parent`.
- **Multiple inheritance** — A class with more than one parent. Python supports it; the MRO keeps things deterministic.
- **Mixin** — A small class meant to be combined with others via multiple inheritance to add a specific capability. By convention, mixins don't define `__init__`.
- **Polymorphism** — "Many shapes." Code that calls `obj.do_thing()` works the same way regardless of what `obj` actually is, as long as it implements `do_thing()`.
- **Duck typing** — "If it walks like a duck and quacks like a duck, it's a duck." Python's default: type checks are based on what an object can do, not what class it is.
- **Abstract Base Class (ABC)** — A class that defines methods subclasses must implement. Use the `abc` module and the `@abstractmethod` decorator. You can't instantiate an ABC directly.
- **Protocol** — A typing construct (`typing.Protocol`) that describes what methods an object should have. Structural typing — no inheritance required.
- **Liskov Substitution Principle** — A subclass should be usable anywhere its parent was expected, without surprises. Violating it breaks polymorphism.

## Composition & structure

- **Composition** — Building a class out of other objects (it "has-a" Engine) instead of inheriting from them (it "is-a" Engine).
- **Delegation** — A wrapper object forwards method calls to an inner object it owns. The classic "has-a with forwarding" pattern.
- **Aggregation** — A weaker form of composition: the container has a reference to an object that can exist independently.
- **Dataclass** — A class decorated with `@dataclass` that auto-generates `__init__`, `__repr__`, and `__eq__` from annotated attributes. Great for value-like objects.

## Magic / dunder methods

- **Dunder method** — A method whose name starts and ends with double underscores (`__init__`, `__add__`, `__len__`). Lets you hook into Python's syntax and built-ins.
- **Operator overloading** — Defining dunder methods like `__add__`, `__lt__`, `__mul__` so your objects work with `+`, `<`, `*`, etc.
- **Context manager** — An object that defines `__enter__` and `__exit__`. Used by the `with` statement. Classic example: file objects.
- **Iterator** — An object with `__iter__` and `__next__`. The `for` loop consumes iterators.
- **`@staticmethod`** — A method that lives on the class but receives no implicit first argument. Use sparingly; often a free function is clearer.
- **`@classmethod`** — A method that receives the class itself (`cls`) as its first argument. Often used for alternative constructors.
- **`__slots__`** — A class-level tuple that fixes the set of allowed attributes. Saves memory and prevents accidental attribute creation. Trades off flexibility.

## Advanced

- **Descriptor** — An object that defines `__get__`, `__set__`, or `__delete__`. Properties, methods, `classmethod`, and `staticmethod` are all descriptors. The mechanism that powers "Python attributes are objects."
- **Metaclass** — The class of a class. By default, classes are instances of `type`. Custom metaclasses let you customize class creation. Powerful; rarely needed.
- **Method binding** — When you access `obj.method`, Python creates a bound method object with `obj` already plugged in as `self`. When you access `Class.method`, you get the raw function.

## Design patterns

- **Design pattern** — A reusable, named solution to a common design problem. Patterns are vocabulary, not rules.
- **Strategy** — Encapsulate a family of algorithms behind a common interface so the caller can swap them at runtime.
- **Observer** — An object (subject) keeps a list of dependents (observers) and notifies them of state changes.
- **Decorator pattern** — Wrap an object to add behavior, while keeping the same interface. Different from Python's `@decorator` syntax sugar.
- **Factory** — A function or method that builds and returns objects, hiding the construction logic from the caller.
- **Adapter** — A thin wrapper that translates one interface into another the client expects.

## Testing

- **Unit test** — A test that exercises one small piece of behavior in isolation.
- **pytest** — The dominant Python testing framework. Discovers files named `test_*.py` and functions named `test_*`.
- **Fixture** — A reusable test setup helper, decorated with `@pytest.fixture`. Used to provide objects to tests.
- **Mock** — A test double that stands in for a real object, recording how it was called. Use `unittest.mock.Mock` or `pytest-mock`.
- **Test coverage** — A measure of what fraction of your code is exercised by tests. `pytest-cov` reports it.
- **Test-driven development (TDD)** — Write a failing test, write the minimum code to make it pass, refactor. Repeat.
