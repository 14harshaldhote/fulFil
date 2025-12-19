# Product Importer

A web application for importing products from CSV files (up to 500,000 records) with real-time progress tracking, product management, and webhook configuration.

## Features

- **CSV Upload**: Upload large CSV files with real-time progress tracking via SSE
- **Product Management**: Full CRUD operations with filtering and pagination
- **Bulk Delete**: Delete all products with confirmation
- **Webhook Configuration**: Manage webhooks for product events

## Tech Stack

- **Backend**: Django 5, Django REST Framework
- **Async Tasks**: Celery with Redis
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Vanilla HTML/CSS/JavaScript

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

## CSV Format

| Column | Required | Description |
|--------|----------|-------------|
| sku | Yes | Unique product identifier (case-insensitive) |
| name | No | Product name (defaults to SKU) |
| description | No | Product description |

## API Endpoints

### Products
- `GET /api/products/` - List products (paginated, filterable)
- `POST /api/products/` - Create product
- `GET /api/products/{id}/` - Get product
- `PUT /api/products/{id}/` - Update product
- `DELETE /api/products/{id}/` - Delete product
- `DELETE /api/products/bulk_delete/` - Delete all products
- `POST /api/products/upload/` - Upload CSV file
- `GET /api/products/upload/{job_id}/status/` - Get upload progress (supports SSE)

### Webhooks
- `GET /api/webhooks/` - List webhooks
- `POST /api/webhooks/` - Create webhook
- `GET /api/webhooks/{id}/` - Get webhook
- `PUT /api/webhooks/{id}/` - Update webhook
- `DELETE /api/webhooks/{id}/` - Delete webhook
- `POST /api/webhooks/{id}/test/` - Test webhook

## Deployment

### Render.com

1. Fork/push code to GitHub
2. Connect to Render
3. Use the Blueprint (render.yaml) for automatic setup

### Environment Variables

| Variable | Description |
|----------|-------------|
| SECRET_KEY | Django secret key |
| DEBUG | Debug mode (false in production) |
| DATABASE_URL | PostgreSQL connection string |
| REDIS_URL | Redis connection string |
| ALLOWED_HOSTS | Comma-separated list of allowed hosts |

## License

MIT
