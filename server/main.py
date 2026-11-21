from datetime import datetime
import re

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

ISBN_REGEX = r"(?:[0-9]{10}|[0-9]{13})"


class Book(BaseModel):
    title: str
    author: str
    publish_date: str
    isbn: str


class CachedBookResponse(BaseModel):
    cached: bool
    data: Book


class BulkBookError(BaseModel):
    isbn: str
    status_code: int
    detail: str


book_cache: dict[str, Book] = {}


def validate_isbn(isbn: str) -> bool:
    return re.fullmatch(ISBN_REGEX, isbn) is not None


def parse_date(date_str: str, *, validate_range: bool = False) -> str:
    date_formats = ("%Y-%m-%d", "%Y-%m", "%Y", "%B %d, %Y", "%b %d, %Y")

    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(date_str.strip(), date_format)
        except ValueError:
            continue

        if validate_range and not 1800 <= parsed_date.year <= datetime.now().year:
            raise HTTPException(
                status_code=400,
                detail="Publication year must be between 1800 and the current year",
            )

        return parsed_date.strftime("%Y-%m-%d")

    if validate_range:
        raise HTTPException(status_code=400, detail="Invalid publication date")

    return date_str


@app.get("/book/{isbn}", response_model=CachedBookResponse)
def get_book_by_isbn(isbn: str):
    if not validate_isbn(isbn):
        raise HTTPException(
            status_code=400,
            detail="Invalid ISBN format (must be 10 or 13 digits)",
        )

    cached_book = book_cache.get(isbn)
    if cached_book is not None:
        return CachedBookResponse(cached=True, data=cached_book)

    book_key = f"ISBN:{isbn}"

    try:
        response = requests.get(
            "https://openlibrary.org/api/books",
            params={"bibkeys": book_key, "format": "json", "jscmd": "data"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise HTTPException(
            status_code=500, detail="Error fetching book data"
        ) from error

    if book_key not in data:
        raise HTTPException(status_code=404, detail="Book not found")

    book_data = data[book_key]
    authors = book_data.get("authors") or []

    book = Book(
        title=book_data.get("title", "Unknown"),
        author=authors[0].get("name", "Unknown") if authors else "Unknown",
        publish_date=parse_date(
            book_data.get("publish_date") or "Unknown",
            validate_range=True,
        ),
        isbn=isbn,
    )
    book_cache[isbn] = book

    return CachedBookResponse(cached=False, data=book)


@app.get("/books/search", response_model=list[Book])
def search_books(title: str):
    try:
        response = requests.get(
            "https://openlibrary.org/search.json",
            params={
                "title": title,
                "limit": 5,
                "fields": "title,author_name,first_publish_year,isbn",
            },
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("docs", [])
    except requests.RequestException as error:
        raise HTTPException(
            status_code=500, detail="Error searching for books"
        ) from error

    books = []
    for result in results[:5]:
        authors = result.get("author_name") or []
        isbns = result.get("isbn") or []
        year = result.get("first_publish_year")

        books.append(
            Book(
                title=result.get("title") or "Unknown",
                author=authors[0] if authors else "Unknown",
                publish_date=parse_date(str(year)) if year else "Unknown",
                isbn=isbns[0] if isbns else "Unknown",
            )
        )

    return books


@app.post("/books/bulk", response_model=list[Book | BulkBookError])
def get_books_bulk(isbns: list[str]):
    results: list[Book | BulkBookError] = []

    for isbn in isbns:
        try:
            results.append(get_book_by_isbn(isbn).data)
        except HTTPException as error:
            results.append(
                BulkBookError(
                    isbn=isbn,
                    status_code=error.status_code,
                    detail=error.detail,
                )
            )

    return results