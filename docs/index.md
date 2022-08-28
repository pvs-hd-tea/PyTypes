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

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
