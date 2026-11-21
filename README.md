# Public API Lab

This project uses FastAPI to fetch book data from the Open Library API. A Typer command-line client lets users look up books by ISBN, search by title, and look up multiple ISBNs at once.

## Setup

Run these commands from the project root:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## Run the server

```bash
python -m uvicorn server.main:app --port 8000 --reload
```

## Run the client

Keep the server running. Open a second terminal in the project root and run:

```bash
source venv/bin/activate
python client/client.py get-book 9780142437247
python client/client.py search-title "Great Gatsby"
python client/client.py get-book 9780142437247 --min-year 2000
python client/client.py get-bulk 9780142437247 9781739460810
```

## Challenge features

- **Title search:** `GET /books/search` returns up to five matches.
- **Caching:** Repeating a successful ISBN lookup returns `"cached": true`.
- **Publication date validation:** The ISBN lookup checks that the publication year is between 1800 and the current year. The client supports filtering with `--min-year`.
- **Bulk ISBN lookup:** `POST /books/bulk` accepts a JSON list of ISBNs and returns book details or an error for each ISBN.

## Testing

Postman tests cover a successful lookup (`200`), an invalid ISBN (`400`), a missing book (`404`), title search, caching, and bulk lookup. The Typer client was also tested with publication-year filtering.

See `screenshots/Lab_Report.docx` for the test screenshots and implementation details.