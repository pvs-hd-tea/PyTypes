import click

import fetching
from tracing import TracerDecoratorAppender

if __name__ == "__main__":
    # Ordered by workflow usage
    TracerDecoratorAppender().append_decorator_on_all_files_in(None)
    main = click.Group(commands=[fetching.main])
    main()
