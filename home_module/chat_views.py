# home_module/chat_views.py

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
import json
from .models import Service
from account_module.models import Customer, Operator


def get_user_type(user):
    """تشخیص نوع کاربر"""
    if isinstance(user, Customer):
        return 'customer'
    elif isinstance(user, Operator):
        return 'operator'
    return None


def has_chat_access(user, service):
    """بررسی دسترسی کاربر به چت"""
    user_type = get_user_type(user)
    if user_type == 'customer':
        return user == service.customer
    elif user_type == 'operator':
        return user == service.operator
    return False


@login_required
@require_GET
def get_messages(request, service_id):
    """دریافت پیام‌های چت"""
    service = get_object_or_404(Service, id=service_id)

    if not has_chat_access(request.user, service):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    page = int(request.GET.get('page', 1))
    user_type = get_user_type(request.user)

    messages = service.chat.get_messages(
        page=page,
        page_size=50,
        user_type=user_type
    )

    return JsonResponse(messages)


@login_required
@require_POST
def send_message(request, service_id):
    """ارسال پیام جدید"""
    service = get_object_or_404(Service, id=service_id)

    if not has_chat_access(request.user, service):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    if service.status in ['completed', 'delivered', 'cancelled']:
        return JsonResponse({'error': 'این سرویس به پایان رسیده'}, status=400)

    try:
        data = json.loads(request.body)
        content = data.get('content', '').strip()

        if not content:
            return JsonResponse({'error': 'متن پیام الزامی است'}, status=400)

        user_type = get_user_type(request.user)
        sender_name = request.user.full_name or request.user.phone

        message = service.chat.add_message(
            sender_id=str(request.user.id),
            sender_name=sender_name,
            sender_type=user_type,
            content=content
        )

        return JsonResponse({
            'success': True,
            'message': message
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'فرمت داده نامعتبر'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def mark_as_read(request, service_id):
    """علامت‌گذاری پیام‌ها به عنوان خوانده شده"""
    service = get_object_or_404(Service, id=service_id)

    if not has_chat_access(request.user, service):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    user_type = get_user_type(request.user)
    service.chat.mark_as_read(user_type)

    return JsonResponse({'success': True})


@login_required
@require_GET
def get_unread_count(request):
    """دریافت تعداد پیام‌های خوانده نشده"""
    user = request.user
    user_type = get_user_type(user)

    if user_type == 'customer':
        services = Service.objects.filter(customer=user)
    else:
        services = Service.objects.filter(operator=user)

    total_unread = 0
    services_unread = {}

    for service in services:
        count = service.chat.get_unread_count(user_type)
        if count > 0:
            total_unread += count
            services_unread[str(service.id)] = count

    return JsonResponse({
        'total_unread': total_unread,
        'services': services_unread
    })


@login_required
@require_GET
def get_chat_list(request):
    """لیست چت‌های کاربر"""
    user = request.user
    user_type = get_user_type(user)

    if user_type == 'customer':
        services = Service.objects.filter(customer=user)
    else:
        services = Service.objects.filter(operator=user)

    chat_list = []
    for service in services:
        last_msg = service.chat.get_last_message()
        unread = service.chat.get_unread_count(user_type)

        chat_list.append({
            'service_id': str(service.id),
            'tracking_code': service.tracking_code,
            'title': service.title,
            'status': service.status,
            'unread_count': unread,
            'last_message': last_msg['content'][:100] if last_msg else None,
            'last_message_time': last_msg['timestamp'] if last_msg else None,
            'last_message_sender': last_msg['sender_name'] if last_msg else None,
        })

    chat_list.sort(key=lambda x: x['last_message_time'] or '', reverse=True)

    return JsonResponse({'chats': chat_list})