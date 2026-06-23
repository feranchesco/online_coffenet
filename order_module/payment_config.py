# order_module/payment_config.py
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class PaymentGateway(Enum):
    ZARINPAL = "zarinpal"
    ZIBAL = "zibal"

# تنظیمات درگاه‌ها - فقط درگاه فعال را مقداردهی کنید
PAYMENT_CONFIG = {
    "active_gateway": PaymentGateway.ZARINPAL,  # یا PaymentGateway.ZIBAL
    
    "zarinpal": {
        "merchant_id": "3a681e90-59c0-4511-8101-655b26314ae5",
        "request_url": "https://payment.zarinpal.com/pg/v4/payment/request.json",
        "verify_url": "https://payment.zarinpal.com/pg/v4/payment/verify.json",
        "startpay_url": "https://payment.zarinpal.com/pg/StartPay/{authority}",
        # آدرس سایت واسط برای وریفای
        "intermediate_site": "https://baharandishemoalem.ir",
        "intermediate_verify_path": "/order/irn-verify/",
    },
    
    "zibal": {
        "merchant_id": "your_zibal_merchant_id",  # merchant id زیبال خود را وارد کنید
        "request_url": "https://gateway.zibal.ir/v1/request",
        "verify_url": "https://gateway.zibal.ir/v1/verify",
        "startpay_url": "https://gateway.zibal.ir/start/{trackId}",
        # زیبال نیاز به سایت واسط ندارد
        "intermediate_site": None,
    }
}

def get_active_gateway():
    """دریافت درگاه فعال"""
    gateway = PAYMENT_CONFIG["active_gateway"]
    return gateway, PAYMENT_CONFIG[gateway.value]