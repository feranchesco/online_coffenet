from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import models
import json
import os
from home_module.models import Service, Operator, Transaction
from account_module.models import Customer
from order_module.models import Payment
# ============================================
# API: ویرایش پروژه
# ============================================
@require_POST
def api_update_project(request, project_id):
    """ویرایش اطلاعات پروژه"""
    if not is_admin_or_owner(request):
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        data = json.loads(request.body)
        service = Service.objects.get(id=project_id)

        if 'title' in data:
            service.title = data['title']
        if 'description' in data:
            service.description = data['description']
        if 'price' in data:
            service.price = int(data['price'])
            service.final_price = service.price - service.discount_amount
        if 'priority' in data:
            service.priority = data['priority']
        if 'customer_note' in data:
            service.customer_note = data['customer_note']
        if 'operator_note' in data:
            service.operator_note = data['operator_note']

        service.save()

        return JsonResponse({
            'success': True,
            'message': 'پروژه با موفقیت بروزرسانی شد'
        })

    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'پروژه یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# API: دریافت جزئیات یک پروژه
# ============================================
@require_GET
def api_get_project_detail(request, project_id):
    """دریافت جزئیات یک پروژه"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        service = Service.objects.select_related('customer', 'operator').get(id=project_id)

        # دریافت پیام‌های چت
        chat_data = service.chat.read()
        messages = chat_data.get('messages', [])[-50:]  # ۵۰ پیام آخر

        return JsonResponse({
            'id': str(service.id),
            'tracking_code': service.tracking_code,
            'title': service.title,
            'description': service.description,
            'price': service.final_price or service.price,
            'status': service.status,
            'status_display': service.get_status_display(),
            'priority': service.priority,
            'customer': {
                'id': str(service.customer.id),
                'name': service.customer.full_name,
                'phone': service.customer.phone,
            } if service.customer else None,
            'operator': {
                'id': str(service.operator.id),
                'name': service.operator.full_name,
                'phone': service.operator.phone,
            } if service.operator else None,
            'is_paid': service.is_paid,
            'customer_note': service.customer_note,
            'operator_note': service.operator_note,
            'has_file': bool(service.result_file),
            'result_file_name': service.result_file_name,
            'chat_messages': messages,
            'created_at': service.created_at.isoformat(),
            'completed_at': service.completed_at.isoformat() if service.completed_at else None,
        })

    except Service.DoesNotExist:
        return JsonResponse({'error': 'پروژه یافت نشد'}, status=404)


# ============================================
# API: دریافت لیست اپراتورها (برای dropdown)
# ============================================
@require_GET
def api_get_operators_list(request):
    """دریافت لیست ساده اپراتورها"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    operators = Operator.objects.filter(is_active=True).values('id', 'full_name', 'role')

    return JsonResponse({
        'operators': list(operators)
    })
# admin_panel/views.py


# ============================================
# تنظیمات
# ============================================
SITE_OWNERS = ['مهران سبزی', 'دانیال وفادارنژاد', 'ابوالفضل رحمانی']
COMMISSION_RATE = 0.40  # 👈 ۴۰ درصد کمیسیون
MIN_WALLET_BALANCE = 200000  # 👈 حداقل موجودی کیف پول


# ============================================
# دسترسی به پنل ادمین
# ============================================
def is_admin_or_owner(request):
    """بررسی دسترسی به پنل مدیریت"""
    if request.user.is_authenticated and request.user.is_superuser:
        return True

    operator_id = request.session.get('operator_id')
    if operator_id:
        try:
            operator = Operator.objects.get(id=operator_id)
            if operator.role in ['admin', 'owner']:
                return True
        except Operator.DoesNotExist:
            pass

    return False


