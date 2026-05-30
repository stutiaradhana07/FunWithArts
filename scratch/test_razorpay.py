import razorpay

KEY_ID = "rzp_test_SvcAHOM6mQQ4HB"
KEY_SECRET = "JP46wvEypnMrPdG3ybYhriaY"

try:
    print("Initializing client...")
    client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))
    
    print("Attempting to create a test order of 100 paise...")
    order = client.order.create({
        "amount": 100,
        "currency": "INR",
        "receipt": "test_receipt_123"
    })
    print("SUCCESS! Created order:", order)
except Exception as e:
    print("FAILURE! Error type:", type(e))
    print("Error message:", str(e))
