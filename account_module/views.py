from django.shortcuts import render
# account_module/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
import json

from .models import Customer
from home_module.models import Service, Operator, Transaction


# Create your views here.
def signup(request):
    return None


# ============================================
# احراز هویت
# ============================================
def customer_login(request):
    """ورود مشتری"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        user = authenticate(request, username=phone, password=password)
        if user is not None:
            login(request, user)
            return redirect('customer_panel')
        else:
            messages.error(request, 'شماره تلفن یا رمز عبور اشتباه است')

    return render(request, 'account_module/login.html')


def customer_register(request):
    """ثبت‌نام مشتری"""
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if Customer.objects.filter(phone=phone).exists():
            messages.error(request, 'این شماره تلفن قبلاً ثبت شده است')
        else:
            user = Customer.objects.create_user(
                phone=phone,
                password=password,
                full_name=full_name,
                username=phone
            )
            login(request, user)
            return redirect('customer_panel')

    return render(request, 'account_module/register.html')


def customer_logout(request):
    """خروج مشتری"""
    logout(request)
    return redirect('home')


# ============================================
# پنل مشتری
# ============================================
# @login_required
# def customer_panel(request):
#     """
#     پنل اصلی مشتری
#     نمایش همه سرویس‌ها با وضعیت‌های مختلف
#     """
#     customer = request.user
#
#     # دریافت همه سرویس‌های مشتری
#     services = Service.objects.filter(customer=customer).order_by('-created_at')
#
#     # آماده‌سازی داده‌ها برای template
#     services_data = []
#     for service in services:
#         # دریافت اطلاعات چت
#         chat_data = service.chat.read()
#         unread_count = service.chat.get_unread_count('customer')
#         last_message = service.chat.get_last_message()
#
#         services_data.append({
#             'id': str(service.id),
#             'tracking_code': service.tracking_code,
#             'title': service.title,
#             'description': service.description,
#             'status': service.status,
#             'status_display': service.get_status_display(),
#             'status_color': service.get_status_display_color(),
#             'priority': service.priority,
#             'price': service.price,
#             'final_price': service.final_price or service.price,
#             'is_paid': service.is_paid,
#             'operator_name': service.operator.full_name if service.operator else None,
#             'operator_role': service.operator.get_role_display() if service.operator else None,
#             'has_file': bool(service.result_file),
#             'result_file_url': service.result_file.url if service.result_file else None,
#             'result_file_name': service.result_file_name,
#             'unread_count': unread_count,
#             'last_message': last_message['content'][:50] if last_message else None,
#             'last_message_time': last_message['timestamp'] if last_message else None,
#             'created_at': service.created_at,
#         })
#
#     context = {
#         'customer': customer,
#         'services': services_data,
#         'wallet_balance': customer.wallet_balance,
#         'active_services': [s for s in services_data if s['status'] in ['pending', 'accepted', 'in_progress']],
#         'completed_services': [s for s in services_data if s['status'] in ['completed', 'delivered']],
#         'history_services': [s for s in services_data if s['status'] in ['delivered', 'cancelled', 'rejected']],
#     }
#
#     return render(request, 'account_module/customer_panel.html', context)


