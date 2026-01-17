# Bitable Operations Guide

This guide covers how to work with Feishu Bitable (multidimensional tables) in feishu-doc-tools.

## Overview

Bitable is Feishu's multidimensional table product, similar to Airtable or Google Sheets. The feishu-doc-tools project now supports:

1. **Bitable API Operations** - Create tables, insert/update/delete records
2. **Markdown Table to Bitable** - Convert Markdown tables to Bitable automatically

## Bitable API Client

### Basic Usage

```python
from lib.feishu_api_client import FeishuApiClient, BitableFieldType

# Initialize client
client = FeishuApiClient.from_env()

# Create a new Bitable app
bitable = client.create_bitable("My Data")
print(f"Created: {bitable['url']}")

# Create a table with fields
fields = [
    {"field_name": "Name", "type": BitableFieldType.TEXT},
    {"field_name": "Age", "type": BitableFieldType.NUMBER},
    {
        "field_name": "Status",
        "type": BitableFieldType.SINGLE_SELECT,
        "options": {
            "options": [
                {"name": "To Do"},
                {"name": "In Progress"},
                {"name": "Done"},
            ]
        },
    },
]

table = client.create_table(bitable['app_id'], "Tasks", fields)
print(f"Table ID: {table['table_id']}")

# Insert records
records = [
    {"fields": {"Name": "Alice", "Age": 30, "Status": "In Progress"}},
    {"fields": {"Name": "Bob", "Age": 25, "Status": "To Do"}},
]

result = client.insert_records(bitable['app_id'], table['table_id'], records)
print(f"Inserted {result['total_records']} records")
```

### Field Types

Supported field types (from `BitableFieldType`):

| Type | Constant | Description |
|------|----------|-------------|
| Text | `BitableFieldType.TEXT` | Single-line text |
| Number | `BitableFieldType.NUMBER` | Numeric values |
| Single Select | `BitableFieldType.SINGLE_SELECT` | Dropdown with single selection |
| Multi Select | `BitableFieldType.MULTI_SELECT` | Dropdown with multiple selections |
| Date | `BitableFieldType.DATE` | Date without time |
| DateTime | `BitableFieldType.DATETIME` | Date with time |
| Person | `BitableFieldType.PERSON` | User/person selection |
| Checkbox | `BitableFieldType.CHECKBOX` | Boolean/checkbox |
| URL | `BitableFieldType.URL` | Hyperlink |
| Phone | `BitableFieldType.PHONE` | Phone number |
| Email | `BitableFieldType.EMAIL` | Email address |
| Progress | `BitableFieldType.PROGRESS` | Progress bar (0-100) |

### Reading Records

```python
# Get first page of records
page = client.get_table_records(app_id, table_id, page_size=100)

for record in page["records"]:
    print(record["fields"])

# Paginate through all records
all_records = []
while page:
    all_records.extend(page["records"])
    if page["has_more"]:
        page = client.get_table_records(
            app_id, table_id,
            page_size=100,
            page_token=page["page_token"]
        )
    else:
        break
```

### Updating Records

```python
# Update a single record
updated = client.update_record(
    app_id, table_id, record_id,
    {"Name": "Alice Updated", "Age": 31}
)
```

### Deleting Records

```python
# Delete a single record
result = client.delete_record(app_id, table_id, record_id)
assert result["success"]
```

## Markdown Table to Bitable

The `md_table_to_bitable.py` script converts Markdown tables to Bitable automatically.

### Command-Line Usage

```bash
# Basic usage - convert all tables in a Markdown file
uv run python scripts/md_table_to_bitable.py data.md

# Custom Bitable name
uv run python scripts/md_table_to_bitable.py data.md --name "Project Data"

# Create in specific folder
uv run python scripts/md_table_to_bitable.py data.md --folder fldcnxxxxx

# Auto-detect field types (default: enabled)
uv run python scripts/md_table_to_bitable.py data.md --auto-types

# Convert only specific table (0-based index)
uv run python scripts/md_table_to_bitable.py data.md --table-index 0

# Verbose logging
uv run python scripts/md_table_to_bitable.py data.md -v
```

### Input Format

Markdown tables in pipe syntax:

```markdown
| Name | Age | Status |
|------|-----|--------|
| Alice | 30 | In Progress |
| Bob | 25 | To Do |
| Charlie | 35 | Done |
```

### Field Type Detection

The converter automatically detects field types:

| Data Pattern | Detected Type |
|--------------|---------------|
| All numeric | `NUMBER` |
| Date patterns (YYYY-MM-DD, etc.) | `DATE` |
| Boolean (yes/no, true/false) | `CHECKBOX` |
| Few unique values (< 10, < 50% unique) | `SINGLE_SELECT` |
| Everything else | `TEXT` |

### Programmatic Usage

```python
from scripts.md_table_to_bitable import TableToBitableConverter
from lib.feishu_api_client import FeishuApiClient

# Initialize
client = FeishuApiClient.from_env()
converter = TableToBitableConverter(client)

# Read Markdown content
with open("data.md") as f:
    md_content = f.read()

# Extract tables
tables = converter.extract_tables(md_content)
print(f"Found {len(tables)} table(s)")

# Create Bitable
result = converter.create_bitable_from_tables(
    tables=tables,
    bitable_name="My Data",
    auto_types=True,  # Auto-detect field types
)

print(f"Created: {result['app_url']}")
for table_info in result['tables']:
    print(f"  Table: {table_info['table_name']}")
    print(f"    Records: {table_info['records_inserted']}")
```

## API Reference

### `create_bitable(name, folder_token=None)`

Create a new Bitable application.

**Parameters:**
- `name` (str): Application name
- `folder_token` (str, optional): Folder to create in

