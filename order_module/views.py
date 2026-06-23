# order_module/views.py
import json
import logging
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import Payment, DiscountCode
from .utils import apply_discount
from .zibal_service import (
    zarinpal_send_request,
    zarinpal_verify_payment,
    ZARINPAL_STARTPAY,
)
from home_module.models import Service

logger = logging.getLogger(__name__)

# آدرس سایت واسط (در صورت نیاز)
SITE_B_VERIFY_URL = "https://baharandishemoalem.ir/irn-verify/"

# آدرس بازگشت به سایت خودمون
CALLBACK_URL = "http://emdadmoalem.ir/pay/confirm/"


# ============================================
# صفحه پرداخت
# ============================================
@login_required
def payment_page(request, service_id):
    """صفحه پرداخت برای یک سرویس"""
    service = get_object_or_404(Service, id=service_id, customer=request.user)

    if service.is_paid:
        messages.info(request, 'این سرویس قبلاً پرداخت شده است')
        return redirect('profile')

    amount = service.final_price or service.price

    context = {
        'service': service,
        'amount': amount,
    }

    return render(request, 'order_module/payment.html', context)


# ============================================
# ارسال به درگاه پرداخت
# ============================================
@login_required
def send_to_gateway(request, service_id):
    """
    ارسال به درگاه پرداخت (زرین‌پال)
    """
    try:
        service = Service.objects.get(id=service_id, customer=request.user, is_paid=False)
    except Service.DoesNotExist:
        return HttpResponse("سرویس یافت نشد یا قبلاً پرداخت شده", status=404)

    amount = int(service.final_price or service.price)

    # ساخت callback URL
    callback_url = request.build_absolute_uri(
        reverse('verify_payment') + f'?service_id={service_id}'
    )

    # اگر از سایت واسط استفاده میکنید:
    # callback_url = f"{SITE_B_VERIFY_URL}?service_id={service_id}&amount={amount}&return_url={request.build_absolute_uri(reverse('verify_payment'))}"

    # ارسال به زرین‌پال
    result = zarinpal_send_request(
        amount=amount,
        callback_url=callback_url,
        description=f'پرداخت خدمت: {service.title}'
    )

    if result.get('data') and result['data'].get('authority'):
        authority = result['data']['authority']

        # ذخیره اطلاعات پرداخت
        Payment.objects.create(
            user=request.user,
            service=service,
            amount=amount,
            authority=authority,
            status='pending',
            description=f'پرداخت خدمت: {service.title}'
        )

        # ذخیره authority در سرویس
        service.payment_ref = authority
        service.save(update_fields=['payment_ref'])

        # ریدایرکت به درگاه
        return redirect(ZARINPAL_STARTPAY.format(authority=authority))

    else:
        logger.error(f"ZarinPal Error: {result}")
        messages.error(request, 'خطا در اتصال به درگاه پرداخت')
        return redirect('profile')


# ============================================
# وریفای پرداخت (بازگشت از درگاه)
# ============================================
@login_required
def verify_payment(request):
    """
    وریفای پرداخت بعد از بازگشت از درگاه
    """
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    service_id = request.GET.get('service_id')

    if not authority or status != 'OK':
        messages.error(request, 'پرداخت ناموفق بود یا توسط کاربر لغو شد')
        return redirect('profile')

    try:
        service = Service.objects.get(id=service_id, customer=request.user)
    except Service.DoesNotExist:
        return HttpResponse("سرویس یافت نشد", status=404)

    amount = int(service.final_price or service.price)

    # وریفای با زرین‌پال
    result = zarinpal_verify_payment(authority=authority, amount=amount)

    if result.get('data') and result['data'].get('code') == 100:
        # پرداخت موفق
        ref_id = result['data'].get('ref_id')

        # آپدیت سرویس
        service.is_paid = True
        service.payment_date = timezone.now()
        service.payment_ref = ref_id
        service.save()

        # آپدیت پرداخت
        Payment.objects.filter(authority=authority).update(
            ref_id=ref_id,
            status='success',
            payment_date=timezone.now()
        )

        context = {
            'success': True,
            'ref_id': ref_id,
            'amount': amount,
            'service': service,
        }

        return render(request, 'order_module/payment_result.html', context)

    else:
        # پرداخت ناموفق
        Payment.objects.filter(authority=authority).update(status='failed')
        messages.error(request, 'پرداخت ناموفق بود')
        return redirect('profile')


