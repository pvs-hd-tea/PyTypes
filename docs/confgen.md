## Functionality

The confgen module contains a short script intended to help facililate creation of an initial [`pytypes.toml`](misc/config.md) that can later be extended as the user wishes.
It also offers a command to execute the typegen workflow.

```
λ poetry run python main.py confgen --help
Usage: main.py confgen [OPTIONS]

  generate pytypes.toml

Options:
  -p, --project PATH  Project path (also used as output path)  [required]
  --help              Show this message and exit.
```

Example usage: 

```
λ poetry run python main.py confgen -p pytest
```

will generate a config file in the referenced folder.
It will contain an absolute path to the the project specified on the command line, with `stdlib_path` and `venv_path` being automatically inferred on the basis of the Python executable used to run this script.
