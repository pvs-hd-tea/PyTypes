import click

import fetching
import typegen

if __name__ == "__main__":
    # Ordered by workflow usage
    main = click.Group(commands=[fetching.main, typegen.main])
    main()
