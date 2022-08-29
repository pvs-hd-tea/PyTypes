## Principles

The project has a need for a bidirectional lookup of types and modules;
When the [tracer implementation](../workflow/tracing.md#tracer---setting-syssettrace-and-collecting-data) finds an instance that needs logging, it can query the `Resolver` for a module path and the instance's type's qualified name.
Similary, when given strings containing a module path and a type's qualified name, the `Resolver` is capable of loading the requested type from its file.

## API

### Retrieving Module Path and Qualified Type Name from a [`type`](https://docs.python.org/3/library/functions.html#type)

The process of type to module & path is performed by querying the given [`type`](https://docs.python.org/3/library/functions.html#type) using the [`__module__` and `__file__`](https://docs.python.org/3/library/inspect.html), together with [`sys.modules`](https://docs.python.org/3/library/sys.html#sys.modules).

[sys.modules](https://docs.python.org/3/library/sys.html#sys.modules) can be queried using a `type`'s  `__module__` attribute.
For builtin types, this query delivers `"builtins"`, which is caught as an early-return.
Using the [`__file__`] attribute on the query's result, using the [paths specified in the config file](config.md), the `Resolver` can determine by detection of relative paths whether the requested type is from the traced project, the standard library, or from a third-party dependency.

#### Examples:

```py
>>> resolver.get_module_and_name(ty=int)
(None, 'int')

>>> resolver.get_module_and_name(ty=pathlib.Path)
('pathlib', 'Path')

>>> resolver.get_module_and_name(ty=fractions.Fraction)
('fractions', 'Fraction')

>>> class Outer:
...     class Inner:
...         class EvenMoreInner:
...             ...

>>> r.get_module_and_name(ty=Outer.Inner.EvenMoreInner)
('__main__', 'Outer.Inner.EvenMoreInner')
```


### Creating a `type` from a Module Path and Qualified Type Name

The process of module & path to `type` is facilitated by Python's [`importlib`](https://docs.python.org/3/library/importlib.html), which enables dynamic imports from modules.


#### Examples:

```py
>>> resolver.type_lookup(module_name=None, type_name="int")
<class 'int'>

>>> resolver.type_lookup(module_name="pathlib", type_name="Path")
<class 'pathlib.Path'>

>>> resolver.type_lookup(module_name="fractions", type_name="Fraction")
<class 'fractions.Fraction'>

>>> class Outer:
...     class Inner:
...         class EvenMoreInner:
...             ...

>>> resolver.type_lookup(
...    module_name="__main__", 
...    type_name="Outer.Inner.EvenMoreInner")
<class '__main__.Outer.Inner.EvenMoreInner'>
```

(The final example doesn't work in the REPL, because the repl cannot be passed as a project path, but tests show that it works in practice)