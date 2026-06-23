# order_module/zibal_service.py
import requests
import json
import logging

logger = logging.getLogger(__name__)

# تنظیمات درگاه (می‌تونید از Zibal یا ZarinPal استفاده کنید)
ZIBAL_MERCHANT = ""  # merchant id شما
ZIBAL_REQUEST_URL = "https://gateway.zibal.ir/v1/request"
ZIBAL_VERIFY_URL = "https://gateway.zibal.ir/v1/verify"
ZIBAL_STARTPAY = "https://gateway.zibal.ir/start/{}"

# یا از ZarinPal (مشابه سایت قبلی)
ZARINPAL_MERCHANT = "3a681e90-59c0-4511-8101-655b26314ae5"  # merchant id خودتون
ZARINPAL_REQUEST_URL = "https://payment.zarinpal.com/pg/v4/payment/request.json"
ZARINPAL_VERIFY_URL = "https://payment.zarinpal.com/pg/v4/payment/verify.json"
ZARINPAL_STARTPAY = "https://payment.zarinpal.com/pg/StartPay/{authority}"


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
# order_module/payment_service.py
# import json
# import logging
# import requests
# from django.urls import reverse
# from .payment_config import get_active_gateway, PaymentGateway

# logger = logging.getLogger(__name__)

# class PaymentService:
#     """سرویس یکپارچه پرداخت برای همه درگاه‌ها"""
    
#     def __init__(self, request=None):
#         self.request = request
#         self.gateway_type, self.gateway_config = get_active_gateway()
#         logger.info(f"Active payment gateway: {self.gateway_type.value}")
    
#     def send_to_gateway(self, amount, callback_url, description="", service_id=None, return_url=None):
#         """
#         ارسال به درگاه پرداخت مناسب
#         بسته به نوع درگاه، رفتار متفاوتی دارد
#         """
#         if self.gateway_type == PaymentGateway.ZARINPAL:
#             return self._send_to_zarinpal_via_intermediate(
#                 amount, callback_url, description, service_id
#             )
#         elif self.gateway_type == PaymentGateway.ZIBAL:
#             return self._send_to_zibal_direct(
#                 amount, callback_url, description
#             )
#         else:
#             raise ValueError(f"Unknown gateway: {self.gateway_type}")
    
#     def verify_payment(self, authority=None, amount=None, track_id=None):
#         """
#         وریفای پرداخت از درگاه مناسب
#         """
#         if self.gateway_type == PaymentGateway.ZARINPAL:
#             return self._verify_zarinpal_direct(authority, amount)
#         elif self.gateway_type == PaymentGateway.ZIBAL:
#             return self._verify_zibal_direct(track_id)
#         else:
#             raise ValueError(f"Unknown gateway: {self.gateway_type}")
    
#     def _send_to_zarinpal_via_intermediate(self, amount, callback_url, description, service_id):
#         """
#         ارسال به زرین‌پال از طریق سایت واسط
#         """
#         # ساخت URL برای سایت واسط
#         intermediate_url = (
#             f"{self.gateway_config['intermediate_site']}"
#             f"{self.gateway_config['intermediate_verify_path']}"
#         )
        
#         # پارامترهایی که باید به سایت واسط ارسال شود
#         params = {
#             'article_id': service_id,  # یا service_id
#             'amount': amount,
#             'return_url': callback_url,  # آدرس بازگشت به سایت خودمان
#             'merchant_id': self.gateway_config['merchant_id'],
#         }
        
#         # ساخت URL کامل با پارامترها
#         query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
#         final_url = f"{intermediate_url}?{query_string}"
        
#         return {
#             'success': True,
#             'redirect_url': final_url,
#             'gateway': 'zarinpal_intermediate',
#             'service_id': service_id,
#         }
    
#     def _send_to_zibal_direct(self, amount, callback_url, description):
#         """
#         ارسال مستقیم به زیبال
#         """
#         req_data = {
#             "merchant": self.gateway_config['merchant_id'],
#             "amount": amount,
#             "callbackUrl": callback_url,
#             "description": description,
#         }
        
#         req_headers = {
#             "accept": "application/json",
#             "content-type": "application/json"
#         }
        
#         try:
#             resp = requests.post(
#                 self.gateway_config['request_url'],
#                 data=json.dumps(req_data),
#                 headers=req_headers,
#                 timeout=10
#             )
#             result = resp.json()
            
#             if result.get('result') == 100:
#                 track_id = result.get('trackId')
#                 startpay_url = self.gateway_config['startpay_url'].format(trackId=track_id)
                
#                 return {
#                     'success': True,
#                     'redirect_url': startpay_url,
#                     'gateway': 'zibal_direct',
#                     'track_id': track_id,
#                 }
#             else:
#                 logger.error(f"Zibal request error: {result}")
#                 return {
#                     'success': False,
#                     'error': result.get('message', 'خطا در اتصال به زیبال'),
#                 }
                
#         except Exception as e:
#             logger.error(f"Zibal request exception: {e}")
#             return {
#                 'success': False,
#                 'error': 'خطا در اتصال به درگاه',
#             }
    
#     def _verify_zarinpal_direct(self, authority, amount):
#         """
#         وریفای مستقیم زرین‌پال (برای وقتی که خودمان مستقیم با زرین‌پال کار می‌کنیم)
#         """
#         req_data = {
#             "merchant_id": self.gateway_config['merchant_id'],
#             "amount": amount,
#             "authority": authority,
#         }
        
#         req_headers = {
#             "accept": "application/json",
#             "content-type": "application/json"
#         }
        
#         try:
#             resp = requests.post(
#                 self.gateway_config['verify_url'],
#                 data=json.dumps(req_data),
#                 headers=req_headers,
#                 timeout=10
#             )
#             result = resp.json()
#             return result
#         except Exception as e:
#             logger.error(f"ZarinPal verify error: {e}")
#             return {"error": str(e)}
    
#     def _verify_zibal_direct(self, track_id):
#         """
#         وریفای مستقیم زیبال
#         """
#         req_data = {
#             "merchant": self.gateway_config['merchant_id'],
#             "trackId": track_id,
#         }
        
#         req_headers = {
#             "accept": "application/json",
#             "content-type": "application/json"
#         }
        
#         try:
#             resp = requests.post(
#                 self.gateway_config['verify_url'],
#                 data=json.dumps(req_data),
#                 headers=req_headers,
#                 timeout=10
#             )
#             result = resp.json()
#             return result
#         except Exception as e:
#             logger.error(f"Zibal verify error: {e}")
#             return {"error": str(e)}