# Backend API Contract (Frontend Integration)

Base URL: `/api/`

## Health
- `GET /api/health/`

Response:
```json
{ "status": "ok" }
```

## Products
- `GET /api/products/`
- `GET /api/products/{id}/`

Product object:
```json
{
  "id": 1,
  "name": "The Guardians",
  "description": "Handmade wall decor",
  "price": 7800.0,
  "stock": 10,
  "image": "/media/products/item.jpg",
  "image_url": "http://localhost:8000/media/products/item.jpg",
  "category": "Decor",
  "is_available": true,
  "is_new": true,
  "isNew": true,
  "created_at": "2026-04-28T10:00:00Z"
}
```

## Orders
- `POST /api/orders/`

Request:
```json
{
  "contact_email": "user@example.com",
  "contact_phone": "9999999999",
  "shipping_first_name": "Aarav",
  "shipping_last_name": "Sharma",
  "shipping_address_line_1": "123 Street",
  "shipping_address_line_2": "",
  "shipping_city": "Delhi",
  "shipping_state": "Delhi",
  "shipping_pincode": "110001",
  "payment_method": "card",
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 2, "quantity": 1 }
  ]
}
```

Response (`201`):
```json
{
  "id": 4,
  "contact_email": "user@example.com",
  "contact_phone": "9999999999",
  "shipping_first_name": "Aarav",
  "shipping_last_name": "Sharma",
  "shipping_address_line_1": "123 Street",
  "shipping_address_line_2": "",
  "shipping_city": "Delhi",
  "shipping_state": "Delhi",
  "shipping_pincode": "110001",
  "payment_method": "card",
  "subtotal": 20100.0,
  "shipping_fee": 0.0,
  "total_amount": 20100.0,
  "status": "pending",
  "created_at": "2026-04-28T11:00:00Z",
  "items": [
    {
      "id": 10,
      "product": 1,
      "product_name": "The Guardians",
      "unit_price": 7800.0,
      "quantity": 2,
      "line_total": 15600.0
    }
  ]
}
```

## Delivery Check
- `GET /api/delivery-check/?pincode=110001`

Response:
```json
{
  "pincode": "110001",
  "is_serviceable": true,
  "estimated_delivery": "3-5 business days"
}
```

## Newsletter
- `POST /api/newsletter/subscribe/`

Request:
```json
{ "email": "hello@example.com" }
```

Response:
```json
{
  "message": "Subscribed successfully",
  "email": "hello@example.com",
  "already_subscribed": false
}
```

## Auth
- `POST /api/auth/register/`
- `POST /api/auth/login/`
- `GET /api/auth/me/` (requires `Authorization: Token <token>`)

Register/Login response:
```json
{
  "message": "Login successful",
  "token": "generated-token",
  "user": {
    "id": 1,
    "username": "stuti",
    "email": "stuti@example.com"
  }
}
```
