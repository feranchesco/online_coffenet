# home_module/views.py
from django.utils import timezone
from .models import Service, HomeService
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json
from .models import Transaction, News
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.db import models
# services_module/views.py - به viewهای موجود اضافه کن
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from account_module.models import Customer
from .models import ChatSession, ChatMessage, Service
import json
import requests
from datetime import datetime
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


from .models import News


@require_GET
def news_list_api(request):
    """API برای دریافت لیست اخبار فعال"""
    now = timezone.now()

    # فیلتر اخبار فعال و منقضی نشده
    news_queryset = News.objects.filter(
        is_active=True
    ).filter(
        models.Q(expire_date__isnull=True) | models.Q(expire_date__gt=now)
    ).order_by('-is_pinned', '-publish_date')[:10]  # محدود به ۱۰ خبر آخر

    news_data = []
    for news in news_queryset:
        news_data.append({
            'id': str(news.id),
            'title': news.title,
            'summary': news.summary or news.content[:150],
            'icon': news.icon,
            'link': news.link,
            'date': news.get_relative_date(),
            'is_pinned': news.is_pinned,
            'image': news.image.url if news.image else None,
        })

    return JsonResponse({
        'success': True,
        'news': news_data,
        'count': len(news_data)
    })





@login_required
def ai_chat_page(request):
    """
    صفحه اصلی چت بات با اطلاعات کاربر
    """
    customer = request.user

    # دریافت اطلاعات کاربر از دیتابیس
    context = {
        'customer': {
            'id': str(customer.id),
            'full_name': customer.full_name,
            'phone': customer.phone,
            'wallet_balance': customer.wallet_balance,
            'email': customer.email or '',
        },
        # اطلاعات اضافی از سرویس‌ها
        'active_services_count': Service.objects.filter(
            customer=customer,
            status__in=['pending', 'accepted', 'in_progress']
        ).count(),
        'completed_services_count': Service.objects.filter(
            customer=customer,
            status__in=['completed', 'delivered']
        ).count(),
        'total_spent': sum(
            s.final_price or 0
            for s in Service.objects.filter(
                customer=customer,
                is_paid=True
            )
        ),
        # دریافت چت‌های قبلی
        'previous_chats': ChatSession.objects.filter(
            customer=customer,
            is_active=True
        ).order_by('-updated_at')[:10],
    }

    return render(request, 'services_module/ai_chat.html', context)


@login_required
@csrf_exempt
@require_POST
def ai_chat_api(request):
    """
    API ارسال و دریافت پیام از هوش مصنوعی
    """
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id', None)

        if not message:
            return JsonResponse({'error': 'پیام نمی‌تواند خالی باشد'}, status=400)

        customer = request.user

        # دریافت یا ایجاد جلسه چت
        if session_id:
            session = ChatSession.objects.get(
                id=session_id,
                customer=customer
            )
        else:
            # ایجاد جلسه جدید
            session = ChatSession.objects.create(
                customer=customer,
                title=message[:50] + '...' if len(message) > 50 else message
            )

        # ذخیره پیام کاربر
        user_msg = ChatMessage.objects.create(
            session=session,
            role='user',
            content=message
        )

        # آماده‌سازی تاریخچه برای API
        conversation_history = build_conversation_context(customer, session)

        # ارسال به API
        response = requests.post(
            'https://api.gapgpt.app/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {settings.GAPGPT_API_KEY}'
            },
            json={
                'model': 'gpt-4o-mini',
                'messages': conversation_history,
                'temperature': 0.7,
                'max_tokens': 2000
            },
            timeout=30
        )

        if response.status_code == 200:
            ai_response = response.json()
            bot_reply = ai_response['choices'][0]['message']['content']

            # تخمین توکن مصرفی
            tokens_used = ai_response.get('usage', {}).get('total_tokens', 0)
            cost = (tokens_used / 1000) * 0.00015  # هزینه gpt-4o-mini

            # ذخیره پاسخ
            bot_msg = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=bot_reply,
                tokens_used=tokens_used,
                cost=cost
            )

            # بروزرسانی آمار جلسه
            session.total_messages += 2
            session.total_tokens += tokens_used
            session.save()

            return JsonResponse({
                'success': True,
                'session_id': str(session.id),
                'message': {
                    'id': str(bot_msg.id),
                    'content': bot_reply,
                    'role': 'assistant',
                    'timestamp': bot_msg.created_at.strftime('%H:%M'),
                },
                'tokens_used': tokens_used,
                'cost': round(cost, 6)
            })
        else:
            error_data = response.json()
            return JsonResponse({
                'error': error_data.get('error', {}).get('message', 'خطای نامشخص')
            }, status=500)

    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'جلسه چت یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def build_conversation_context(customer, session):
    """
    ساخت تاریخچه مکالمه با اطلاعات کاربر
    """
    # پیام سیستمی با اطلاعات کاربر
    system_prompt = f"""شما یک دستیار هوشمند و دوستانه هستید که در سایت خدمات کافی‌نت فعالیت می‌کنید.

اطلاعات کاربر فعلی:
- نام: {customer.full_name}
- شماره تماس: {customer.phone}
- موجودی کیف پول: {customer.wallet_balance:,} تومان
- تعداد خدمات فعال: {Service.objects.filter(customer=customer, status__in=['pending', 'accepted', 'in_progress']).count()}
- تعداد خدمات تکمیل شده: {Service.objects.filter(customer=customer, status__in=['completed', 'delivered']).count()}

خدمات فعال کاربر:
{chr(10).join([f'- {s.title} (وضعیت: {s.get_status_display()}, کد پیگیری: {s.tracking_code})' for s in Service.objects.filter(customer=customer, status__in=['pending', 'accepted', 'in_progress'])[:5]])}

لطفاً:
1. همیشه به فارسی و با لحن گرم و صمیمی پاسخ دهید
2. از نام کاربر ({customer.full_name}) در پاسخ‌ها استفاده کنید
3. اگر کاربر درباره خدماتش سوال کرد، از اطلاعات فوق استفاده کنید
4. پاسخ‌ها را مختصر و مفید ارائه دهید
5. اگر کاربر مشکل یا سوال خاصی داشت، راهنمایی دقیق کنید
6. می‌توانید کاربر را برای خدمات جدید راهنمایی کنید"""

    messages = [{"role": "system", "content": system_prompt}]

    # اضافه کردن ۱۰ پیام آخر تاریخچه
    history = session.messages.order_by('-created_at')[:10]
    for msg in reversed(history):
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    return messages


@login_required
def get_chat_history(request, session_id):
    """
    دریافت تاریخچه یک چت
    """
    try:
        session = ChatSession.objects.get(
            id=session_id,
            customer=request.user
        )

        messages = session.messages.all().values(
            'id', 'role', 'content', 'created_at'
        )

        return JsonResponse({
            'success': True,
            'session': {
                'id': str(session.id),
                'title': session.title,
                'created_at': session.created_at.strftime('%Y/%m/%d %H:%M'),
            },
            'messages': [
                {
                    'id': str(m['id']),
                    'role': m['role'],
                    'content': m['content'],
                    'timestamp': m['created_at'].strftime('%H:%M'),
                }
                for m in messages
            ]
        })

    except ChatSession.DoesNotExist:
        return JsonResponse({'error': 'جلسه چت یافت نشد'}, status=404)