**Returns:**
```python
{
    "app_id": "bascnxxxxx",
    "name": "My Data",
    "url": "https://feishu.cn/base/bascnxxxxx"
}
```

### `create_table(app_id, table_name, fields)`

Create a new table in a Bitable app.

**Parameters:**
- `app_id` (str): Bitable application ID
- `table_name` (str): Table name
- `fields` (list): Field definitions

**Field Definition Format:**
```python
{
    "field_name": "Column Name",
    "type": BitableFieldType.TEXT,
    "options": {...}  # Optional field-specific options
}
```

**Returns:**
```python
{
    "table_id": "tblxxxxx",
    "table_name": "Table Name",
    "app_id": "bascnxxxxx",
    "fields": [...]
}
```

### `insert_records(app_id, table_id, records)`

Insert records into a table.

**Parameters:**
- `app_id` (str): Bitable application ID
- `table_id` (str): Table ID
- `records` (list): Records to insert

**Record Format:**
```python
{
    "fields": {
        "Column1": "Value1",
        "Column2": 123,
        ...
    }
}
```

**Returns:**
```python
{
    "record_ids": ["rec1", "rec2", ...],
    "total_records": 2,
    "records": [...]
}
```

### `get_table_records(app_id, table_id, page_size=100, page_token=None)`

Get records from a table.

**Parameters:**
- `app_id` (str): Bitable application ID
- `table_id` (str): Table ID
- `page_size` (int): Records per page (max 500)
- `page_token` (str, optional): Pagination token

**Returns:**
```python
{
    "records": [...],
    "has_more": True,
    "page_token": "next_token",
    "total_records": 100
}
```

### `update_record(app_id, table_id, record_id, fields)`

Update a single record.

**Parameters:**
- `app_id` (str): Bitable application ID
- `table_id` (str): Table ID
- `record_id` (str): Record ID to update
- `fields` (dict): Field values to update

**Returns:**
```python
{
    "record_id": "recxxxxx",
    "record": {...},
    "fields": {...}
}
```

### `delete_record(app_id, table_id, record_id)`

Delete a single record.

**Parameters:**
- `app_id` (str): Bitable application ID
- `table_id` (str): Table ID
- `record_id` (str): Record ID to delete

**Returns:**
```python
{
    "success": True,
    "record_id": "recxxxxx"
}
```

## Testing

### Run Bitable Tests

```bash
# Run all Bitable tests
pytest tests/test_feishu_api_extended.py::TestBitableOperations -v

# Run table converter tests
pytest tests/test_table_to_bitable.py -v
```

### Test Coverage

- **Bitable API Tests** (`test_feishu_api_extended.py`):
  - 15 test cases covering all Bitable operations
  - Success cases, error handling, edge cases

- **Table Converter Tests** (`test_table_to_bitable.py`):
  - Table extraction from Markdown
  - Field type inference
  - Value conversion
  - Error handling

## Examples

### Example 1: Convert README Tables

```bash
# Convert all tables in README.md to a Bitable
uv run python scripts/md_table_to_bitable.py README.md --name "README Tables"
```

### Example 2: Project Data

```python
from scripts.md_table_to_bitable import TableToBitableConverter
from lib.feishu_api_client import FeishuApiClient

# Suppose you have project-data.md with:
# | Task | Owner | Status | Priority |
# |------|-------|--------|----------|
# | Fix bug | Alice | In Progress | High |
# | Add feature | Bob | To Do | Medium |

client = FeishuApiClient.from_env()
converter = TableToBitableConverter(client)

with open("project-data.md") as f:
    tables = converter.extract_tables(f.read())

result = converter.create_bitable_from_tables(
    tables,
    bitable_name="Project Tracking",
    auto_types=True,
)

print(f"Created Bitable: {result['app_url']}")
```

### Example 3: Batch Import

```python
from lib.feishu_api_client import FeishuApiClient, BitableFieldType

client = FeishuApiClient.from_env()

# Create Bitable for contacts
bitable = client.create_bitable("Contacts")

# Create table with contact fields
fields = [
    {"field_name": "Name", "type": BitableFieldType.TEXT},
    {"field_name": "Email", "type": BitableFieldType.EMAIL},
    {"field_name": "Phone", "type": BitableFieldType.PHONE},
    {"field_name": "Active", "type": BitableFieldType.CHECKBOX},
]

table = client.create_table(bitable['app_id'], "People", fields)

# Batch insert contacts
contacts = [
    {"fields": {"Name": "Alice", "Email": "alice@example.com", "Active": True}},
    {"fields": {"Name": "Bob", "Email": "bob@example.com", "Active": False}},
]

result = client.insert_records(bitable['app_id'], table['table_id'], contacts)
print(f"Imported {result['total_records']} contacts")
```

## Troubleshooting

### Common Issues

1. **"Application not found" error**
   - Check that `app_id` is correct
   - Verify you have access to the Bitable

2. **"Field not found" error**
   - Ensure field names in records match field names in table schema
   - Field names are case-sensitive

3. **"Invalid field type" error**
   - Verify field type constants from `BitableFieldType`
   - Check that options match the field type

4. **Table conversion issues**
   - Ensure Markdown tables use proper pipe syntax
   - Check that tables have consistent column counts
   - Use `--verbose` flag to debug

### Debug Mode

```bash
# Enable verbose logging
uv run python scripts/md_table_to_bitable.py data.md -v

# Or set environment variable
export PYTHONUNBUFFERED=1
uv run python scripts/md_table_to_bitable.py data.md
```

## See Also

- [Feishu Bitable API Documentation](https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/field)
- [Performance Optimization Guide](PERFORMANCE_OPTIMIZATION.md)
- [Main README](../README.md)
