from datetime import datetime
import re

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class Book(BaseModel):
    title: str
    author: str
    publish_date: str
    isbn: str

ISBN_REGEX = r"(?:[0-9]{10}|[0-9]{13})"


def validate_isbn(isbn: str) -> bool:
    return re.fullmatch(ISBN_REGEX, isbn) is not None


def parse_date(date_str: str) -> str:
    for date_format in ("%Y-%m-%d", "%Y-%m", "%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(date_str, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return date_str
@app.get("/book/{isbn}", response_model=Book)
def get_book_by_isbn(isbn: str):
    if not validate_isbn(isbn):
        raise HTTPException(
            status_code=400,
            detail="Invalid ISBN format (must be 10 or 13 digits)",
        )

    book_key = f"ISBN:{isbn}"

    try:
        response = requests.get(
            "https://openlibrary.org/api/books",
            params={"bibkeys": book_key, "format": "json", "jscmd": "data"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException:
        raise HTTPException(status_code=500, detail="Error fetching book data")

    if book_key not in data:
        raise HTTPException(status_code=404, detail="Book not found")

    book_data = data[book_key]
    authors = book_data.get("authors") or []

    return Book(
        title=book_data.get("title", "Unknown"),
        author=authors[0].get("name", "Unknown") if authors else "Unknown",
        publish_date=parse_date(book_data.get("publish_date") or "Unknown"),
        isbn=isbn,
    )