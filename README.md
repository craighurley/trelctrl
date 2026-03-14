# trelctl

A CLI tool for managing Trello boards via the Trello REST API.

## Installation

```bash
uv tool install trelctl
```

Or run directly without installing:

```bash
uvx trelctl
```

## Setup

### 1. Get your Trello credentials

- **API Key**: Go to [trello.com/power-ups/admin](https://trello.com/power-ups/admin), create a Power-Up, and copy the API key.
- **Token**: From the same page, generate a token with read/write access to your boards.

### 2. Set environment variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
TRELLO_API_KEY=your_trello_api_key_here
TRELLO_TOKEN=your_trello_oauth_token_here
```

Alternatively, export them in your shell:

```bash
export TRELLO_API_KEY=your_api_key
export TRELLO_TOKEN=your_token
```

## Commands

### create board

Create a new Trello board.

```bash
trelctl create board "My Board"
```

Output:

```
Created board: "My Board" (id: abc123)
```

### import lists

Create lists in a board from a CSV file.

```bash
trelctl import lists --board "My Board" lists.csv
trelctl import lists --board "My Board" --dry-run lists.csv
```

CSV format:

| Column | Required | Example   |
|--------|----------|-----------|
| `name` | Yes      | `Backlog` |

Example `lists.csv`:

```csv
name
Backlog
In Progress
Done
```

`--dry-run` validates the file and resolves the board without creating anything.

### import cards

Create cards in a board list from a CSV file.

```bash
trelctl import cards --board "My Board" --list "Backlog" cards.csv
trelctl import cards --board "My Board" --list "Backlog" --dry-run cards.csv
```

CSV format:

| Column        | Required | Format                      | Example                          |
|---------------|----------|-----------------------------|----------------------------------|
| `name`        | Yes      | Plain text                  | `Fix login bug`                  |
| `description` | No       | Plain text                  | `Steps to reproduce...`          |
| `labels`      | No       | Comma-separated label names | `Bug,High Priority`              |
| `due_date`    | No       | `YYYY-MM-DD`                | `2026-04-15`                     |
| `checklist`   | No       | Pipe-separated items        | `Write tests\|Review PR\|Deploy` |
| `members`     | No       | Pipe-separated member IDs   | `abc123def456\|ghi789jkl0`       |

- Labels must already exist on the board. Unknown label names are skipped with a warning.
- `members` values must be Trello member IDs (alphanumeric), not usernames or email addresses.
- Column order does not matter. `name` is the only required column.

Example `cards.csv`:

```csv
name,description,labels,due_date,checklist,members
Fix login bug,Reproduce on mobile,Bug,2026-04-15,Write test|Fix bug|Deploy,
Add dark mode,,Enhancement,,,,
```

`--dry-run` validates the file, resolves the board, list, and labels, but creates nothing.

### get lists

Export all lists from a board to CSV.

```bash
trelctl get lists --board "My Board"
trelctl get lists --board "My Board" > lists.csv
```

Output columns: `name`

### get cards

Export all cards from a board (or a specific list) to CSV.

```bash
trelctl get cards --board "My Board"
trelctl get cards --board "My Board" --list "Backlog"
trelctl get cards --board "My Board" > cards.csv
```

Output columns: `name`, `description`, `labels`, `due_date`, `checklist`, `members`

The output uses the same format as `import cards`, so exported files can be re-imported.

### get members

Export all members of a board to CSV.

```bash
trelctl get members --board "My Board"
trelctl get members --board "My Board" > members.csv
```

Output columns: `name` (Trello member IDs)

## Board and list resolution

All `--board` and `--list` options accept either a name or an ID:

- **Name**: matched case-insensitively against your boards/lists.
- **ID**: used directly if no name match is found.

If neither matches, the command exits with an error.

## Round-tripping

`get cards` output is compatible with `import cards` input, which allows you to export cards from one board and import them into another:

```bash
trelctl get cards --board "Source Board" > cards.csv
trelctl import cards --board "Target Board" --list "Backlog" cards.csv
```

## Development

```bash
make install     # install dependencies
make test        # run tests
make lint        # run linters
make build       # build package
```
