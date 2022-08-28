## Functionality

The tracing module contains classes that facilitate the tracing process behind a user-friendly API.
Note that it does not offer a command for performing the tracing procedure, which should instead be done by executing the [decorated tests of the project](fetching.md).
The testing process can be highly customised on a per-project basis, and as such represents a high-effort low-reward coding investment on this project's end.

## Foundations & Principles

### [sys.settrace](https://docs.python.org/3/library/sys.html#sys.settrace)

`sys.settrace` is a Python function that allows a callable to be set that is invoked on every line of Python code that comes after it.
This registered callable, henceforth refered to as the trace function is expected to have three arguments:
 
- `frame`: a representation of the current stack frame, containing references to further execution-related objects, such as:
    - the previous frame
    - visible globals 
    - variables that have been placed on the stack
    - [and more](https://docs.python.org/3/library/inspect.html)

- `event`: a string indicating the manner in which the current line of Python is handled. Relevant for us are:
    - call: a callable was entered
    - line: plain line of code that is about to be executed (NOTE: this means the line will executed in the next interpreter step, not when it is encountered by the `trace` function)
    - return: a callable is about to return

- `arg`: a value that differs depending on the given event. Relevant for us are:
    - call: `arg` is None. Retrieving the values of arguments is to be performed separately.
    - line: `arg` is None. Retrieving the values of variables on this line is also to be performed separately.
    - return: `arg` is the value that will be returned from the callable.

### Effect on Coverage, Debugging and other trace-related Tooling

While this approach is very powerful, it comes at a detriment to the development process.
[pdb](https://docs.python.org/3/library/pdb.html), which is the Python debugger, uses the `sys.settrace` API to provide information during debugging sesesions.
Similarly, the [coverage](https://coverage.readthedocs.io/en/6.4.4/) tool, which provides code-coverage information of Python programs, also uses this entrypoint.

`sys.settrace` only allows for one trace function to be set, meaning no tooling that also uses this API can coexist with another.
Therefore, along a codepath that uses the entrypoint in question, determining code coverage, or attempting to debug, is simply not possible.



## API

The project implements the required functionalities in the `tracing` module, in the classes of `Tracer` and `TraceBatchUpdate`, which trace and collect instances into a `DataFrame` by the following schema:


| Column       | Meaning                                                    | Type              | Null?                          |
|--------------|------------------------------------------------------------|-------------------|--------------------------------|
| Filename     | Relative path to file of traced instance from project root | string            | Never                          |
| ClassModule  | Module of class traced instance is in                      | string            | When not in a class' scope     |
| Class        | Name of class traced instance is in                        | string            | When not in a class' scope     |
| FunctionName | Name of function traced instance is in                     | string            | When not in a function's scope |
| LineNo       | Line number traced instance occurs on                      | uint              | Never                          |
| Category     | Number identifying context traced instance appears in      | int               | Never                          |
| VarName      | Name of traced instance                                    | string            | Never                          |
| TypeModule   | Module of traced instance's type                           | string            | When the type is builtin       |
| Type         | Name of traced instance's type                             | string            | Never                          |


Category can take on 5 different values, which are contained in the `TraceDataCategory` enum class: `LOCAL_VARIABLE`, `GLOBAL_VARIABLE`, `CLASS_MEMBER`, `FUNCTION_PARAMETER` and `FUNCTION_RETURN`.


### `@decorators.trace` - Minimally Intrusive Tracing API

[The fetching process](fetching.md) generates instances of this decorator function where applicable.
Each invocation parses the [config file](../misc/config.md) from the root of the project, and executes the tracing process on the marked callable.
This decorator takes care to forward all arguments that `pytest` may inject into the decorated function so that all kinds of [monkeypatching](https://docs.pytest.org/en/latest/how-to/monkeypatch.html), [fixtures](https://docs.pytest.org/en/latest/how-to/fixtures.html) and much else.

After tracing has concluded, the accumulated `DataFrame` in the `Tracer` is serialised under `pytypes/{project}/{test_case}/{func_name}-{hash(df)}.pytype`.
The hashing is performed to force tests that are executed in loops (e.g. by `@pytest.mark.parametrize`) to not overwrite their predecessor's data, which could cause valuable information that would indicate union types, to be lost.
If the traced test causes an uncaught exception, then a similarly named file with an `.err` suffix is generated containing the traceback.

Additionally, if the `benchmark_performance` value has been set to true in `pytypes.toml`, then additional tracing will be performed that does not store any trace data, and again with logging enabled but with optimisations turned off.
The runtimes for each execution are serialised next to the logged trace files.


### Tracer - Setting `sys.settrace` and Collecting Data

The events generated by the trace function are caught in the `Tracer` class' `_on_trace_is_called` method after its `start_trace` method has been called.
This ends when its `end_trace` method being called.
This functionality has again been wrapped in its `active_trace` method, which can be used in Python's `with` statements.
These methods are called from the `@decorators.trace` function, as documented in the [previous section](#decoratorstrace---minimally-intrusive-tracing-api).

The implementation backs-up any previously set trace function by reading from `sys.gettrace`, and sets its own using `sys.settrace`.
This newly set trace function handles the `call`, `line` and `return` events, and ignores the `exception` and `opcode` events, as no relevant data can be gleamed from these.
Each event is handled in its own appropriately named method, and the tracer combines the `DataFrame`s generated by `BatchTraceUpdate`.
When tracing is halted, the `DataFrame` is deduplicated to remove redundant information and the old trace function is restored.

During tracing, the values for `TypeModule` and `Type` are derived from the `type` function, which is passed to the [Resolver](../misc/resolver.md) to mirror components to Python's `from x.y import z` import style.


### BatchTraceUpdate - Simplifying and Batching Trace Updates

Despite the events emitted by `sys.settrace` being disjunct, the operations that must be performed on the basis thereof are not.
For example, the handling of the `return` event is a superset of that of the `line` event. 
Furthermore, the `line` event must perform update operations for both local and global variables.
Also, the general functionality necessary to update the `DataFrame` is repetitive, especially with `FileName`, `ClassModule`, `Class` and `FunctionName` being identical for every trace call within the same function.

The `BatchTraceUpdate` class was designed to solve these issues; the aforementioned repetitive data is passed to the constructor, to be reused in its methods.
These methods form a builder-pattern style interface for each relevant category, allowing updates to be chained as each event requires.
After all updates have been handled, a `DataFrame` can be produced that is to added to the otherwise accumulated trace data.