## Functionality
The typegen module contains classes & functions to unify trace data and generate files with type hints. 
It also offers a command to execute the typegen workflow.

```
λ poetry run python main.py typegen --help
Usage: main.py typegen [OPTIONS]

  Generate type hinted files using trace data

Options:
  -p, --path PATH                 Path to project directory  [required]
  -u, --unifiers TEXT             Unifier to apply, as given by `name` in
                                  pytypes.toml under [[unifier]]
  -g, --gen-strat [stub|inline|eval_inline]
                                  Select a strategy for generating type hints
                                  [required]
  -v, --verbose                   INFO if not given, else DEBUG
  --help                          Show this message and exit.
```

Example usage: 

```
λ poetry run python main.py typegen \
    -p project_path -g eval_inline \
    -u mt -u dupl -u mult2 -u dupl -u first
```

## Foundations & Principles

The project's approach to annotating is CST-based (Concrete-Syntax-Tree) transformation.
A CST differs from an AST in that it keeps all formatting details, including comments, whitespace and parantheses, and is therefore a fitting choice for the project, as only minimals modifications to a repository's code should occur, i.e. annotations and decorators for tracing.

In regards thereto, Python's AST module is a poor choice, as it only contains elements that are necessary for code execution, i.e. it drops extraneous newlines, changes all quote signs to single quotes, and perhaps worst of all, it removes all single-line comments.

The project offers both inline and stub-based annotation generation, whose mechanics, both shared and individual, have been split into CST transformers.
By reading in files that have been traced, trace data can be segmented on a per-file basis.
From this per-file basis trace data, annotations (also called type hints) can be generated for each file using the aforementioned transformers, and output appropriately.

### Unification

