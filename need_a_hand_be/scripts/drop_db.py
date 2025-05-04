import typer

from ..database import drop_tables
from ..main import engine

cli_app = typer.Typer()


@cli_app.command()
def main():
    drop_tables(engine)


if __name__ == "__main__":
    cli_app()
