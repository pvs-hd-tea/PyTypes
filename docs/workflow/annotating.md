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

The examples in the following section only contain ["Category", "VarName", "TypeModule" and "Type"](tracing.md#api) for brevity's sake.

## Unifiers

Every unifier performs a different operation upon the trace data.
These can largely be segmented into two categories, namely 'filtering' and 'reducing'.
The former removes occurrences of trace data that are undesirable, and the latter groups rows and make replacements where appropriate.


### Filtering Unifiers


#### Drop Duplicates

While the [tracer implementation](tracing.md#tracer---setting-syssettrace-and-collecting-data) may deduplicate trace data after halting, when the trace data is loaded into memory, every test that shares a call-path usually holds the same information, which is redundant, and can therefore be removed.


<details>
<summary>Example:</summary>
```py
print("Hello World")
```
</details>


#### Drop Test Functions

The project always applies its [decorators to test functions and methods](fetching.md#decorators.trace), which leads to trace information about the test also being stored, and possibly generated during the [annotation process](#type-hint-generators).
If the user does not want to retain this information, then this filter should be applied, which simply drops all rows that reference testing callables.

Example:



#### Min-Threshold

Drop all rows whose types appear less often than the minimum threshold. 

This is a simple attempt to detect API misusage in tests; if a statistically significant amount of tests use a certain signature, and a very low amount of other tests use a different one, then this unifier will remove those rows.

Example:


### Reducing Unifiers


#### Subtypes & Common Interfaces

Replaces rows containing types of the same variable in the data with their earliest common base type.
This unifier uses the [Resolver](../misc/resolver.md) implementation to load the [MRO](https://www.python.org/download/releases/2.3/mro/)s for such rows in order to find the said shared base type.
The instance can also be defined so that only type hints are replaced if the common base type is also in the trace data.
No replacement occurs for undesirable base types, such as `abc.ABC`, `abc.ABCMeta` and `object`.

Example:



#### Unions

Replaces rows containing types of the same variable in the data with the union of these types.

Example:


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


### Type Hint Generators

After unifying the trace data, a type hint generator is used to generate files with. 
Which type hint generator is used is specified by the `--gen-strat` option.

Type Hint Generators are instances which generate the files with traced type hints for callables and variables using the filtered trace data. As the trace data contains the filenames,  The constraint of the trace data is that to each variable, only one type hint exists. 


* InlineGenerator - Overwrites the files by adding the traced type hints inline. Does not overwrite existing type hints. Uses the `TypeHintTransformer` followed by the `AddImportTransformer`.
* EvaluationInlineGenerator - Overwrites the files by adding the inline type hints, and removing annotations for instances that do not have any trace data. Used to [evaluate the traced type hints compared with the existing type hints](evaluating.md). Uses the `RemoveAllTypeHintsTransformer`, followed by the `TypeHintTransformer` and `AddImportTransformer`.
* StubFileGenerator - Generates `.pyi` stub files of the affected files with the traced type hints. Existing type hints are kept. Uses the `TypeHintTransformer` followed by the `AddImportTransformer`, `MyPyHintTransformer` and `ImportUnionTransformer`, in that order.




### Developer Documentation



* Drop Test Functions - Drops all data about test functions. Used to remove data about test functions to prevent test functions to be annotated by the [type hint generator](#type-hint-generators).
* Drop of multiple types - Drops rows containing variables of multiple types.
* Min-Threshold - Drops all rows whose types appear less often than the minimum threshold.
* Keep only first - Keeps only the first row of each variable. Used to ensure that each variable in the trace data has only one type hint. Often used as the last filter.
* Unify subtypes - Replaces rows containing types of the same variable in the data with their common base type. Does not replace if the common base type is `ABC`, `ABCMeta` or `object`. 
Used to unify the traced type hints of the variables. The instance can also be defined so that only type hints are replaced if the common base type is also in the trace data.
* Union - Replaces rows containing types of the same variable in the data with the union of these types. Used to unify the traced type hints of the variables.
* Filter List - Applies the filters in this list on the trace data. Used to filter the trace data with multiple filters, one-by-one. This is possible due to the common base class