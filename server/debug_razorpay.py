import sys
import os

# Add the server directory to sys.path so we can import utils
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils.razorpay_client import razorpay_client, RAZORPAY_KEY_ID

print(f"Key ID: {RAZORPAY_KEY_ID}")

if not razorpay_client:
    print("razorpay_client is None")
else:
    try:
        import uuid
        receipt_id = f"R-${str(uuid.uuid4())[:8]}"
        order = razorpay_client.order.create({
            "amount": 100,
            "currency": "INR",
            "receipt": receipt_id
        })
        print("Success:", order)
    except Exception as e:
        print("Exception caught:", e)