# ============================================
# API های پنل مشتری
# ============================================
@login_required
@require_POST
def create_service(request):
    """ایجاد سرویس جدید توسط مشتری"""
    try:
        data = json.loads(request.body)

        service = Service.objects.create(
            customer=request.user,
            title=data.get('title'),
            description=data.get('description', ''),
            customer_note=data.get('note', ''),
            price=int(data.get('price', 0)),
            priority=data.get('priority', 'medium'),
        )

        return JsonResponse({
            'success': True,
            'service_id': str(service.id),
            'tracking_code': service.tracking_code,
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def pay_service(request, service_id):
    """پرداخت هزینه سرویس"""
    service = get_object_or_404(Service, id=service_id, customer=request.user)

    if service.is_paid:
        return JsonResponse({'success': False, 'error': 'قبلاً پرداخت شده'}, status=400)

    # بررسی موجودی کیف پول
    amount = service.final_price or service.price
    if request.user.wallet_balance < amount:
        return JsonResponse({'success': False, 'error': 'موجودی کافی نیست'}, status=400)

    # کسر از کیف پول
    request.user.wallet_balance -= amount
    request.user.save(update_fields=['wallet_balance'])

    # ثبت تراکنش
    Transaction.objects.create(
        customer=request.user,
        service=service,
        amount=amount,
        transaction_type='payment',
        description=f'پرداخت خدمت: {service.title}'
    )

    # آپدیت سرویس
    service.is_paid = True
    service.payment_date = timezone.now()
    service.save(update_fields=['is_paid', 'payment_date'])

    return JsonResponse({
        'success': True,
        'new_balance': request.user.wallet_balance,
    })


@login_required
def download_result(request, service_id):
    """دانلود فایل نتیجه"""
    service = get_object_or_404(Service, id=service_id, customer=request.user)

    if not service.result_file:
        return JsonResponse({'success': False, 'error': 'فایلی آپلود نشده'}, status=404)

    if not service.is_paid:
        return JsonResponse({'success': False, 'error': 'ابتدا باید پرداخت کنید'}, status=403)

    from django.http import FileResponse
    return FileResponse(
        service.result_file.open('rb'),
        as_attachment=True,
        filename=service.result_file_name or 'result.pdf'
    )


@login_required
def rate_service(request, service_id):
    """امتیازدهی به سرویس"""
    if request.method != 'POST':
        return JsonResponse({'success': False}, status=405)

    service = get_object_or_404(Service, id=service_id, customer=request.user)

    try:
        data = json.loads(request.body)
        rating = int(data.get('rating', 0))
        review = data.get('review', '')

        if rating < 1 or rating > 5:
            return JsonResponse({'success': False, 'error': 'امتیاز باید بین ۱ تا ۵ باشد'}, status=400)

        service.rating = rating
        service.review = review
        service.save(update_fields=['rating', 'review'])

        # آپدیت امتیاز اپراتور
        if service.operator:
            service.operator.total_reviews += 1
            all_ratings = Service.objects.filter(
                operator=service.operator,
                rating__isnull=False
            ).values_list('rating', flat=True)
            service.operator.rating = sum(all_ratings) / len(all_ratings)
            service.operator.save(update_fields=['rating', 'total_reviews'])

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def profile(request):
    """
        پنل اصلی مشتری
        نمایش همه سرویس‌ها با وضعیت‌های مختلف
        """
    customer = request.user

    # دریافت همه سرویس‌های مشتری
    services = Service.objects.filter(customer=customer).order_by('-created_at')

    # آماده‌سازی داده‌ها برای template
    services_data = []
    for service in services:
        # دریافت اطلاعات چت
        chat_data = service.chat.read()
        unread_count = service.chat.get_unread_count('customer')
        last_message = service.chat.get_last_message()

        services_data.append({
            'id': str(service.id),
            'tracking_code': service.tracking_code,
            'title': service.title,
            'description': service.description,
            'status': service.status,
            'status_display': service.get_status_display(),
            'status_color': service.get_status_display_color(),
            'priority': service.priority,
            'price': service.price,
            'final_price': service.final_price or service.price,
            'is_paid': service.is_paid,
            'operator_name': service.operator.full_name if service.operator else None,
            'operator_role': service.operator.get_role_display() if service.operator else None,
            'has_file': bool(service.result_file),
            'result_file_url': service.result_file.url if service.result_file else None,
            'result_file_name': service.result_file_name,
            'unread_count': unread_count,
            'last_message': last_message['content'][:50] if last_message else None,
            'last_message_time': last_message['timestamp'] if last_message else None,
            'created_at': service.created_at,
        })

    context = {
        'customer': customer,
        'services': services_data,
        'wallet_balance': customer.wallet_balance,
        'active_services': [s for s in services_data if s['status'] in ['pending', 'accepted', 'in_progress']],
        'completed_services': [s for s in services_data if s['status'] in ['completed', 'delivered']],
        'history_services': [s for s in services_data if s['status'] in ['delivered', 'cancelled', 'rejected']],
    }
    return render(request, 'account_module/profile.html', context)