The trace data must be cleaned and appropriately unified to remove redundant data so that at most one type hint can be associated with each traced instance. 
To this extent, [unifiers](#unifiers) with a common interface have been implemented to cover unification needs.
The unifiers are applied to the trace data in the order specified on the command line; the value given to each `-u` flag references a unifier by the `name` key given in the [config file](../misc/config.md#example).

The examples in the following section will contain ["Category", "FunctionName", "VarName", "TypeModule" and "Type"](tracing.md#api) at a minimum for brevity's sake.

## Unifiers

Every unifier performs a different operation upon the trace data.
These can largely be segmented into two categories, namely 'filtering' and 'reducing'.
The former removes occurrences of trace data that are undesirable, and the latter groups rows and make replacements where appropriate.

Each unifier implements the `TraceDataFilter` class from `typegen.unification.filter_base`, which can simply be derived from to implement the desired behaviour.
It is automatically registered in the factory, i.e. no further updates are required.

If a user should be able to reference this new unifier from the command line, then `common.ptconfig` must also be updated with a matching entry to create the unifier from.


### Filtering Unifiers


#### Drop Duplicates

While the [tracer implementation](tracing.md#tracer---setting-syssettrace-and-collecting-data) may deduplicate trace data after halting, when the trace data is loaded into memory, every test that shares a call-path usually holds the same information, which is redundant, and can therefore be removed.

Example:

Configuration File: 

```toml
[[unifier]]
name = "remove_dups"
kind = "dedup"
```

Trace Data: 

| FunctionName  | VarName        | TypeModule | Type |
|---------------|----------------|------------|------|
| test_function | local_variable | NA         | str  |
| function      | parameter      | NA         | int  |
| function      | parameter      | NA         | int  |

After applying the filter:

| FunctionName  | VarName        | TypeModule | Type |
|---------------|----------------|------------|------|
| test_function | local_variable | NA         | str  |
| function      | parameter      | NA         | int  |


#### Drop Test Functions

The project always applies its [decorators to test functions and methods](fetching.md#decorators.trace), which leads to trace information about the test also being stored, and possibly generated during the [annotation process](#type-hint-generators).
If the user does not want to retain this information, then this filter should be applied, which simply drops all rows that reference testing callables.

Example:

Configuration File: 

```toml
[[unifier]]
name = "ignore_test"
kind = "drop_test"
test_name_pat = "test_"
```

Trace Data:

| Category | FunctionName  | VarName        | TypeModule | Type |
|----------|---------------|----------------|------------|------|
| 1        | test_function | local_variable | NA         | str  |
| 2        | function      | parameter      | NA         | int  |
| 2        | function      | parameter      | NA         | int  |

After applying the filter:

| Category | FunctionName  | VarName        | TypeModule | Type |
|----------|---------------|----------------|------------|------|
| 2        | function      | parameter      | NA         | int  |
| 2        | function      | parameter      | NA         | int  |

#### Min-Threshold

Drop all rows whose types appear less often than the minimum threshold. 

This is a simple attempt to detect API misusage in tests; if a statistically significant amount of tests use a certain signature, and a very low amount of other tests use a different one, then this unifier will remove those rows.

Example:

Configuration File: 

```toml
[[unifier]]
name = "min_threshold"
kind = "drop_min_threshold"
min_threshold = 0.3
```

Trace Data:

| Category | VarName   | TypeModule | Type |
|----------|-----------|------------|------|
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | str  |

After applying the filter:

| Category | VarName   | TypeModule | Type |
|----------|-----------|------------|------|
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |
| 2        | parameter | NA         | int  |

#### Drop of multiple types 

Drops rows containing variables of multiple types. It can be used to drop variables which do not have any distinct type hint as they have too many different type hints.

Example:

Configuration File: 

```toml

[[unifier]]
name = "drop_explicit_3"
kind = "drop_mult_var"
min_amount_types_to_drop = 3
```

Trace Data:


| Category | VarName    | TypeModule | Type  |
|----------|------------|------------|-------|
| 2        | parameter  | NA         | int   |
| 2        | parameter  | NA         | str   |
| 2        | parameter  | NA         | bool  |
| 2        | parameter  | NA         | float |
| 2        | parameter2 | NA         | int   |
| 2        | parameter2 | NA         | int   |
| 2        | parameter2 | NA         | str   |

After applying the filter:

| Category | VarName    | TypeModule | Type  |
|----------|------------|------------|-------|
| 2        | parameter2 | NA         | int   |
| 2        | parameter2 | NA         | int   |
| 2        | parameter2 | NA         | str   |


#### Keep only first 

Keeps only the first row of each variable. It can be used to ensure that each variable in the trace data has only one type hint. Thus, it is often used as the last filter.

Example:

Configuration File: 

```toml
[[unifier]]
name = "keep_first"
kind = "keep_only_first"
```

Trace Data:


| Category | VarName    | TypeModule  | Type      |
|----------|------------|-------------|-----------|
| 2        | parameter  | NA          | int       |
| 2        | parameter  | NA          | str       |
| 2        | parameter2 | module_name | SubClass  |
| 2        | parameter2 | module_name | BaseClass |

After applying the filter:

| Category | VarName    | TypeModule  | Type      |
|----------|------------|-------------|-----------|
| 2        | parameter  | NA          | int       |
| 2        | parameter2 | module_name | SubClass  |



### Reducing Unifiers


#### Subtypes & Common Interfaces

Replaces rows containing types of the same variable in the data with their earliest common base type.
This unifier uses the [Resolver](../misc/resolver.md) implementation to load the [MRO](https://www.python.org/download/releases/2.3/mro/)s for such rows in order to find the said shared base type.
The instance can also be defined so that only type hints are replaced if the common base type is also in the trace data.
No replacement occurs for undesirable base types, such as `abc.ABC`, `abc.ABCMeta` and `object`.


```toml
[[unifier]]
name = "unify_subtypes_relaxed"
kind = "unify_subty"
only_unify_if_base_was_traced = false
```

Trace Data:

| Category | VarName    | TypeModule  | Type      |
|----------|------------|-------------|-----------|
| 2        | parameter2 | pathlib | WindowsPath  |
| 2        | parameter2 | pathlib | PosixPath |

(In this example, pathlib.WindowsPath and pathlib.PosixPath inherit from pathlib.Path)

After applying the filter:

| Category | VarName    | TypeModule  | Type      |
|----------|------------|-------------|-----------|
| 2        | parameter2  | pathlib          | Path       |

Configuration File:

```toml
[[unifier]]
name = "unify_subtypes_strict"
kind = "unify_subty"
only_unify_if_base_was_traced = true
```

Trace Data:

| Category | VarName    | TypeModule  | Type      |
|----------|------------|-------------|-----------|
| 2        | parameter  | NA          | int       |
| 2        | parameter  | NA          | str       |
| 2        | parameter2 | module_name | SubClass  |
| 2        | parameter2 | module_name | BaseClass |

(In this example, module_name.SubClass inherits from module_name.BaseClass)

After applying the filter:

| Category | VarName    | TypeModule  | Type      |
|----------|------------|-------------|-----------|
| 2        | parameter  | NA          | int       |
| 2        | parameter  | NA          | str       |
| 2        | parameter2 | module_name | BaseClass |


#### Unions

Replaces rows containing types of the same variable in the data with the union of these types.

Example:

Configuration File:

```toml
[[unifier]]
name = "unify"
kind = "union"
```

Trace Data:

| Category | VarName    | TypeModule  | Type      |
|----------|------------|-------------|-----------|
| 2        | parameter  | NA          | int       |
| 2        | parameter  | NA          | str       |
| 2        | parameter2 | module_name1 | SubClass  |
| 2        | parameter2 | module_name2 | BaseClass |

After applying the filter:

| Category | VarName    | TypeModule              | Type                 |
|----------|------------|-------------------------|----------------------|
| 2        | parameter  | NA,NA                   | int\|str             |
| 2        | parameter2 | module_name1,module_name2 | SubClass\|BaseClass  |


#### Transformers

To apply changes to the files / add type hints to the code, the code in the file is parsed into a CST. 
Modifying the CSTs is done by transformers which visit the nodes in the trees and modify these if necessary. 
The following transformers are used to achieve the functionality of the type hint generators:

* TypeHintTransformer - Updates aug-/assign, function definition & function parameter nodes by adding the traced type hints to the corresponding variables if that variable is in the trace data. If an already existing type hint exists, the node will not be changed. 
Used to add traced type hints to global, local variables and class members in assignments, to function parameters and function return in function definitions.

* RemoveAllTypeHintsTransformer - Removes type hints from annotated assign, function definition & function parameter nodes.
Used by the evaluation inline generator to remove existing type hints of global, local variables and class members in assignments, to function parameters and function return in function definitions.

* AddImportTransformer - Transforms the CST by adding Import-From nodes to import the modules of the type hints in the trace data. 
Used to update the code in the files so that the modules of the added type hints are imported.

* MyPyHintTransformer - Uses the given CST to generate the corresponding stub CST. This is done by saving the CST code in a temporary file, generating the corresponding stub file (also as a temporary file) using `mypy.stubgen` and parsing the stub file's contents into the stub CST.
Used by the stub file generator to generate the stub CST after adding the traced type hints to the CST.

* ImportUnionTransformer - Transforms the CST by adding the Import-From node to import `Union` from `typing` (`from typing import Union`) if the corresponding code contains a type hint which uses `Union`.
Used by the stub file generator to add the missing import in the stub CST as `mypy.stubgen` annotates with `Union`, but does not add the corresponding import.

These transformers all derive from `cst.CSTTransformer`; if a new transformer needs to be made, then deriving from this class is sufficient to reuse said transformer in an annotation generator.


### Type Hint Generators

After unifying the trace data, a type hint generator is used to generate files with. 
Which type hint generator is used is specified by the `--gen-strat` option.

Type Hint Generators are instances which generate the files with traced type hints for callables and variables using the filtered trace data. As the trace data contains the filenames,  The constraint of the trace data is that to each variable, only one type hint exists. 


* InlineGenerator - Overwrites the files by adding the traced type hints inline. Does not overwrite existing type hints. Uses the `TypeHintTransformer` followed by the `AddImportTransformer`.
* EvaluationInlineGenerator - Overwrites the files by adding the inline type hints, and removing annotations for instances that do not have any trace data. Used to [evaluate the traced type hints compared with the existing type hints](evaluating.md). Uses the `RemoveAllTypeHintsTransformer`, followed by the `TypeHintTransformer` and `AddImportTransformer`.
* StubFileGenerator - Generates `.pyi` stub files of the affected files with the traced type hints. Existing type hints are kept. Uses the `TypeHintTransformer` followed by the `AddImportTransformer`, `MyPyHintTransformer` and `ImportUnionTransformer`, in that order.