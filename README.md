# ERP Purchase Order Management System

A production-quality mini ERP purchasing module built with FastAPI, PostgreSQL, and Bootstrap. This system allows authenticated users to manage vendors, products, and purchase orders with automatic tax calculations.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Examples](#api-examples)
- [Project Structure](#project-structure)

## Features

- **User Authentication**: Google OAuth 2.0 with JWT tokens
- **Vendor Management**: Create, read, update, delete vendors
- **Product Management**: Full CRUD operations with SKU tracking
- **Purchase Orders**: Create orders with multiple items
- **Automatic Calculations**: Subtotal, tax (5%), and total computed automatically
- **AI-Powered Descriptions**: Optional LLM integration for product descriptions
- **Responsive Dashboard**: Bootstrap-based UI with real-time statistics

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│   HTML + Bootstrap + Vanilla JavaScript                     │
│   (login.html, dashboard.html, vendors.html, etc.)          │
├─────────────────────────────────────────────────────────────┤
│                      API Layer (Routes)                      │
│   FastAPI endpoints with authentication                      │
│   /api/vendors, /api/products, /api/purchase-orders         │
├─────────────────────────────────────────────────────────────┤
│                   Business Logic Layer                       │
│   CRUD operations, calculations, validations                 │
│   (crud.py, auth.py)                                        │
├─────────────────────────────────────────────────────────────┤
│                   Data Access Layer                          │
│   SQLAlchemy ORM, Pydantic schemas                          │
│   (models.py, schemas.py, database.py)                      │
├─────────────────────────────────────────────────────────────┤
│                      Database Layer                          │
│   PostgreSQL with relational integrity                       │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Python 3.9+**
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - ORM for database operations
- **PostgreSQL** - Relational database
- **Pydantic** - Data validation

### Authentication
- **Google OAuth 2.0** - Social login
- **JWT (JSON Web Tokens)** - Stateless authentication
- **python-jose** - JWT encoding/decoding

### Frontend
- **HTML5**
- **CSS3**
- **Bootstrap 5.3**
- **Vanilla JavaScript**

## Database Schema

### Entity Relationship Diagram

```
┌──────────────┐     ┌───────────────────┐     ┌────────────┐
│    users     │     │  purchase_orders  │     │   vendors  │
├──────────────┤     ├───────────────────┤     ├────────────┤
│ id (PK)      │     │ id (PK)           │     │ id (PK)    │
│ email        │     │ reference_no (UK) │────▶│ name       │
│ name         │     │ vendor_id (FK)    │     │ contact    │
│ oauth_provider│     │ order_date        │     │ rating     │
│ created_at   │     │ status            │     │ created_at │
└──────────────┘     │ subtotal          │     └────────────┘
                     │ tax               │
                     │ total_amount      │
                     │ created_at        │
                     └─────────┬─────────┘
                               │
                               │ 1:N
                               ▼
                     ┌─────────────────┐     ┌────────────┐
                     │    po_items     │     │  products  │
                     ├─────────────────┤     ├────────────┤
                     │ id (PK)         │     │ id (PK)    │
                     │ po_id (FK)      │     │ name       │
                     │ product_id (FK) │────▶│ sku (UK)   │
                     │ quantity        │     │ unit_price │
                     │ price           │     │ stock_level│
                     └─────────────────┘     │ description│
                                             │ created_at │
                                             └────────────┘
```

### Tables

#### users
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| email | VARCHAR(255) | Unique email address |
| name | VARCHAR(255) | User's display name |
| oauth_provider | VARCHAR(50) | OAuth provider (google) |
| created_at | TIMESTAMP | Account creation time |

#### vendors
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(255) | Vendor name |
| contact_info | TEXT | Contact details |
| rating | FLOAT | Rating (0-5) |
| created_at | TIMESTAMP | Creation time |

#### products
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | VARCHAR(255) | Product name |
| sku | VARCHAR(100) | Unique SKU |
| unit_price | FLOAT | Price per unit |
| stock_level | INTEGER | Current stock |
| description | TEXT | Product description |
| created_at | TIMESTAMP | Creation time |

#### purchase_orders
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| reference_no | VARCHAR(50) | Unique reference (auto-generated) |
| vendor_id | INTEGER | Foreign key to vendors |
| order_date | TIMESTAMP | Order date |
| status | ENUM | draft, pending, approved, ordered, received, cancelled |
| subtotal | FLOAT | Sum of line items |
| tax | FLOAT | Tax amount (5%) |
| total_amount | FLOAT | subtotal + tax |
| created_at | TIMESTAMP | Creation time |

#### po_items
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| po_id | INTEGER | Foreign key to purchase_orders |
| product_id | INTEGER | Foreign key to products |
| quantity | INTEGER | Quantity ordered |
| price | FLOAT | Unit price at order time |

## API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/google` | Authenticate with Google OAuth |
| POST | `/api/auth/dev-login` | Development login (debug mode only) |
| GET | `/api/auth/me` | Get current user info |
| POST | `/api/auth/logout` | Logout |
| GET | `/api/auth/config` | Get OAuth configuration |

### Vendor Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/vendors` | List all vendors |
| GET | `/api/vendors/{id}` | Get vendor by ID |
| POST | `/api/vendors` | Create new vendor |
| PUT | `/api/vendors/{id}` | Update vendor |
| DELETE | `/api/vendors/{id}` | Delete vendor |

### Product Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all products |
| GET | `/api/products/{id}` | Get product by ID |
| POST | `/api/products` | Create new product |
| PUT | `/api/products/{id}` | Update product |
| DELETE | `/api/products/{id}` | Delete product |
| POST | `/api/products/generate-description` | AI-generate description |

### Purchase Order Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/purchase-orders` | List all purchase orders |
| GET | `/api/purchase-orders/{id}` | Get PO with items |
| POST | `/api/purchase-orders` | Create new PO |
| PUT | `/api/purchase-orders/{id}` | Update PO status |
| DELETE | `/api/purchase-orders/{id}` | Delete PO |

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL 13 or higher
- Git

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd erp_po_system
```

### Step 2: Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Setup PostgreSQL Database

```sql
-- Connect to PostgreSQL and create database
CREATE DATABASE erp_po_db;
```

### Step 5: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
# Required: DATABASE_URL, SECRET_KEY
# Optional: GOOGLE_CLIENT_ID, OPENAI_API_KEY
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | Yes | PostgreSQL connection string |
| SECRET_KEY | Yes | JWT signing key (use `openssl rand -hex 32`) |
| GOOGLE_CLIENT_ID | No* | Google OAuth client ID |
| GOOGLE_CLIENT_SECRET | No* | Google OAuth client secret |
| OPENAI_API_KEY | No | For AI product descriptions |
| TAX_RATE | No | Tax rate (default: 0.05 = 5%) |
| DEBUG | No | Enable debug mode (default: True) |

*Required for Google OAuth authentication. Development login available when DEBUG=True.

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/api/auth/callback`
6. Copy Client ID and Client Secret to `.env`

## Running the Application

### Start the Server

```bash
# From the erp_po_system directory
uvicorn backend.main:app --reload
```

The application will be available at:
- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/api/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/api/redoc

### Using Development Login

When DEBUG=True, you can use the "Development Login" button on the login page to authenticate without Google OAuth.

## API Examples

### Create a Vendor

```bash
curl -X POST "http://localhost:8000/api/vendors" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "contact_info": "contact@acme.com",
    "rating": 4.5
  }'
```

### Create a Product

```bash
curl -X POST "http://localhost:8000/api/products" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Wireless Keyboard",
    "sku": "KB-001",
    "unit_price": 49.99,
    "stock_level": 100,
    "description": "Ergonomic wireless keyboard"
  }'
```

### Create a Purchase Order

```bash
curl -X POST "http://localhost:8000/api/purchase-orders" \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_id": 1,
    "items": [
      {"product_id": 1, "quantity": 3, "price": 120.00},
      {"product_id": 2, "quantity": 5, "price": 80.00}
    ]
  }'
```

**Response:**
```json
{
  "id": 1,
  "reference_no": "PO-20260310143022-A1B2C3D4",
  "vendor_id": 1,
  "order_date": "2026-03-10T14:30:22",
  "status": "draft",
  "subtotal": 760.00,
  "tax": 38.00,
  "total_amount": 798.00,
  "vendor": {...},
  "items": [...]
}
```

### Get All Purchase Orders

```bash
curl -X GET "http://localhost:8000/api/purchase-orders" \
  -H "Authorization: Bearer <your-token>"
```

## Project Structure

```
erp_po_system/
├── backend/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration and settings
│   ├── database.py          # Database connection and session
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic validation schemas
│   ├── crud.py              # Database CRUD operations
│   ├── auth.py              # Authentication utilities
│   └── routes/
│       ├── __init__.py      # Routes package
│       ├── auth_routes.py   # Authentication endpoints
│       ├── vendors.py       # Vendor CRUD endpoints
│       ├── products.py      # Product CRUD endpoints
│       └── purchase_orders.py # PO endpoints
├── frontend/
│   ├── login.html           # Login page
│   ├── dashboard.html       # Dashboard with PO list
│   ├── vendors.html         # Vendor management
│   ├── products.html        # Product management
│   └── create_po.html       # Create purchase order
├── static/
│   ├── css/
│   │   └── styles.css       # Custom styles
│   └── js/
│       ├── app.js           # Common utilities
│       └── po.js            # PO-specific functions
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Business Logic

### Tax Calculation

All calculations are performed server-side:

```
subtotal = Σ(item.quantity × item.price)
tax = subtotal × 0.05
total_amount = subtotal + tax
```

### Reference Number Generation

Purchase order reference numbers are auto-generated:

```
Format: PO-{YYYYMMDDHHMMSS}-{8-char-UUID}
Example: PO-20260310143022-A1B2C3D4
```

## Security Features

- **JWT Authentication**: Stateless token-based auth
- **Input Validation**: Pydantic schemas validate all input
- **CORS Protection**: Configured middleware
- **Environment Variables**: Secrets stored securely
- **SQL Injection Prevention**: SQLAlchemy ORM

## Troubleshooting

### Database Connection Issues

```bash
# Verify PostgreSQL is running
pg_isready -h localhost -p 5432

# Check connection string format
postgresql://user:password@host:port/database
```

### Authentication Errors

- Verify JWT token in Authorization header
- Check token expiration (default: 60 minutes)
- In debug mode, use Development Login

### CORS Issues

If accessing from different origin, update CORS settings in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://your-frontend-url"],
    ...
)
```

## License

MIT License - Feel free to use and modify for your projects.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
