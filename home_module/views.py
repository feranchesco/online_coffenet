# home_module/views.py
from django.utils import timezone
from .models import Service, HomeService
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from .models import Transaction

def home(request):
    """صفحه اصلی سایت"""
    home_services = HomeService.objects.filter(is_active=True).order_by('order')

    context = {
        'home_services': home_services,
    }

    return render(request, 'home_module/home.html', context)


def get_home_services_api(request):
    """API برای دریافت خدمات صفحه اصلی"""
    services = HomeService.objects.filter(is_active=True).order_by('order')

    data = [
        {
            'id': str(s.id),
            'icon': s.icon,
            'title': s.title,
            'description': s.description,
            'price': s.price,
            'price_display': s.get_price_display(),
        }
        for s in services
    ]

    return JsonResponse({'services': data})


@login_required
@require_POST
def create_service(request):
    """
    ایجاد سرویس جدید توسط مشتری از صفحه اصلی
    """
    try:
        data = json.loads(request.body)

        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        price = int(data.get('price', 0))
        priority = data.get('priority', 'medium')

        if not title:
            return JsonResponse({
                'success': False,
                'error': 'عنوان خدمت الزامی است'
            }, status=400)

        if price < 0:
            return JsonResponse({
                'success': False,
                'error': 'قیمت نمی‌تواند منفی باشد'
            }, status=400)

        service = Service.objects.create(
            customer=request.user,
            title=title,
            description=description,
            customer_note=data.get('note', ''),
            price=price,
            priority=priority,
        )

        return JsonResponse({
            'success': True,
            'service_id': str(service.id),
            'tracking_code': service.tracking_code,
            'message': f'خدمت "{title}" با موفقیت ثبت شد.'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'فرمت داده نامعتبر است'
        }, status=400)
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'مقدار نامعتبر: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'خطای سیستمی: {str(e)}'
        }, status=500)


# ============================================
# API های پنل مشتری
# ============================================
# @login_required
# @require_POST
# def create_service(request):
#     """ایجاد سرویس جدید توسط مشتری"""
#     try:
#         data = json.loads(request.body)
#
#         service = Service.objects.create(
#             customer=request.user,
#             title=data.get('title'),
#             description=data.get('description', ''),
#             customer_note=data.get('note', ''),
#             price=int(data.get('price', 0)),
#             priority=data.get('priority', 'medium'),
#         )
#
#         return JsonResponse({
#             'success': True,
#             'service_id': str(service.id),
#             'tracking_code': service.tracking_code,
#         })
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=400)


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

