# Product Importer

A web application for importing products from CSV files (up to 500,000 records) with real-time progress tracking, product management, and webhook configuration.

## Features

- **CSV Upload**: Upload large CSV files with real-time progress tracking via SSE
- **Product Management**: Full CRUD operations with filtering and pagination
- **Bulk Delete**: Delete all products with confirmation
- **Webhook Configuration**: Manage webhooks for product events
- **Async Processing**: Celery workers handle long-running imports (no timeout issues)

## Tech Stack

- **Backend**: Django 5, Django REST Framework
- **Async Tasks**: Celery with Redis
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Vanilla HTML/CSS/JavaScript

---

## CSV Import Assumptions

| Rule | Description |
|------|-------------|
| **Required columns** | `sku`, `name`, `description`, `price` |
| **SKU uniqueness** | Case-insensitive (SKU-001 = sku-001) |
| **Duplicate handling** | Last occurrence overwrites previous |
| **Invalid rows** | Skipped and logged (missing SKU) |
| **Default status** | Products default to `active = true` on import |
| **Price validation** | Invalid/negative prices are set to null |
| **Idempotent** | Re-importing same CSV is safe (upsert) |

### CSV Format

| Column | Required | Description |
|--------|----------|-------------|
| `sku` | **Yes** | Unique product identifier (case-insensitive) |
| `name` | No | Product name (defaults to SKU if empty) |
| `description` | No | Product description |
| `price` | No | Product price (numeric) |

### Example CSV

```csv
sku,name,description,price
SKU-001,Apple iPhone 14,Latest Apple smartphone,799.99
sku-002,Samsung Galaxy S23,Android flagship phone,749.50
Sku-003,Google Pixel 8,Pixel phone with AI features,699.00
```

> **Note**: SKU case varies intentionally - all will be normalized to lowercase.

---

## Test Data

The `data/` folder contains test CSV files for all scenarios:

| File | Purpose |
|------|---------|
| `test_small_10_products.csv` | Basic import test |
| `test_medium_1000_products.csv` | Medium scale test |
| `test_large_100k_products.csv` | Performance test (100K rows) |
| `test_duplicate_sku_overwrite.csv` | SKU case-insensitivity and overwrite |
| `test_invalid_rows.csv` | Error handling (missing SKU, invalid price) |
| `test_edge_cases.csv` | Unicode, special characters, whitespace |
| `test_realistic_mixed_500.csv` | Combined scenarios |

### Generate Test Data

```bash
cd data
python generate_test_data.py
```

---

## Local Development

### Option 1: Using Docker Compose

```bash
docker-compose up
```

### Option 2: Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate
```

3. Start Redis (required for Celery):
```bash
redis-server
```

4. Start Celery worker:
```bash
celery -A config worker --loglevel=info
```

5. Start Django server:
```bash
python manage.py runserver
```

6. Open http://localhost:8000

---

## API Endpoints

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products/` | List products (paginated, filterable) |
| POST | `/api/products/` | Create product |
| GET | `/api/products/{id}/` | Get product |
| PUT | `/api/products/{id}/` | Update product |
| DELETE | `/api/products/{id}/` | Delete product |
| DELETE | `/api/products/bulk_delete/` | Delete all products |
| POST | `/api/products/upload/` | Upload CSV file |
| GET | `/api/products/upload/{job_id}/status/` | Get upload progress (SSE) |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/webhooks/` | List webhooks |
| POST | `/api/webhooks/` | Create webhook |
| GET | `/api/webhooks/{id}/` | Get webhook |
| PUT | `/api/webhooks/{id}/` | Update webhook |
| DELETE | `/api/webhooks/{id}/` | Delete webhook |
| POST | `/api/webhooks/{id}/test/` | Test webhook |

---

## Deployment

### Railway / Render

1. Fork/push code to GitHub
2. Connect to Railway/Render
3. Add PostgreSQL and Redis services
4. Set environment variables

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | Debug mode (false in production) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Redis connection string |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts |

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│   Web Browser   │────▶│  Django (DRF)   │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
            ┌───────────┐ ┌───────────┐ ┌───────────┐
            │ PostgreSQL│ │   Redis   │ │  Celery   │
            │ (Database)│ │ (Broker)  │ │ (Worker)  │
            └───────────┘ └───────────┘ └───────────┘
```

---

## License

MIT
