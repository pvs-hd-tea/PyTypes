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

Copy a local folder for `pytest` into a new one called `pytest-typed`, and apply decorators.
```
λ poetry run python main.py fetch \
    --url pytest \
    --output pytest-typed
```

Clone the `thefuck` project into a local folder called `thefuck`, and apply decorators.
```
λ python run python main.py fetch \
    --url "git@github.com:nvbn/thefuck.git" \
    --output thefuck
    --eval
```    


As shown above on the command line interface, the project accepts links to Git repositories, .zip archives and paths to local directories.
Regardless of whatever resource is given, it is written to the specified output directory.
Thereafter, test directories are searched for inside the project for so that the [decorators for tracing](tracing.md#decoratorstrace---minimally-intrusive-tracing-api) can be applied to testing callables.
Currently, only pytest suites are supported

Further resource formats can be supported by implementing the `Repository` class in `fetching.repo` and updating the `factory` method.

If more testing suites should be supported, a subclass of `TestDetector` has to be created, and methods should be implemented, which means most likely that a corresponding subclass of `ApplicationStrategy` needs to be implemented. These classes are in `fetching.detector` and `fetching.strat` respectively.

