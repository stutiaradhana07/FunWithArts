# Backend Setup and Verification

## 1) Install dependencies
```bash
pip install -r requirements.txt
```

## 2) Create env file
Copy `.env.example` to `.env` and adjust values as needed.

## 3) Migrate and seed
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py seed_store_data
python manage.py seed_shipping_zones
```

**Important**: `seed_shipping_zones` populates the ShippingZone table with valid delivery pincodes.
Without this data, all order delivery checks will fail with "Pincode not serviceable".
Run this after initial migrate to enable pincode-based delivery validation.

## 4) Run checks and tests
```bash
python manage.py check
python manage.py test
```

## 5) Start server
```bash
python manage.py runserver
```

Primary APIs:
- `http://127.0.0.1:8000/api/products/`
- `http://127.0.0.1:8000/api/orders/`
- `http://127.0.0.1:8000/api/delivery-check/?pincode=110001`
- `http://127.0.0.1:8000/api/newsletter/subscribe/`
- `http://127.0.0.1:8000/api/auth/register/`
