## Functionality

The fetching module contains classes that facilitate the process of taking a repository and applying decorators for the functions that need tracing behind a user-friendly API.
It also offers a command to execute this part of the workflow:

```
λ poetry run python main.py fetch --help
Usage: main.py fetch [OPTIONS]

  download repositories and apply tracing decorators

Options:
  -u, --url TEXT              URL to a repository  [required]
  -o, --output PATH           Download output path  [required]
  -f, --format [Git|Archive|Local]  
                              Indicate repository format explicitly
  -n, --no-traverse           Do not go down the directory tree of the tests,
                              instead stay in the first level
  -e, --eval                  Instead of generating one copy, generate two
                              copies: The original & the repository for
                              tracing
  -v, --verbose               INFO if not given, else CRITICAL
  --help                      Show this message and exit.
```

Example usage:

```
λ poetry run python main.py fetch \
    --url pytest \
    --output pytest-typed
```

```
λ python run python main.py fetch \
    --url "git@github.com:nvbn/thefuck.git" \
    --output thefuck
    --eval
```    


# Foundations & Principles



* Modify given codebase by detecting test folders and applying decorator for tracing to test functions


## Supported Formats

* Git repository
* Local folder
* Archives


## Decorator Application

[This is further documented here](fetching.md#decorator-application).