# ============================================
# API وریفای از سایت واسط
# ============================================
@csrf_exempt
def verify_from_other_site(request):
    """
    وریفای پرداخت از سایت واسط (Site B)
    این view توسط سایت دوم صدا زده میشه
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        authority = data.get('authority')
        ref_id = data.get('ref_id')
        amount = data.get('amount')
        service_id = data.get('service_id')
        secret_key = data.get('secret_key')

        # بررسی کلید امنیتی
        if secret_key != 'YOUR_SECRET_KEY_HERE':
            return JsonResponse({'error': 'Unauthorized'}, status=401)

        if not all([authority, ref_id, amount, service_id]):
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        service = get_object_or_404(Service, id=service_id)

        # آپدیت سرویس
        service.is_paid = True
        service.payment_date = timezone.now()
        service.payment_ref = ref_id
        service.save()

        # آپدیت پرداخت
        Payment.objects.filter(authority=authority).update(
            ref_id=ref_id,
            status='success',
            payment_date=timezone.now()
        )

        return JsonResponse({'success': True})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# ============================================
# اعمال کد تخفیف
# ============================================
@login_required
def apply_discount_view(request, service_id):
    """اعمال کد تخفیف روی سرویس"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    service = get_object_or_404(Service, id=service_id, customer=request.user)

    if service.is_paid:
        return JsonResponse({'success': False, 'error': 'قبلاً پرداخت شده'})

    code = request.POST.get('code', '').strip()

    if not code:
        return JsonResponse({'success': False, 'error': 'کد تخفیف را وارد کنید'})

    try:
        discount = DiscountCode.objects.get(code=code)

        if not discount.is_valid():
            return JsonResponse({'success': False, 'error': 'کد تخفیف منقضی شده است'})

        original_price = service.price
        new_price = apply_discount(original_price, discount)
        discount_amount = original_price - new_price

        # آپدیت سرویس
        service.discount_amount = discount_amount
        service.final_price = new_price
        service.discount_code = code
        service.save()

        # آپدیت استفاده از کد
        discount.used_count += 1
        discount.save()

        return JsonResponse({
            'success': True,
            'original_price': original_price,
            'discount_amount': discount_amount,
            'final_price': new_price,
            'percent': discount.discount_percent,
        })

    except DiscountCode.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'کد تخفیف نامعتبر است'})


# ============================================
# پرداخت از کیف پول
# ============================================
@login_required
def pay_from_wallet(request, service_id):
    """پرداخت از کیف پول"""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    service = get_object_or_404(Service, id=service_id, customer=request.user)

    if service.is_paid:
        return JsonResponse({'success': False, 'error': 'قبلاً پرداخت شده'})

    amount = service.final_price or service.price

    if request.user.wallet_balance < amount:
        return JsonResponse({'success': False, 'error': 'موجودی کافی نیست'})

    # کسر از کیف پول
    request.user.wallet_balance -= amount
    request.user.save(update_fields=['wallet_balance'])

    # آپدیت سرویس
    service.is_paid = True
    service.payment_date = timezone.now()
    service.payment_ref = f'WALLET-{timezone.now().strftime("%Y%m%d%H%M%S")}'
    service.save()

    # ثبت تراکنش
    Payment.objects.create(
        user=request.user,
        service=service,
        amount=amount,
        status='success',
        payment_date=timezone.now(),
        ref_id=service.payment_ref,
        description='پرداخت از کیف پول'
    )

    # ثبت تراکنش مالی
    from home_module.models import Transaction
    Transaction.objects.create(
        customer=request.user,
        service=service,
        amount=amount,
        transaction_type='payment',
        description=f'پرداخت خدمت: {service.title}'
    )

    return JsonResponse({
        'success': True,
        'new_balance': request.user.wallet_balance,
        'message': 'پرداخت با موفقیت انجام شد'
    })
    
# order_module/views.py (بخش‌های اصلاح‌شده)
# import json
# import logging
# from django.shortcuts import render, redirect, get_object_or_404
# from django.http import HttpResponse, JsonResponse
# from django.contrib.auth.decorators import login_required
# from django.contrib import messages
# from django.urls import reverse
# from django.utils import timezone
# from django.views.decorators.csrf import csrf_exempt
# from .models import Payment, DiscountCode
# from .utils import apply_discount
# from .payment_service import PaymentService
# from .payment_config import PaymentGateway
# from home_module.models import Service

