# ShopZone Backend

ShopZone Backend is a Django REST API that powers authentication, product catalog browsing, cart management, and wishlist management for the ShopZone frontend.

## Features

- JWT-based authentication
- Public product listing and product detail endpoints
- Filterable and paginated product catalog
- Authenticated cart and wishlist APIs
- Backend coupon validation and checkout/order APIs
- Ownership enforcement so users can only access their own cart and wishlist records
- Database migrations and product seeding support

## Requirements

- Python 3.11 or later
- `pip`
- SQLite is used by default for local development

## Repository Layout

- `accounts/` - custom user model and auth endpoints
- `catalog/` - product model, catalog APIs, tests, and seed command
- `commerce/` - cart and wishlist models and APIs
- `config/` - project settings and root URL configuration

## Environment Variables

Create a local `.env` file from `.env.example` and set the following values:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret key used for signing and security-sensitive operations |
| `DJANGO_DEBUG` | Enables or disables debug mode |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated list of allowed hostnames |
| `DJANGO_CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |

Example:

```env
DJANGO_SECRET_KEY=change-me-to-a-long-random-development-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

4. Update `.env` with your local values if needed.

## Database Setup

Apply migrations:

```bash
python manage.py migrate
```

Seed the product catalog:

```bash
python manage.py seed_products
```

Seed the default coupons:

```bash
python manage.py seed_coupons
```

## Run the Server

Start the development server:

```bash
python manage.py runserver
```

The API is available at:

```text
http://127.0.0.1:8000
```

## Testing

Run the backend test suite:

```bash
python manage.py test
```

## API Summary

### Public Endpoints

- `GET /api/products/`
- `GET /api/products/{id}/`

### Authenticated Endpoints

- `GET /api/cart/`
- `POST /api/cart/`
- `PATCH /api/cart/items/{id}/`
- `DELETE /api/cart/items/{id}/`
- `GET /api/wishlist/`
- `POST /api/wishlist/`
- `DELETE /api/wishlist/items/{id}/`
- `GET /api/coupons/`
- `POST /api/coupons/validate/`
- `POST /api/checkout/`
- `GET /api/orders/`
- `GET /api/orders/{id}/`

## Frontend Integration

The React frontend should point `REACT_APP_API_BASE_URL` to this backend instance.

If the frontend runs locally on port `3000`, make sure `DJANGO_CORS_ALLOWED_ORIGINS` includes:

```text
http://localhost:3000
http://127.0.0.1:3000
```

## Verification Checklist

- `python manage.py migrate` completes successfully
- `python manage.py seed_products` creates or updates catalog records
- `python manage.py seed_coupons` creates or updates default coupons
- `python manage.py test` passes
- `GET /api/products/` returns product data
- Authenticated cart and wishlist requests return the current user's data only
- Checkout creates an order and clears the cart
