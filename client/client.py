import json
from typing import Optional

import requests
import typer

app = typer.Typer()
BASE_URL = "http://127.0.0.1:8000"


@app.callback()
def main():
    """Look up books through the FastAPI server."""


@app.command("get-book")
def get_book(
    isbn: str,
    min_year: Optional[int] = typer.Option(
        None,
        "--min-year",
        help="Only show books published in this year or later.",
    ),
):
    """Fetch book details by ISBN."""
    try:
        response = requests.get(f"{BASE_URL}/book/{isbn}", timeout=15)
    except requests.RequestException as error:
        typer.echo(f"Could not connect to the server: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Status Code: {response.status_code}")

    try:
        payload = response.json()
    except ValueError:
        typer.echo(response.text)
        raise typer.Exit(code=1)

    if response.ok and min_year is not None:
        publish_year = int(payload["data"]["publish_date"][:4])
        if publish_year < min_year:
            typer.echo(f"Book was published in {publish_year}, before {min_year}.")
            return

    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))

    if not response.ok:
        raise typer.Exit(code=1)


@app.command("search-title")
def search_title(title: str):
    """Search for books by title."""
    try:
        response = requests.get(
            f"{BASE_URL}/books/search",
            params={"title": title},
            timeout=15,
        )
    except requests.RequestException as error:
        typer.echo(f"Could not connect to the server: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Status Code: {response.status_code}")
    try:
        typer.echo(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except ValueError:
        typer.echo(response.text)

    if not response.ok:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()