# logger = logging.getLogger(__name__)



# # ============================================
# # ارسال به درگاه پرداخت (اصلاح‌شده)
# # ============================================
# @login_required
# def send_to_gateway(request, service_id):
#     """
#     ارسال به درگاه پرداخت - اتوماتیک تشخیص می‌دهد از کدام درگاه استفاده کند
#     """
#     try:
#         service = Service.objects.get(id=service_id, customer=request.user, is_paid=False)
#     except Service.DoesNotExist:
#         return HttpResponse("سرویس یافت نشد یا قبلاً پرداخت شده", status=404)

#     amount = int(service.final_price or service.price)

#     # ساخت callback URL برای بازگشت از درگاه
#     callback_url = request.build_absolute_uri(
#         reverse('verify_payment') + f'?service_id={service_id}'
#     )

#     # استفاده از سرویس پرداخت یکپارچه
#     payment_service = PaymentService(request)
    
#     result = payment_service.send_to_gateway(
#         amount=amount,
#         callback_url=callback_url,
#         description=f'پرداخت خدمت: {service.title}',
#         service_id=str(service_id),
#         return_url=callback_url,
#     )

#     if result.get('success'):
#         # ذخیره اطلاعات پرداخت
#         payment_data = {
#             'user': request.user,
#             'service': service,
#             'amount': amount,
#             'status': 'pending',
#             'description': f'پرداخت خدمت: {service.title}',
#             'gateway': result.get('gateway'),
#         }
        
#         # برای هر درگاه، شناسه متفاوتی ذخیره می‌شود
#         if result.get('gateway') == 'zarinpal_intermediate':
#             # authority بعداً در callback دریافت می‌شود
#             pass
#         elif result.get('gateway') == 'zibal_direct':
#             payment_data['authority'] = result.get('track_id')
        
#         Payment.objects.create(**payment_data)

#         # ریدایرکت به درگاه (مستقیم یا سایت واسط)
#         return redirect(result['redirect_url'])
#     else:
#         logger.error(f"Payment gateway error: {result.get('error')}")
#         messages.error(request, result.get('error', 'خطا در اتصال به درگاه پرداخت'))
#         return redirect('profile')


# # ============================================
# # وریفای پرداخت (بازگشت از درگاه) - اصلاح‌شده
# # ============================================
# @login_required
# def verify_payment(request):
#     """
#     وریفای پرداخت بعد از بازگشت از درگاه
#     پشتیبانی از هر دو درگاه زرین‌پال و زیبال
#     """
#     payment_service = PaymentService(request)
#     gateway_type = payment_service.gateway_type
    
#     service_id = request.GET.get('service_id')
    
#     if not service_id:
#         messages.error(request, 'اطلاعات پرداخت ناقص است')
#         return redirect('profile')
    
#     try:
#         service = Service.objects.get(id=service_id, customer=request.user)
#     except Service.DoesNotExist:
#         return HttpResponse("سرویس یافت نشد", status=404)
    
#     amount = int(service.final_price or service.price)
    
#     if gateway_type == PaymentGateway.ZARINPAL:
#         return _verify_zarinpal_payment(request, service, amount, payment_service)
#     elif gateway_type == PaymentGateway.ZIBAL:
#         return _verify_zibal_payment(request, service, amount, payment_service)
#     else:
#         messages.error(request, 'درگاه پرداخت نامشخص')
#         return redirect('profile')


# def _verify_zarinpal_payment(request, service, amount, payment_service):
#     """وریفای پرداخت زرین‌پال"""
#     authority = request.GET.get('Authority')
#     status = request.GET.get('Status')
#     ref_id = request.GET.get('ref_id')  # ممکن است از سایت واسط بیاید
    
#     # اگر ref_id از سایت واسط آمده، یعنی پرداخت موفق بوده
#     if ref_id and authority:
#         return _mark_payment_success(service, amount, authority, ref_id)
    
#     # در غیر این صورت، باید وریفای کنیم
#     if not authority or status != 'OK':
#         messages.error(request, 'پرداخت ناموفق بود یا توسط کاربر لغو شد')
#         return redirect('profile')
    
#     # وریفای با زرین‌پال
#     result = payment_service.verify_payment(authority=authority, amount=amount)
    
