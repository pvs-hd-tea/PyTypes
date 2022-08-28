## Principles

For this project's multi-stage workflow, some variables remain constant across multiple commands.
For example, the paths necessary to differentiate between standard project types, standard library types and types from third-party dependencies in the virtualenv are needed for both the tracing and unification processes.

All such variables are stored in a `pytypes.toml` file in the root of the prject to trace, which will be read in by the program without the user having to respecify them.

## Example

The following configuration is used for a project called `PyTypes`.
The project is located in `/home/name/repos/pytypes`, the used Python binary's standard library is located at `/usr/lib/python3.10`, and the virtual environment is located at `/home/name/.cache/pypoetry/venv/pytypes-xvtnrWJT`.
To read up on why these paths are necessary, read up on the [Resolver class](resolver.md) and how [types are stored into our trace data](../workflow/tracing.md#api).

Furthermore, customisable unifiers that are used during the annotation generation process are stored by a `name` and identified by the `kind` attribute.
To read up on how these unifiers come into play, read up on the [annotation generation process](../workflow/annotating.md).



```toml
[pytypes]
project = "PyTypes"

proj_path = "/home/name/repos/pytypes"
stdlib_path = "/usr/lib/python3.10"
venv_path = "/home/name/.cache/pypoetry/venv/pytypes-xvtnrWJT"

[[unifier]]
name = "remove_dups"
kind = "dedup"

[[unifier]]
name = "ignore_test"
kind = "drop_test"
test_name_pat = "test_"

[[unifier]]
name = "drop_implicit_2"
kind = "drop_mult_var"

[[unifier]]
name = "drop_explicit_5"
kind = "drop_mult_var"
min_amount_types_to_drop = 5

[[unifier]]
name = "unify_subtypes_relaxed"
kind = "unify_subty"

[[unifier]]
name = "min_threshold"
kind = "drop_min_threshold"
min_threshold = 0.3

[[unifier]]
name = "unify"
kind = "union"
```