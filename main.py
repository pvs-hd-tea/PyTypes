import click

import fetching
import typegen
import confgen

if __name__ == "__main__":
    # Ordered by workflow usage
    main = click.Group(commands=[fetching.main, typegen.main, confgen.main])
    main()
