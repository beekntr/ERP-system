# ERP Purchase Order Management System

A production-quality mini ERP purchasing module built with FastAPI, SQLite, and Bootstrap. This system allows authenticated users to manage vendors, products, and purchase orders with automatic tax calculations.

**Assignment:** IV Innovations Private Limited - ERP System PO Management

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)
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

### Core Requirements Met
- **RESTful API**: Built with FastAPI (Python)
- **Database Schema**: Three related tables - Vendors, Products, PurchaseOrders with proper FK relationships
- **Calculate Total Function**: Automatically applies 5% tax and updates Total Amount
- **Dashboard**: View all Purchase Orders with status and amounts
- **Create New PO Form**: Fetches Vendors and Products via API
- **Dynamic UI**: Vanilla JS allows adding multiple product rows before submitting
- **OAuth Authentication**: Google OAuth with JWT tokens

### Additional Features
- **AI Auto-Description**: Button to generate product descriptions using OpenAI/Gemini
- **Rate Limiting**: API rate limiting with slowapi
- **Input Sanitization**: XSS protection with bleach
- **Responsive Design**: Bootstrap 5.3 with CSS Flexbox/Grid

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│   HTML5 + Bootstrap 5.3 + Vanilla JavaScript                │
│   (login.html, dashboard.html, vendors.html, etc.)          │
├─────────────────────────────────────────────────────────────┤
│                      API Layer (Routes)                      │
│   FastAPI RESTful endpoints with JWT authentication          │
│   /api/vendors, /api/products, /api/purchase-orders         │
├─────────────────────────────────────────────────────────────┤
│                   Business Logic Layer                       │
│   CRUD operations, tax calculations, validations             │
│   (crud.py, auth.py, security.py)                           │
├─────────────────────────────────────────────────────────────┤
│                   Data Access Layer                          │
│   SQLAlchemy ORM, Pydantic schemas                          │
│   (models.py, schemas.py, database.py)                      │
├─────────────────────────────────────────────────────────────┤
│                      Database Layer                          │
│   SQLite with relational integrity (PK/FK)                   │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Python 3.9+**
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - ORM for database operations
- **SQLite** - Lightweight relational database (easily switchable to PostgreSQL)
- **Pydantic** - Data validation
- **slowapi** - Rate limiting
- **bleach** - Input sanitization

### Authentication
- **Google OAuth 2.0** - Social login
- **JWT (JSON Web Tokens)** - Stateless authentication
- **python-jose** - JWT encoding/decoding

### Frontend
- **HTML5**
- **CSS3** (Flexbox/Grid)
- **Bootstrap 5.3**
- **Vanilla JavaScript** (jQuery-free)

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

### Step 4: Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
# Required: SECRET_KEY
# Optional: GOOGLE_CLIENT_ID, OPENAI_API_KEY, GEMINI_API_KEY
```

**Note:** SQLite database is created automatically on first run. No database setup required.

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| DATABASE_URL | No | SQLite connection string (default: `sqlite:///./erp_po_system.db`) |
| SECRET_KEY | Yes | JWT signing key (use `openssl rand -hex 32`) |
| GOOGLE_CLIENT_ID | No* | Google OAuth client ID |
| GOOGLE_CLIENT_SECRET | No* | Google OAuth client secret |
| OPENAI_API_KEY | No | For AI product descriptions (OpenAI) |
| GEMINI_API_KEY | No | For AI product descriptions (Google Gemini) |
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
python run.py
```

Or using uvicorn directly:
```bash
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
│   ├── security.py          # Rate limiting, sanitization
│   └── routes/
│       ├── __init__.py      # Routes package
│       ├── auth_routes.py   # Authentication endpoints
│       ├── vendors.py       # Vendor CRUD endpoints
│       ├── products.py      # Product CRUD endpoints
│       └── purchase_orders.py # PO endpoints
├── frontend/
│   ├── login.html           # Login page (Google OAuth)
│   ├── dashboard.html       # Dashboard with PO list
│   ├── vendors.html         # Vendor management
│   ├── products.html        # Product management
│   └── create_po.html       # Create purchase order form
├── static/
│   ├── css/
│   │   └── styles.css       # Custom styles (Flexbox/Grid)
│   └── js/
│       ├── app.js           # Common utilities, auth handling
│       └── po.js            # PO-specific functions
├── database/
│   └── schema.sql           # SQL schema export
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
├── run.py                   # Server runner script
└── README.md                # This file
```

## Business Logic

### Calculate Total Function (Assignment Requirement)

The system automatically applies 5% tax and updates Total Amount based on items added to the PO. All calculations are performed server-side in `crud.py`:

```python
subtotal = Σ(item.quantity × item.price)  # Sum of all line items
tax = subtotal × 0.05                      # 5% tax automatically applied
total_amount = subtotal + tax              # Final amount
```

This ensures:
- Data integrity (calculations done server-side)
- Consistent tax application (5% as per requirement)
- Automatic updates when items are added/modified

### Reference Number Generation

Purchase order reference numbers are auto-generated:

```
Format: PO-{YYYYMMDDHHMMSS}-{8-char-UUID}
Example: PO-20260310143022-A1B2C3D4
```

## Security Features

- **JWT Authentication**: Stateless token-based auth with expiration
- **Input Validation**: Pydantic schemas validate all input
- **Input Sanitization**: XSS protection using bleach library
- **Rate Limiting**: API rate limiting with slowapi (prevents abuse)
- **CORS Protection**: Configured middleware
- **Environment Variables**: Secrets stored securely
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries

## AI Auto-Description Feature (Gen AI Integration)

The "Auto-Description" button on Products page generates professional marketing descriptions:

1. **OpenAI Integration**: Uses GPT-3.5-turbo if `OPENAI_API_KEY` is configured
2. **Google Gemini**: Falls back to Gemini Pro if `GEMINI_API_KEY` is configured
3. **Template Fallback**: Uses intelligent templates if no API keys available

Example prompt: *"Write a professional 2-sentence marketing description for: {product_name}"*

## Troubleshooting

### Database Issues

The SQLite database (`erp_po_system.db`) is created automatically. To reset:
```bash
rm erp_po_system.db
python run.py  # Recreates database
```

### Authentication Errors

- Verify JWT token in Authorization header
- Check token expiration (default: 60 minutes)
- Use Development Login when DEBUG=True

### CORS Issues

If accessing from different origin, update CORS settings in `main.py`.

## Database Schema Export

SQL schema file is located at `database/schema.sql`. This includes all table definitions with Primary Keys, Foreign Keys, and constraints.

## Design Choices

### Why SQLite over PostgreSQL?
- Zero configuration required for demo/evaluation
- Easy to distribute and run locally
- SQLAlchemy ORM makes switching to PostgreSQL trivial (change DATABASE_URL)

### Why Vanilla JS over jQuery?
- Modern browsers support all required features natively
- Smaller bundle size, faster load times
- Better alignment with contemporary web development practices

### Why Server-Side Tax Calculation?
- Ensures data integrity (can't be manipulated client-side)
- Single source of truth for business logic
- Easy to audit and modify tax rates

### Add Row Logic (Frontend)
- Items stored in JavaScript array before submission
- Real-time subtotal/tax/total calculation displayed
- Edit/Remove functionality with instant UI updates
- Single API call on submit for better performance

## Author

Developed for IV Innovations Private Limited Assignment

## License

MIT License - Feel free to use and modify for your projects.
4. Push to the branch
5. Create a Pull Request