# ============================================
# صفحه اصلی پنل مدیریت
# ============================================
@ensure_csrf_cookie  # 👈 اطمینان از ارسال CSRF cookie
def admin_dashboard(request):
    """داشبورد مدیریت"""
    if not is_admin_or_owner(request):
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, 'شما دسترسی به این بخش را ندارید')
        return redirect('home')

    total_services = Service.objects.count()
    active_services = Service.objects.filter(status__in=['pending', 'accepted', 'in_progress']).count()
    completed_services = Service.objects.filter(status__in=['completed', 'delivered']).count()
    total_operators = Operator.objects.filter(is_active=True).count()

    context = {
        'total_services': total_services,
        'active_services': active_services,
        'completed_services': completed_services,
        'total_operators': total_operators,
    }

    return render(request, 'admin_panel/dashboard.html', context)


# ============================================
# API: دریافت همه پروژه‌ها
# ============================================
@require_GET
def api_get_projects(request):
    """دریافت لیست همه پروژه‌ها"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    projects = Service.objects.select_related('customer', 'operator').all().order_by('-created_at')

    data = []
    for p in projects:
        price = p.final_price or p.price
        commission = int(price * COMMISSION_RATE)
        is_owner = p.operator and (p.operator.full_name in SITE_OWNERS or p.operator.role == 'owner')

        data.append({
            'id': str(p.id),
            'tracking_code': p.tracking_code,
            'title': p.title,
            'description': p.description or '',
            'price': price,
            'status': p.status,
            'status_display': p.get_status_display(),
            'operator_name': p.operator.full_name if p.operator else None,
            'operator_id': str(p.operator.id) if p.operator else None,
            'customer_name': p.customer.full_name if p.customer else 'نامشخص',
            'customer_id': str(p.customer.id) if p.customer else None,
            'is_paid': p.is_paid,
            'commission': commission,
            'is_owner': is_owner,
            'created_at': p.created_at.isoformat(),
            'completed_at': p.completed_at.isoformat() if p.completed_at else None,
        })

    return JsonResponse({'projects': data, 'total': len(data)})


# ============================================
# API: دریافت اطلاعات اپراتورها
# ============================================
@require_GET
def api_get_operators(request):
    """دریافت لیست اپراتورها با اطلاعات مالی"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    operators = Operator.objects.filter(is_active=True)

    data = []
    for op in operators:
        done_services = Service.objects.filter(operator=op, status__in=['completed', 'delivered'])
        total_earned = done_services.aggregate(total=models.Sum('final_price'))['total'] or 0
        job_count = done_services.count()

        is_owner = op.full_name in SITE_OWNERS or op.role == 'owner'
        commission = 0 if is_owner else int(total_earned * COMMISSION_RATE)
        net_payable = total_earned - commission

        # 👈 فقط اگر بیشتر از حداقل موجودی باشه قابل پرداخت نشون بده
        can_pay = net_payable > MIN_WALLET_BALANCE if not is_owner else False

        # وضعیت پرداخت
        total_paid = Payment.objects.filter(
            service__operator=op,
            status='success'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        data.append({
            'id': str(op.id),
            'name': op.full_name,
            'phone': op.phone,
            'role': op.role,
            'rating': float(op.rating),
            'total_reviews': op.total_reviews,
            'completed_jobs': job_count,
            'total_earned': total_earned,
            'commission': commission,
            'net_payable': net_payable,
            'is_owner': is_owner,
            'is_paid': total_paid >= net_payable if net_payable > 0 else False,
            'total_paid': total_paid,
            'wallet_balance': op.wallet_balance,
            'can_pay': can_pay,  # 👈 آیا قابل پرداخت است؟
        })

    return JsonResponse({'operators': data})


# ============================================
# API: دریافت اطلاعات درآمد
# ============================================
@require_GET
def api_get_revenue(request):
    """دریافت گزارش درآمد"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    all_done = Service.objects.filter(status__in=['completed', 'delivered'])
    total_revenue = all_done.aggregate(total=models.Sum('final_price'))['total'] or 0

    this_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
    monthly_revenue = all_done.filter(completed_at__gte=this_month).aggregate(
        total=models.Sum('final_price')
    )['total'] or 0

    this_year = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0)
    yearly_revenue = all_done.filter(completed_at__gte=this_year).aggregate(
        total=models.Sum('final_price')
    )['total'] or 0

    # محاسبه کمیسیون (فقط از غیر صاحبان)
    non_owner_services = all_done.exclude(
        Q(operator__full_name__in=SITE_OWNERS) | Q(operator__role='owner')
    )

    total_commission = 0
    for service in non_owner_services:
        price = service.final_price or service.price
        total_commission += int(price * COMMISSION_RATE)

    # سهم هر صاحب
    share_per_owner = int(total_commission / 3) if total_commission > 0 else 0

    # درآمد صاحبان
    owners_data = []
    for owner_name in SITE_OWNERS:
        try:
            owner = Operator.objects.get(full_name=owner_name)
            owner_services = all_done.filter(operator=owner)
            owner_revenue = owner_services.aggregate(total=models.Sum('final_price'))['total'] or 0
        except Operator.DoesNotExist:
            owner_revenue = 0

        owners_data.append({
            'name': owner_name,
            'share': share_per_owner,
            'own_revenue': owner_revenue,
            'total': share_per_owner + owner_revenue,
        })

    return JsonResponse({
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'yearly_revenue': yearly_revenue,
        'total_commission': total_commission,
        'actual_commission': total_commission,
        'share_per_owner': share_per_owner,
        'owners': owners_data,
        'commission_rate': int(COMMISSION_RATE * 100),  # 👈 درصد کمیسیون
    })


# ============================================
# API: حذف پروژه
# ============================================
@require_POST
@csrf_exempt  # 👈 برای رفع ارور CSRF (موقت)
def api_delete_project(request, project_id):
    """حذف یک پروژه"""
    if not is_admin_or_owner(request):
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    try:
        service = Service.objects.get(id=project_id)

        # حذف فایل‌ها
        if service.result_file:
            file_path = service.result_file.path
            if os.path.exists(file_path):
                os.remove(file_path)

        # حذف فایل چت
        service_id_clean = str(service.id).replace('-', '')
        chat_file = os.path.join('media', 'chats', f'service_{service_id_clean}.json')
        if os.path.exists(chat_file):
            os.remove(chat_file)

        title = service.title
        service.delete()

        return JsonResponse({'success': True, 'message': f'پروژه "{title}" حذف شد'})

    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'پروژه یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# API: تغییر وضعیت پروژه
# ============================================
@require_POST
def api_update_project_status(request, project_id):
    """تغییر وضعیت پروژه"""
    if not is_admin_or_owner(request):
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        new_status = data.get('status', '')

        if new_status not in ['pending', 'accepted', 'in_progress', 'completed', 'delivered', 'cancelled', 'rejected']:
            return JsonResponse({'success': False, 'error': 'وضعیت نامعتبر'}, status=400)

        service = Service.objects.get(id=project_id)
        service.status = new_status

        if new_status in ['completed', 'delivered']:
            service.completed_at = timezone.now()

        service.save()

        return JsonResponse({
            'success': True,
            'message': f'وضعیت به "{service.get_status_display()}" تغییر کرد'
        })

    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'پروژه یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# API: تخصیص اپراتور
# ============================================
@require_POST
def api_assign_operator(request, project_id):
    """تخصیص اپراتور به پروژه"""
    if not is_admin_or_owner(request):
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        data = json.loads(request.body) if request.body else {}
        operator_id = data.get('operator_id')

        service = Service.objects.get(id=project_id)

        if operator_id:
            operator = Operator.objects.get(id=operator_id)
            service.operator = operator
            if service.status == 'pending':
                service.status = 'accepted'
                service.accepted_at = timezone.now()
        else:
            service.operator = None
            service.status = 'pending'

        service.save()

        return JsonResponse({
            'success': True,
            'message': 'اپراتور با موفقیت تخصیص داده شد'
        })

    except Service.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'پروژه یافت نشد'}, status=404)
    except Operator.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'اپراتور یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================
# API: پرداخت به اپراتور
# ============================================
@require_POST
def api_pay_operator(request, operator_id):
    """
    پرداخت به اپراتور
    - ثبت تراکنش
    - کم کردن از pending_payment
    - حفظ حداقل ۲۰۰ هزار تومان در کیف پول
    """
    if not is_admin_or_owner(request):
        return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        operator = Operator.objects.get(id=operator_id)

        # محاسبه مبلغ قابل پرداخت
        done_services = Service.objects.filter(operator=operator, status__in=['completed', 'delivered'])
        total_earned = done_services.aggregate(total=models.Sum('final_price'))['total'] or 0

        is_owner = operator.full_name in SITE_OWNERS or operator.role == 'owner'
        commission = 0 if is_owner else int(total_earned * COMMISSION_RATE)
        net_payable = total_earned - commission

        # 👈 کم کردن حداقل موجودی
        actual_payment = max(0, net_payable - MIN_WALLET_BALANCE)

        if actual_payment <= 0:
            return JsonResponse({
                'success': False,
                'error': f'مبلغ قابل پرداخت کمتر از حداقل موجودی ({MIN_WALLET_BALANCE:,} تومان) است'
            })

        # ثبت تراکنش
        Transaction.objects.create(
            operator=operator,
            amount=actual_payment,
            transaction_type='operator_pay',
            description=f'پرداخت به {operator.full_name} - {actual_payment:,} تومان',
            is_successful=True
        )

        # 👈 آپدیت کیف پول - فقط مبلغ پرداخت شده کم میشه
        operator.wallet_balance += actual_payment
        operator.pending_payment = net_payable - actual_payment - MIN_WALLET_BALANCE
        operator.save(update_fields=['wallet_balance', 'pending_payment'])

        return JsonResponse({
            'success': True,
            'message': f'پرداخت {actual_payment:,} تومان به {operator.full_name} انجام شد',
            'paid_amount': actual_payment,
            'new_balance': operator.wallet_balance,
            'min_balance_kept': MIN_WALLET_BALANCE,
        })

    except Operator.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'اپراتور یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# views.py - اضافه کردن به انتهای فایل
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from home_module.models import News, HomeService
import json


# ============================================
# API مدیریت اخبار
# ============================================

@ensure_csrf_cookie
def admin_news_list_api(request):
    """لیست تمام اخبار برای پنل ادمین"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    news_list = News.objects.all().order_by('-is_pinned', '-publish_date')

    news_data = []
    for news in news_list:
        news_data.append({
            'id': str(news.id),
            'title': news.title,
            'content': news.content,
            'summary': news.summary or '',
            'icon': news.icon,
            'link': news.link or '',
            'is_active': news.is_active,
            'is_pinned': news.is_pinned,
            'order': news.order,
            'publish_date': news.publish_date.strftime('%Y-%m-%d %H:%M'),
            'expire_date': news.expire_date.strftime('%Y-%m-%d %H:%M') if news.expire_date else None,
            'relative_date': news.get_relative_date(),
        })

    return JsonResponse({
        'success': True,
        'news': news_data
    })


@ensure_csrf_cookie
@require_http_methods(["POST"])
def admin_news_create_api(request):
    """ایجاد خبر جدید"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        data = json.loads(request.body)

        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'عنوان خبر الزامی است'}, status=400)

        news = News.objects.create(
            title=title,
            content=data.get('content', ''),
            summary=data.get('summary', ''),
            icon=data.get('icon', '📰'),
            link=data.get('link', ''),
            is_active=data.get('is_active', True),
            is_pinned=data.get('is_pinned', False),
            order=int(data.get('order', 0)),
            publish_date=data.get('publish_date', timezone.now()),
            expire_date=data.get('expire_date') if data.get('expire_date') else None,
        )

        return JsonResponse({
            'success': True,
            'message': f'خبر "{title}" با موفقیت ایجاد شد',
            'news_id': str(news.id)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'فرمت داده نامعتبر است'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@ensure_csrf_cookie
@require_http_methods(["POST"])
def admin_news_update_api(request, news_id):
    """ویرایش خبر"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        news = News.objects.get(id=news_id)
        data = json.loads(request.body)

        if 'title' in data:
            news.title = data['title'].strip()
        if 'content' in data:
            news.content = data['content']
        if 'summary' in data:
            news.summary = data['summary']
        if 'icon' in data:
            news.icon = data['icon']
        if 'link' in data:
            news.link = data['link']
        if 'is_active' in data:
            news.is_active = data['is_active']
        if 'is_pinned' in data:
            news.is_pinned = data['is_pinned']
        if 'order' in data:
            news.order = int(data['order'])
        if 'publish_date' in data:
            news.publish_date = data['publish_date']
        if 'expire_date' in data:
            news.expire_date = data['expire_date'] if data['expire_date'] else None

        news.save()

        return JsonResponse({
            'success': True,
            'message': f'خبر "{news.title}" با موفقیت بروزرسانی شد'
        })

    except News.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'خبر یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@ensure_csrf_cookie
@require_http_methods(["POST"])
def admin_news_delete_api(request, news_id):
    """حذف خبر"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        news = News.objects.get(id=news_id)
        title = news.title
        news.delete()

        return JsonResponse({
            'success': True,
            'message': f'خبر "{title}" با موفقیت حذف شد'
        })

    except News.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'خبر یافت نشد'}, status=404)


# ============================================
# API مدیریت خدمات صفحه اصلی
# ============================================

@ensure_csrf_cookie
def admin_home_services_list_api(request):
    """لیست خدمات صفحه اصلی برای پنل ادمین"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    services = HomeService.objects.all().order_by('order', '-created_at')

    services_data = []
    for service in services:
        services_data.append({
            'id': str(service.id),
            'icon': service.icon,
            'title': service.title,
            'description': service.description,
            'price': service.price,
            'price_display': service.get_price_display(),
            'is_active': service.is_active,
            'order': service.order,
        })

    return JsonResponse({
        'success': True,
        'services': services_data
    })


@ensure_csrf_cookie
@require_http_methods(["POST"])
def admin_home_service_create_api(request):
    """ایجاد خدمت جدید برای صفحه اصلی"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        data = json.loads(request.body)

        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'success': False, 'error': 'عنوان خدمت الزامی است'}, status=400)

        service = HomeService.objects.create(
            icon=data.get('icon', '📋'),
            title=title,
            description=data.get('description', ''),
            price=int(data.get('price', 0)),
            is_active=data.get('is_active', True),
            order=int(data.get('order', 0)),
        )

        return JsonResponse({
            'success': True,
            'message': f'خدمت "{title}" با موفقیت ایجاد شد',
            'service_id': str(service.id)
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'فرمت داده نامعتبر است'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@ensure_csrf_cookie
@require_http_methods(["POST"])
def admin_home_service_update_api(request, service_id):
    """ویرایش خدمت صفحه اصلی"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        service = HomeService.objects.get(id=service_id)
        data = json.loads(request.body)

        if 'icon' in data:
            service.icon = data['icon']
        if 'title' in data:
            service.title = data['title'].strip()
        if 'description' in data:
            service.description = data['description']
        if 'price' in data:
            service.price = int(data['price'])
        if 'is_active' in data:
            service.is_active = data['is_active']
        if 'order' in data:
            service.order = int(data['order'])

        service.save()

        return JsonResponse({
            'success': True,
            'message': f'خدمت "{service.title}" با موفقیت بروزرسانی شد'
        })

    except HomeService.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'خدمت یافت نشد'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@ensure_csrf_cookie
@require_http_methods(["POST"])
def admin_home_service_delete_api(request, service_id):
    """حذف خدمت صفحه اصلی"""
    if not is_admin_or_owner(request):
        return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)

    try:
        service = HomeService.objects.get(id=service_id)
        title = service.title
        service.delete()

        return JsonResponse({
            'success': True,
            'message': f'خدمت "{title}" با موفقیت حذف شد'
        })

    except HomeService.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'خدمت یافت نشد'}, status=404)
