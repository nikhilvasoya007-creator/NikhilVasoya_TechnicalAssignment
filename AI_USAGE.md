# AI Usage Disclosure

## Tools used
- Muse (Nik) — Meta's personal AI assistant, used as a coding guide.

## Tasks AI helped with
- Explaining the assignment and planning the build order (Parts 1–14).
- Drafting Flask routes, SQL schema, HTML templates and JavaScript for
  orders, reports, CSV import and the REST API.
- Drafting the debugging exercise fix, the pytest tests, README and API docs.
- Debugging help: the pytest fixture error
  (`CMySQLCursor.execute() got an unexpected keyword argument 'multi'`),
  fixed by splitting the schema SQL on `;` and executing statement by statement.

## Example prompts used
1. "What is this assignment, guide me from zero to final completion and
   make sure submission is within the timeline."
2. "All 9 tests show ERROR in the fixture — what is the cause and how do I fix it?"
3. "Give me the remaining REST API endpoints POST /api/orders,
   GET /api/orders/{id}, confirm and cancel, with JSON errors."

## How the code was reviewed
- Every file was pasted and run by me in VS Code / MySQL Workbench.
- Each part was verified in the browser or terminal before moving on:
  login and dashboard, customers, products, orders (4500 / 450 / 4050
  example), confirm/cancel stock changes, reports, CSV import,
  `GET /api/products?q=Mouse`, and `python -m pytest tests/ -v`
  (16 tests passed).
- Corrections made during review: the pytest fixture `multi=True` fix
  above, and the CSV import fix (added missing `import csv` / `import io`).
- No code was submitted without running it first, and no real credentials
  were committed — `.env` is git-ignored and only `.env.example` is in the repo.