#     if result.get('data') and result['data'].get('code') == 100:
#         ref_id = result['data'].get('ref_id')
#         return _mark_payment_success(service, amount, authority, ref_id)
#     elif result.get('data') and result['data'].get('code') == 101:
#         messages.info(request, 'این تراکنش قبلاً تأیید شده است')
#         return redirect('profile')
#     else:
#         # پرداخت ناموفق
#         Payment.objects.filter(authority=authority).update(status='failed')
#         messages.error(request, 'پرداخت ناموفق بود')
#         return redirect('profile')


# def _verify_zibal_payment(request, service, amount, payment_service):
#     """وریفای پرداخت زیبال"""
#     track_id = request.GET.get('trackId')
#     status = request.GET.get('success')
    
#     if not track_id or status != '1':
#         messages.error(request, 'پرداخت ناموفق بود یا توسط کاربر لغو شد')
#         return redirect('profile')
    
#     # وریفای با زیبال
#     result = payment_service.verify_payment(track_id=track_id)
    
#     if result.get('result') == 100:
#         ref_id = result.get('refNumber')
#         return _mark_payment_success(service, amount, track_id, ref_id)
#     else:
#         Payment.objects.filter(authority=track_id).update(status='failed')
#         messages.error(request, 'پرداخت ناموفق بود')
#         return redirect('profile')


# def _mark_payment_success(service, amount, authority, ref_id):
#     """علامت‌گذاری پرداخت موفق"""
#     # آپدیت سرویس
#     service.is_paid = True
#     service.payment_date = timezone.now()
#     service.payment_ref = ref_id
#     service.save()
    
#     # آپدیت رکورد پرداخت
#     Payment.objects.filter(authority=authority).update(
#         ref_id=ref_id,
#         status='success',
#         payment_date=timezone.now()
#     )
    
#     return render(request, 'order_module/payment_result.html', {
#         'success': True,
#         'ref_id': ref_id,
#         'amount': amount,
#         'service': service,
#     })


# # ============================================
# # API وریفای از سایت واسط (برای زرین‌پال)
# # ============================================
# @csrf_exempt
# def verify_from_other_site(request):
#     """
#     وریفای پرداخت از سایت واسط (Site B)
#     فقط برای زرین‌پال استفاده می‌شود
#     """
#     if request.method == 'GET':
#         # GET request - redirect with params
#         authority = request.GET.get('authority')
#         ref_id = request.GET.get('ref_id')
#         amount = request.GET.get('amount')
#         article_id = request.GET.get('article_id')  # service_id
        
#         if all([authority, ref_id, amount, article_id]):
#             # ریدایرکت به صفحه وریفای خودمان با پارامترهای موفقیت
#             verify_url = reverse('verify_payment')
#             redirect_url = f"{verify_url}?Authority={authority}&Status=OK&ref_id={ref_id}&service_id={article_id}"
#             return redirect(redirect_url)
#         else:
#             return HttpResponse("پارامترهای ناقص", status=400)
    
#     elif request.method == 'POST':
#         # POST request - API call with secret key
#         try:
#             data = json.loads(request.body)
#             authority = data.get('authority')
#             ref_id = data.get('ref_id')
#             amount = data.get('amount')
#             service_id = data.get('service_id')
#             secret_key = data.get('secret_key')
            
#             # بررسی کلید امنیتی
#             if secret_key != 'YOUR_SECRET_KEY_HERE':
#                 return JsonResponse({'error': 'Unauthorized'}, status=401)
            
#             if not all([authority, ref_id, amount, service_id]):
#                 return JsonResponse({'error': 'Missing parameters'}, status=400)
            
#             service = get_object_or_404(Service, id=service_id)
            
#             # آپدیت سرویس
#             service.is_paid = True
#             service.payment_date = timezone.now()
#             service.payment_ref = ref_id
#             service.save()
            
#             # آپدیت پرداخت
#             Payment.objects.filter(authority=authority).update(
#                 ref_id=ref_id,
#                 status='success',
#                 payment_date=timezone.now()
#             )
            
#             return JsonResponse({'success': True})
            
#         except json.JSONDecodeError:
#             return JsonResponse({'error': 'Invalid JSON'}, status=400)
#         except Exception as e:
#             logger.error(f"Error in verify_from_other_site: {e}")
#             return JsonResponse({'error': str(e)}, status=500)
    
#     else:
#         return JsonResponse({'error': 'Method not allowed'}, status=405)