# trelctl

A Python CLI tool for managing Trello boards via the Trello REST API.

Trello REST API docs: [Atlassian Trello REST API](https://developer.atlassian.com/cloud/trello/rest/)

## Sub commands

### create board

Create a new Trello board with a specified name.

### import lists

Parse a CSV file and create lists in a specified board. Each CSV row becomes one list.

### import cards

Parse a CSV file and create cards in a specified board and list. Each CSV row becomes one card.

### get lists

Get all lists from a board in CSV format.

API reference: [get lists](https://developer.atlassian.com/cloud/trello/rest/api-group-boards/#api-boards-id-lists-get)

### get cards

Get all cards from a board (optionally filtered by list) in CSV format.

API reference: [get cards](https://developer.atlassian.com/cloud/trello/rest/api-group-boards/#api-boards-id-cards-get)

### get members

Get all members of a board in CSV format.

API reference: [get members](https://developer.atlassian.com/cloud/trello/rest/api-group-boards/#api-boards-id-members-get)

## Tech Stack

- Language: Python 3.14+
- Package management: `uv` (run `uv sync` to install dependencies)
- `typer` for CLI argument parsing
- `httpx` for HTTP API calls (no external frameworks)
- `csv` stdlib for CSV parsing
- Type hints on all functions; dataclasses for data structures

## Project Structure

```
trelctl/
├── pyproject.toml
├── trelctl/
│   ├── __init__.py
│   ├── main.py                  # Entry point, CLI app setup
│   ├── commands/
│   │   ├── create_board.py      # `create board` subcommand
│   │   ├── import_lists.py      # `import lists` subcommand
│   │   ├── import_cards.py      # `import cards` subcommand
│   │   ├── get_lists.py         # `get lists` subcommand
│   │   ├── get_members.py       # `get members` subcommand
│   │   └── get_cards.py         # `get cards` subcommand
│   ├── trello/
│   │   ├── __init__.py
│   │   ├── client.py            # HTTP client, auth, base request helpers
│   │   ├── boards.py            # Board lookup and creation
│   │   ├── lists.py             # List lookup and creation
│   │   ├── cards.py             # Card creation and retrieval
│   │   └── labels.py            # Label lookup
│   └── parser.py                # CSV parsing and row mapping
├── tests/
│   ├── test_parser.py
│   └── test_labels.py
├── .env.example
├── Makefile
└── README.md
```

## CLI Interface

```
trelctl create board <name>
trelctl import lists --board <name-or-id> <file.csv>
trelctl import cards --board <name-or-id> --list <name-or-id> <file.csv>
trelctl get lists --board <name-or-id>
trelctl get cards --board <name-or-id> [--list <name-or-id>]
trelctl get members --board <name-or-id>
```

Common flags:
- `--board` - Board name or ID to target
- `--dry-run` (import commands only) - Validate the CSV and resolve board/list/labels via the API, but do not write any data

Examples:

```
trelctl create board "My Board"
trelctl import lists --board "My Board" lists.csv
trelctl import cards --board "My Board" --list "Backlog" cards.csv
trelctl get lists --board "My Board"
trelctl get cards --board "My Board" --list "Backlog"
trelctl get members --board "My Board"
```

## Authentication

Read from environment variables only. Validate both are set before making any API calls.

| Variable        | Description             |
|-----------------|-------------------------|
| TRELLO_API_KEY  | Trello Power-Up API key |
| TRELLO_TOKEN    | User OAuth token        |

Fail with a clear error message if either is missing.

## CSV Formats

### lists

| Column | Required | Format     | Example   |
|--------|----------|------------|-----------|
| `name` | Yes      | Plain text | `Backlog` |

Rows with an empty `name` are skipped with a warning to stderr.

### cards

Fixed column headers (case-sensitive). Column order does not matter. `name` is required; all others are optional.

| Column        | Required | Format                            | Example                          |
|---------------|----------|-----------------------------------|----------------------------------|
| `name`        | Yes      | Plain text                        | `Fix login bug`                  |
| `description` | No       | Plain text                        | `Steps to reproduce...`          |
| `labels`      | No       | Pipe-separated label names        | `Bug\|High Priority`             |
| `due_date`    | No       | `YYYY-MM-DD`                      | `2026-04-15`                     |
| `checklist`   | No       | Pipe-separated items              | `Write tests\|Review PR\|Deploy` |
| `members`     | No       | Pipe-separated Trello member IDs  | `abc123def456\|ghi789jkl0`       |

`members` values must be Trello alphanumeric member IDs, not usernames or email addresses.

### members

| Column | Required | Format     | Example        |
|--------|----------|------------|----------------|
| `name` | Yes      | Plain text | `abc123def456` |

## Trello API Integration

Base URL: `https://api.trello.com/1`

Authentication: append `?key={TRELLO_API_KEY}&token={TRELLO_TOKEN}` to all requests.

### Board resolution (all commands that take `--board`)

`GET /members/me/boards` - find board by name (case-insensitive) or treat value as ID directly.

If `--board` does not match any name and is not a valid-looking ID, exit with an error.

### create board

`POST /boards` with `name=<name>`.

Print `Created board: "<name>" (id: <boardId>)` on success.

### import lists

Resolution before processing rows:

1. Resolve board (see above)

Per-row list creation: `POST /boards/{boardId}/lists` with `name=<name>`.

Print `Created list: "<name>" (id: <listId>)` per row.

### import cards

Resolution before processing rows:

1. Resolve board (see above)
2. `GET /boards/{boardId}/lists` - find list by name (case-insensitive) or treat value as ID directly
3. `GET /boards/{boardId}/labels` - fetch all labels to resolve names to IDs

If `--list` does not match any name and is not a valid-looking ID, exit with an error.

Per-row card creation:

1. `POST /cards` with fields:
   - `name`
   - `desc` (optional)
   - `idList` (resolved list ID)
   - `idLabels` (comma-separated resolved label IDs, optional)
   - `due` (RFC3339 datetime from `due_date`, optional)
   - `idMembers` (comma-separated member IDs from `members` column, optional)

2. If `checklist` column is non-empty:
   - `POST /cards/{cardId}/checklists` with `name=Checklist`
   - For each pipe-separated item: `POST /checklists/{checklistId}/checkItems` with `name=<item>`

Label handling:
- Match label names to existing board labels (case-insensitive)
- If a label name does not exist on the board, print a warning to stderr and skip that label (do not create new labels)

Print `Created card: "<name>" (id: <cardId>)` per row.

### get lists

1. Resolve board (see above)
2. `GET /boards/{boardId}/lists` - fetch all lists
3. Write CSV with columns: `name`

### get cards

1. Resolve board (see above)
2. If `--list` provided, resolve list and fetch `GET /lists/{listId}/cards`; otherwise `GET /boards/{boardId}/cards`
3. For each card with checklists, fetch `GET /cards/{cardId}/checklists` to populate the `checklist` column
4. Write CSV with the same columns as the import cards format: `name`, `description`, `labels`, `due_date`, `checklist`, `members`

Get cards CSV uses the same column format as import so files can be round-tripped.

### get members

1. Resolve board (see above)
2. `GET /boards/{boardId}/members` - fetch all members
3. Write CSV with columns: `name`

### Error handling

- Stop on the first API error. Print the command context, HTTP status, and response body to stderr, then exit non-zero
- Do not retry

## Output

- Import commands: print one line per created resource, then `Done. Created N <resource>(s).`
- Get commands: write to stdout in csv format. Users can pipe the output to a file.
- Warnings and errors go to stderr

## Makefile

Targets: `build`, `test`, `lint`, `run`.

- `build`: `uv build`
- `test`: `uv run pytest`
- `lint`: `uv run ruff check .` and `uvx ty check`
- `run`: `uv run trelctl`

## Gotchas

- **Rate limits**: Trello enforces 100 API requests per 10 seconds per token. Cards with checklists require 2+ extra calls each (one for the checklist, one per item). Do not implement throttling unless asked.
- **Checklist API order**: Create the checklist on the card first (`POST /cards/{id}/checklists`), then add items to it (`POST /checklists/{id}/checkItems`) — two separate calls per card with a checklist.

## Testing

- Unit tests for CSV parser: valid rows, missing name, bad date format, pipe-separated checklist/members parsing
- Unit tests for label resolution logic
- Unit tests for get CSV formatting (round-trip: get columns match import columns)
- Mock `httpx` calls using `pytest-mock` or `respx`; do not make real API calls in tests
- Tests in `tests/`: `tests/test_parser.py`, `tests/test_labels.py` etc.
