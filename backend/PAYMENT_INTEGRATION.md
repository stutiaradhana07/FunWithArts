# Payment Gateway Integration - Razorpay

## Overview

This document explains the complete Razorpay payment gateway integration for Udaan Studio pottery ecommerce website.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The following packages are required:
- `razorpay>=1.3.0` - Razorpay Python SDK
- `django>=5.1,<7` - Django framework
- `djangorestframework>=3.15,<4` - Django REST Framework

### 2. Environment Variables

Add the following to your `.env` file:

```env
# Razorpay Payment Gateway Configuration
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
```

To get these credentials:
1. Sign up at [Razorpay Dashboard](https://dashboard.razorpay.com/)
2. Go to Settings → API Keys
3. Generate a new key pair for test mode
4. For webhooks, go to Settings → Webhooks and add your webhook URL

### 3. Database Migration

Run migrations to create payment tables:

```bash
python manage.py makemigrations payments
python manage.py migrate
```

## API Endpoints

### 1. Create Payment Order

**Endpoint:** `POST /api/payments/create-order/`
**Authentication:** Required
**Request Body:**
```json
{
    "order_id": 123
}
```

**Response:**
```json
{
    "razorpay_order_id": "order_1234567890",
    "amount": 201000,
    "currency": "INR",
    "receipt": "order_123",
    "key_id": "rzp_test_1234567890",
    "name": "Udaan Studio",
    "description": "Payment for Order #123",
    "prefill": {
        "email": "customer@example.com",
        "contact": "9999999999"
    }
}
```

### 2. Verify Payment

**Endpoint:** `POST /api/payments/verify/`
**Authentication:** Required
**Request Body:**
```json
{
    "razorpay_order_id": "order_1234567890",
    "razorpay_payment_id": "pay_1234567890",
    "razorpay_signature": "1234567890abcdef"
}
```

**Response:**
```json
{
    "message": "Payment verified successfully",
    "payment_id": 1,
    "order_id": 123,
    "status": "captured"
}
```

### 3. Get Payment Details

**Endpoint:** `GET /api/payments/{payment_id}/`
**Authentication:** Required

**Response:**
```json
{
    "id": 1,
    "order": 123,
    "razorpay_order_id": "order_1234567890",
    "razorpay_payment_id": "pay_1234567890",
    "amount": "20100.00",
    "currency": "INR",
    "status": "captured",
    "payment_method": "card",
    "created_at": "2026-05-12T10:30:00Z",
    "captured_at": "2026-05-12T10:31:00Z"
}
```

### 4. Create Refund

**Endpoint:** `POST /api/payments/refund/`
**Authentication:** Required
**Request Body:**
```json
{
    "payment_id": 1,
    "amount": "20100.00",
    "reason": "Customer requested refund"
}
```

**Response:**
```json
{
    "message": "Refund processed successfully",
    "refund_id": 1,
    "razorpay_refund_id": "refund_1234567890",
    "amount": 20100.00
}
```

### 5. Webhook Handler

**Endpoint:** `POST /api/payments/webhook/`
**Authentication:** None (signature-based)

Handles Razorpay webhook events:
- `payment.captured` - Payment successful
- `payment.failed` - Payment failed
- `refund.processed` - Refund processed

## Payment Flow

### 1. Order Creation
1. Customer creates order via `POST /api/orders/`
2. Order status is set to:
   - `PENDING` for card/UPI payments
   - `CONFIRMED` for COD orders

### 2. Payment Initiation (for online payments)
1. Frontend calls `POST /api/payments/create-order/` with order_id
2. Backend creates Razorpay order and returns order details
3. Frontend initializes Razorpay checkout with returned details

### 3. Payment Completion
1. Customer completes payment on Razorpay checkout
2. Razorpay calls frontend success handler with payment details
3. Frontend calls `POST /api/payments/verify/` to verify payment
4. Backend verifies signature and updates order status to `CONFIRMED`

### 4. Webhook Processing (Backup)
1. Razorpay sends webhook to `POST /api/payments/webhook/`
2. Backend verifies webhook signature
3. Updates payment and order status accordingly

## Payment Methods Supported

- **Card** - Credit/Debit cards
- **UPI** - Unified Payments Interface
- **Net Banking** - Internet banking
- **Wallet** - Mobile wallets (PhonePe, Paytm, etc.)
- **COD** - Cash on Delivery

## Order Status Flow

```
Order Created
    ↓
[PENDING] - For online payments
    ↓
Payment Verified → [CONFIRMED]
    ↓
[SHIPPED]
    ↓
[DELIVERED]

For COD:
Order Created → [CONFIRMED] → [SHIPPED] → [DELIVERED]
```

## Payment Status Flow

```
Payment Created → [CREATED]
    ↓
Payment Initiated → [PENDING]
    ↓
Payment Success → [CAPTURED]
    ↓
Refund Initiated → [REFUNDED]

Payment Failed → [FAILED]
```

## Frontend Integration

### Razorpay Checkout Script

Include Razorpay checkout script in your frontend:

```html
<script src="https://checkout.razorpay.com/v1/checkout.js"></script>
```

### Payment Initialization

```javascript
// 1. Create payment order
const response = await fetch('/api/payments/create-order/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Token your_auth_token'
    },
    body: JSON.stringify({ order_id: 123 })
});

const { razorpay_order_id, key_id, amount, currency, name, description, prefill } = await response.json();

// 2. Initialize Razorpay checkout
const options = {
    key: key_id,
    amount: amount,
    currency: currency,
    name: name,
    description: description,
    order_id: razorpay_order_id,
    prefill: prefill,
    handler: async function (response) {
        // 3. Verify payment
        const verifyResponse = await fetch('/api/payments/verify/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Token your_auth_token'
            },
            body: JSON.stringify({
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
            })
        });
        
        const result = await verifyResponse.json();
        if (result.status === 'captured') {
            // Payment successful - redirect to success page
            window.location.href = '/order-success';
        }
    },
    modal: {
        ondismiss: function() {
            // Payment cancelled by user
            console.log('Payment cancelled');
        }
    }
};

const rzp = new Razorpay(options);
rzp.open();
```

## Security Considerations

1. **Signature Verification**: All payment verifications use Razorpay's signature verification
2. **Webhook Security**: Webhooks are verified using HMAC-SHA256 signatures
3. **Amount Validation**: Order amounts are validated against Razorpay response
4. **User Authorization**: Users can only access their own payments
5. **CSRF Protection**: Webhook endpoint is exempt from CSRF but uses signature verification

## Testing

### Test Mode

Use Razorpay test credentials for development:
- Test cards are available in Razorpay documentation
- No actual money is deducted
- Full payment flow can be tested

### Test Cards

Common test cards for Razorpay:
- **Visa**: 4111 1111 1111 1111
- **Mastercard**: 5555 5555 5555 4444
- **Any expiry date**: Any future date
- **CVV**: Any 3 digits
- **OTP**: 123456

## Error Handling

### Common Error Responses

```json
{
    "error": "Payment record not found"
}
```

```json
{
    "error": "Invalid payment signature"
}
```

```json
{
    "error": "You can only create payment for your own orders"
}
```

## Admin Interface

Payment and refund records are available in Django admin:
- **Payments**: View all payment transactions
- **Refunds**: Manage refund requests
- **Order Status**: Update order fulfillment status

## Production Deployment

1. **Live Credentials**: Replace test credentials with live keys
2. **Webhook URL**: Update webhook URL to production endpoint
3. **SSL Certificate**: Ensure HTTPS is enabled for webhooks
4. **Environment Variables**: Securely store production credentials
5. **Monitoring**: Set up payment failure monitoring

## Troubleshooting

### Common Issues

1. **Signature Mismatch**: Check webhook secret configuration
2. **Payment Not Found**: Verify razorpay_order_id is correct
3. **Order Status Not Updated**: Check webhook processing
4. **CORS Issues**: Ensure frontend URL is in CORS_ALLOWED_ORIGINS

### Debug Mode

Enable debug logging for payment issues:

```python
import logging
logger = logging.getLogger(__name__)
```

## Support

- **Razorpay Documentation**: https://razorpay.com/docs/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Issues**: Create GitHub issue for technical problems
