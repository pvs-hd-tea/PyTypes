import click

import fetching
import tracing

if __name__ == "__main__":
    # Ordered by workflow usage
    main = click.Group(commands=[fetching.main])
    main()