#
# # ============================================
# # دسترسی به پنل ادمین
# # ============================================
# def is_admin(user):
#     """بررسی اینکه کاربر ادمین است"""
#     # مشتری که superuser باشه
#     if user.is_authenticated and user.is_superuser:
#         return True
#
#     # اپراتور با role admin یا owner
#     operator_id = getattr(user, 'session', {}).get('operator_id')
#     if not operator_id:
#         # چک کردن از session (برای اپراتورها)
#         from django.contrib.sessions.models import Session
#         # اینجا باید session رو چک کنیم
#
#     return False
#
#
# def is_admin_or_owner(request):
#     """بررسی دسترسی به پنل مدیریت"""
#     # چک کردن superuser
#     if request.user.is_authenticated and request.user.is_superuser:
#         return True
#
#     # چک کردن اپراتور owner/admin از session
#     operator_id = request.session.get('operator_id')
#     if operator_id:
#         try:
#             operator = Operator.objects.get(id=operator_id)
#             if operator.role in ['admin', 'owner']:
#                 return True
#         except Operator.DoesNotExist:
#             pass
#
#     return False
#
#
# # ============================================
# # صفحه اصلی پنل مدیریت
# # ============================================
# def admin_dashboard(request):
#     """داشبورد مدیریت"""
#     if not is_admin_or_owner(request):
#         from django.contrib import messages
#         messages.error(request, 'شما دسترسی به این بخش را ندارید')
#         from django.shortcuts import redirect
#         return redirect('home')
#
#     # آمار کلی
#     total_services = Service.objects.count()
#     active_services = Service.objects.filter(status__in=['pending', 'accepted', 'in_progress']).count()
#     completed_services = Service.objects.filter(status__in=['completed', 'delivered']).count()
#     total_operators = Operator.objects.filter(is_active=True).count()
#
#     context = {
#         'total_services': total_services,
#         'active_services': active_services,
#         'completed_services': completed_services,
#         'total_operators': total_operators,
#     }
#
#     return render(request, 'admin_panel/dashboard.html', context)
#
#
# # ============================================
# # API: دریافت همه پروژه‌ها
# # ============================================
# @require_GET
# def api_get_projects(request):
#     """دریافت لیست همه پروژه‌ها"""
#     if not is_admin_or_owner(request):
#         return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)
#
#     projects = Service.objects.select_related('customer', 'operator').all().order_by('-created_at')
#
#     data = []
#     for p in projects:
#         commission = int((p.final_price or p.price) * p.commission_percent / 100)
#         is_owner = p.operator and p.operator.role == 'owner'
#
#         data.append({
#             'id': str(p.id),
#             'tracking_code': p.tracking_code,
#             'title': p.title,
#             'description': p.description or '',
#             'price': p.final_price or p.price,
#             'status': p.status,
#             'status_display': p.get_status_display(),
#             'operator_name': p.operator.full_name if p.operator else None,
#             'operator_id': str(p.operator.id) if p.operator else None,
#             'customer_name': p.customer.full_name if p.customer else 'نامشخص',
#             'customer_id': str(p.customer.id) if p.customer else None,
#             'is_paid': p.is_paid,
#             'commission': commission,
#             'is_owner': is_owner,
#             'created_at': p.created_at.isoformat(),
#             'completed_at': p.completed_at.isoformat() if p.completed_at else None,
#         })
#
#     return JsonResponse({'projects': data, 'total': len(data)})
#
#
# # ============================================
# # API: دریافت اطلاعات اپراتورها
# # ============================================
# @require_GET
# def api_get_operators(request):
#     """دریافت لیست اپراتورها با اطلاعات مالی"""
#     if not is_admin_or_owner(request):
#         return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)
#
#     SITE_OWNERS = ['مهران سبزی', 'دانیال وفادارنژاد', 'ابوالفضل رحمانی']
#     COMMISSION_RATE = 0.20
#
#     operators = Operator.objects.filter(is_active=True)
#
#     data = []
#     for op in operators:
#         # محاسبه درآمد
#         done_services = Service.objects.filter(operator=op, status__in=['completed', 'delivered'])
#         total_earned = done_services.aggregate(total=Sum('final_price'))['total'] or 0
#         job_count = done_services.count()
#
#         # محاسبه کمیسیون
#         commission = int(total_earned * COMMISSION_RATE) if not SITE_OWNERS.count(op.full_name) > 0 else 0
#         net_payable = total_earned - commission
#
#         is_owner = op.full_name in SITE_OWNERS or op.role == 'owner'
#
#         # وضعیت پرداخت
#         total_paid = Payment.objects.filter(
#             service__operator=op,
#             status='success'
#         ).aggregate(total=Sum('amount'))['total'] or 0
#
#         data.append({
#             'id': str(op.id),
#             'name': op.full_name,
#             'phone': op.phone,
#             'role': op.role,
#             'rating': float(op.rating),
#             'total_reviews': op.total_reviews,
#             'completed_jobs': job_count,
#             'total_earned': total_earned,
#             'commission': commission,
#             'net_payable': net_payable,
#             'is_owner': is_owner,
#             'is_paid': total_paid >= net_payable if net_payable > 0 else False,
#             'total_paid': total_paid,
#         })
#
#     return JsonResponse({'operators': data})
#
#
# # ============================================
# # API: دریافت اطلاعات درآمد
# # ============================================
# @require_GET
# def api_get_revenue(request):
#     """دریافت گزارش درآمد"""
#     if not is_admin_or_owner(request):
#         return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)
#
#     SITE_OWNERS = ['مهران سبزی', 'دانیال وفادارنژاد', 'ابوالفضل رحمانی']
#     COMMISSION_RATE = 0.20
#
#     # کل درآمد
#     all_done = Service.objects.filter(status__in=['completed', 'delivered'])
#     total_revenue = all_done.aggregate(total=Sum('final_price'))['total'] or 0
#
#     # درآمد ماهانه
#     this_month = timezone.now().replace(day=1, hour=0, minute=0, second=0)
#     monthly_revenue = all_done.filter(completed_at__gte=this_month).aggregate(
#         total=Sum('final_price')
#     )['total'] or 0
#
#     # درآمد سالانه
#     this_year = timezone.now().replace(month=1, day=1, hour=0, minute=0, second=0)
#     yearly_revenue = all_done.filter(completed_at__gte=this_year).aggregate(
#         total=Sum('final_price')
#     )['total'] or 0
#
#     # محاسبه کمیسیون
#     non_owner_services = all_done.exclude(operator__full_name__in=SITE_OWNERS)
#     total_commission = non_owner_services.aggregate(
#         total=models.Sum(models.F('final_price') * COMMISSION_RATE)
#     )['total'] or 0
#
#     # سهم هر صاحب
#     share_per_owner = int(total_commission / 3)
#
#     # درآمد صاحبان
#     owners_data = []
#     for owner_name in SITE_OWNERS:
#         try:
#             owner = Operator.objects.get(full_name=owner_name)
#             owner_services = all_done.filter(operator=owner)
#             owner_revenue = owner_services.aggregate(total=Sum('final_price'))['total'] or 0
#         except Operator.DoesNotExist:
#             owner_revenue = 0
#
#         owners_data.append({
#             'name': owner_name,
#             'share': share_per_owner,
#             'own_revenue': owner_revenue,
#             'total': share_per_owner + owner_revenue,
#         })
#
#     return JsonResponse({
#         'total_revenue': total_revenue,
#         'monthly_revenue': monthly_revenue,
#         'yearly_revenue': yearly_revenue,
#         'total_commission': int(total_commission),
#         'actual_commission': int(total_commission),
#         'share_per_owner': share_per_owner,
#         'owners': owners_data,
#     })
#
#
# # ============================================
# # API: حذف پروژه
# # ============================================
# @require_POST
# def api_delete_project(request, project_id):
#     """حذف یک پروژه"""
#     if not is_admin_or_owner(request):
#         return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)
#
#     try:
#         service = Service.objects.get(id=project_id)
#
#         # حذف فایل‌ها
#         if service.result_file:
#             import os
#             file_path = service.result_file.path
#             if os.path.exists(file_path):
#                 os.remove(file_path)
#
#         # حذف فایل چت
#         service_id_clean = str(service.id).replace('-', '')
#         chat_file = os.path.join('media', 'chats', f'service_{service_id_clean}.json')
#         if os.path.exists(chat_file):
#             os.remove(chat_file)
#
#         title = service.title
#         service.delete()
#
#         return JsonResponse({'success': True, 'message': f'پروژه "{title}" حذف شد'})
#
#     except Service.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'پروژه یافت نشد'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)
#
#
# # ============================================
# # API: تغییر وضعیت پروژه
# # ============================================
# @require_POST
# def api_update_project_status(request, project_id):
#     """تغییر وضعیت پروژه"""
#     if not is_admin_or_owner(request):
#         return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)
#
#     try:
#         data = json.loads(request.body)
#         new_status = data.get('status')
#
#         if new_status not in ['pending', 'accepted', 'in_progress', 'completed', 'delivered', 'cancelled', 'rejected']:
#             return JsonResponse({'success': False, 'error': 'وضعیت نامعتبر'}, status=400)
#
#         service = Service.objects.get(id=project_id)
#         old_status = service.status
#         service.status = new_status
#
#         if new_status in ['completed', 'delivered']:
#             service.completed_at = timezone.now()
#
#         service.save()
#
#         return JsonResponse({
#             'success': True,
#             'message': f'وضعیت از "{old_status}" به "{new_status}" تغییر کرد'
#         })
#
#     except Service.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'پروژه یافت نشد'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)
#
#
# # ============================================
# # API: تخصیص اپراتور به پروژه
# # ============================================
# @require_POST
# def api_assign_operator(request, project_id):
#     """تخصیص اپراتور به پروژه"""
#     if not is_admin_or_owner(request):
#         return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)
#
#     try:
#         data = json.loads(request.body)
#         operator_id = data.get('operator_id')
#
#         service = Service.objects.get(id=project_id)
#
#         if operator_id:
#             operator = Operator.objects.get(id=operator_id)
#             service.operator = operator
#             if service.status == 'pending':
#                 service.status = 'accepted'
#                 service.accepted_at = timezone.now()
#         else:
#             service.operator = None
#             service.status = 'pending'
#
#         service.save()
#
#         return JsonResponse({
#             'success': True,
#             'message': f'اپراتور با موفقیت تخصیص داده شد'
#         })
#
#     except Service.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'پروژه یافت نشد'}, status=404)
#     except Operator.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'اپراتور یافت نشد'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)
#
#
# # ============================================
# # API: پرداخت به اپراتور
# # ============================================
# @require_POST
# def api_pay_operator(request, operator_id):
#     """پرداخت به اپراتور"""
#     if not is_admin_or_owner(request):
#         return JsonResponse({'success': False, 'error': 'دسترسی غیرمجاز'}, status=403)
#
#     try:
#         operator = Operator.objects.get(id=operator_id)
#
#         # محاسبه مبلغ قابل پرداخت
#         SITE_OWNERS = ['مهران سبزی', 'دانیال وفادارنژاد', 'ابوالفضل رحمانی']
#         COMMISSION_RATE = 0.20
#
#         done_services = Service.objects.filter(operator=operator, status__in=['completed', 'delivered'])
#         total_earned = done_services.aggregate(total=Sum('final_price'))['total'] or 0
#
#         is_owner = operator.full_name in SITE_OWNERS or operator.role == 'owner'
#         commission = 0 if is_owner else int(total_earned * COMMISSION_RATE)
#         net_payable = total_earned - commission
#
#         # ثبت تراکنش پرداخت
#         Transaction.objects.create(
#             operator=operator,
#             amount=net_payable,
#             transaction_type='operator_pay',
#             description=f'پرداخت تسویه حساب به {operator.full_name}',
#             is_successful=True
#         )
#
#         # ریست کردن pending payment
#         operator.pending_payment = 0
#         operator.save(update_fields=['pending_payment'])
#
#         return JsonResponse({
#             'success': True,
#             'message': f'پرداخت {net_payable:,} تومان به {operator.full_name} انجام شد'
#         })
#
#     except Operator.DoesNotExist:
#         return JsonResponse({'success': False, 'error': 'اپراتور یافت نشد'}, status=404)
#     except Exception as e:
#         return JsonResponse({'success': False, 'error': str(e)}, status=500)
#