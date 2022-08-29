# Welcome to PyTypes

```
λ poetry run python main.py --help
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  confgen   Generate pytypes.toml
  evaluate  Evaluate given original and traced repository
  fetch     Download repositories and apply tracing decorators
  typegen   Generate type hinted files using trace data
```

## Workflow

1. Fetching: [`poetry run python main.py fetch --help`](workflow/fetching.md)
2. Confgen: [`poetry run python main.py confgen --help`](workflow/fetching.md)
3. [Tracing](workflow/tracing.md)
4. Typegen: [`poetry run python main.py typegen --help`](workflow/annotating.md)
5. Evaluating: [`poetry run python main.py evaluate --help`](workflow/evaluating.md)


## Miscellaneous

* [Resolver](misc/resolver.md)
* [Config](misc/config.md)

## Project layout

```
├── common
│   ├── data_file_collector.py
│   ├── ptconfig.py
│   ├── resolver.py
│   └── trace_data_category.py
├── confgen
│   └── __init__.py
├── constants.py
├── docs
├── evaluation
│   ├── file_type_hints_collector.py
│   ├── ipynb_evaluation_template.py
│   ├── metric_data_calculator.py
│   ├── normalize_types.py
│   └── performance_data_file_collector.py
├── fetching
│   ├── detector.py
│   ├── projio.py
│   ├── repo.py
│   └── strat.py
├── LICENSE
├── main.py
├── mkdocs.yml
├── mypy.ini
├── poetry.lock
├── pyproject.toml
├── pytest.ini
├── pytypes.toml
├── README.md
├── test.log
├── tox.ini
├── tracing
│   ├── decorators.py
│   ├── optimisation
│   │   ├── base.py
│   │   ├── enums.py
│   │   ├── looping.py
│   │   └── utils.py
│   ├── tracer.py
│   └── trace_update.py
└── typegen
    ├── strats
    │   ├── eval_inline.py
    │   ├── gen.py
    │   ├── imports.py
    │   ├── inline.py
    │   └── stub.py
    ├── trace_data_file_collector.py
    └── unification
        ├── drop_dupes.py
        ├── drop_min_threshold.py
        ├── drop_test_func.py
        ├── drop_vars.py
        ├── filter_base.py
        ├── keep_only_first.py
        ├── subtyping.py
        └── union.py
```