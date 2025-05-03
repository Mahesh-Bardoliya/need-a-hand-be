import typer

from ..database import create_tables
from ..main import engine

cli_app = typer.Typer()


@cli_app.command()
def main():
    create_tables(engine)


if __name__ == "__main__":
    cli_app()
