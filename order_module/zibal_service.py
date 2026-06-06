# order_module/zibal_service.py
import requests
import json
import logging

logger = logging.getLogger(__name__)

# تنظیمات درگاه (می‌تونید از Zibal یا ZarinPal استفاده کنید)
ZIBAL_MERCHANT = "zibal"  # merchant id شما
ZIBAL_REQUEST_URL = "https://gateway.zibal.ir/v1/request"
ZIBAL_VERIFY_URL = "https://gateway.zibal.ir/v1/verify"
ZIBAL_STARTPAY = "https://gateway.zibal.ir/start/{}"

# یا از ZarinPal (مشابه سایت قبلی)
ZARINPAL_MERCHANT = "3a681e90-59c0-4511-8101-655b26314ae5"  # merchant id خودتون
ZARINPAL_REQUEST_URL = "https://sandbox.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://sandbox.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_STARTPAY = "https://sandbox.zarinpal.com/pg/StartPay/{authority}"


def zarinpal_send_request(amount, callback_url, description="پرداخت خدمت"):
    """
    ارسال درخواست به زرین‌پال
    """
    req_data = {
        "merchant_id": ZARINPAL_MERCHANT,
        "amount": amount,
        "callback_url": callback_url,
        "description": description,
    }

    req_headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    try:
        response = requests.post(
            ZARINPAL_REQUEST_URL,
            data=json.dumps(req_data),
            headers=req_headers,
            timeout=10
        )
        return response.json()
    except Exception as e:
        logger.error(f"ZarinPal Request Error: {e}")
        return {"error": str(e)}


def zarinpal_verify_payment(authority, amount):
    """
    وریفای پرداخت زرین‌پال
    """
    req_data = {
        "merchant_id": ZARINPAL_MERCHANT,
        "amount": amount,
        "authority": authority,
    }

    req_headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    try:
        response = requests.post(
            ZARINPAL_VERIFY_URL,
            data=json.dumps(req_data),
            headers=req_headers,
            timeout=10
        )
        return response.json()
    except Exception as e:
        logger.error(f"ZarinPal Verify Error: {e}")
        return {"error": str(e)}