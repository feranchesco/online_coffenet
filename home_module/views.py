# home_module/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from account_module import models
from .models import Service, Operator
from .models import Service, HomeService
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import json
from django.db.models import Q

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


# home_module/views.py (اضافه کردن)

# ============================================
# پنل اپراتور
# ============================================
def operator_login(request):
    """ورود اپراتور"""
    if request.method == 'POST':
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        try:
            operator = Operator.objects.get(phone=phone)
            if operator.check_password(password):
                # ذخیره در session
                request.session['operator_id'] = str(operator.id)
                request.session['operator_name'] = operator.full_name
                return redirect('operator_panel')
        except Operator.DoesNotExist:
            pass

        from django.contrib import messages
        messages.error(request, 'شماره تلفن یا رمز عبور اشتباه است')

    return render(request, 'home_module/operator_login.html')


def operator_logout(request):
    """خروج اپراتور"""
    request.session.pop('operator_id', None)
    request.session.pop('operator_name', None)
    return redirect('home')


def get_operator(request):
    """دریافت اپراتور از session"""
    operator_id = request.session.get('operator_id')
    if operator_id:
        try:
            return Operator.objects.get(id=operator_id)
        except Operator.DoesNotExist:
            pass
    return None

def operator_panel(request):
    """پنل اصلی اپراتور"""
    operator = get_operator(request)
    if not operator:
        from django.contrib import messages
        messages.error(request, 'لطفاً ابتدا وارد شوید')
        return redirect('operator_login')

    # ✅ اصلاح شده - استفاده از Q صحیح
    all_services = Service.objects.filter(
        Q(operator=operator) | Q(status='pending')
    ).select_related('customer', 'operator').order_by('-created_at')

    services_json = []
    for service in all_services:
        services_json.append({
            'id': str(service.id),
            'tracking_code': service.tracking_code,
            'title': service.title,
            'description': service.description,
            'customer_note': service.customer_note,
            'status': service.status,
            'status_display': service.get_status_display(),
            'final_price': service.final_price or service.price,
            'is_paid': service.is_paid,
            'customer_name': service.customer.full_name,
            'customer_phone': service.customer.phone,
            'has_file': bool(service.result_file),
            'result_file_name': service.result_file_name,
        })

    # محاسبه آمار
    pending_count = all_services.filter(status='pending').count()
    progress_count = all_services.filter(status__in=['accepted', 'in_progress']).count()
    done_count = all_services.filter(status__in=['completed', 'delivered']).count()

    context = {
        'operator': operator,
        'services_json': json.dumps(services_json, ensure_ascii=False),
        'pending_count': pending_count,
        'progress_count': progress_count,
        'done_count': done_count,
    }

    return render(request, 'account_module/operator_panel.html', context)



# ============================================
# API های اپراتور
# ============================================
@require_POST
def operator_accept_service(request, service_id):
    """قبول کردن کار توسط اپراتور"""
    operator = get_operator(request)
    if not operator:
        return JsonResponse({'success': False, 'error': 'لطفاً وارد شوید'}, status=401)

    service = get_object_or_404(Service, id=service_id, status='pending')

    service.operator = operator
    service.status = 'accepted'
    service.accepted_at = timezone.now()
    service.save()

    # آپدیت چت
    service.chat.update_operator(operator)
    service.chat.update_status('accepted')

    return JsonResponse({'success': True})


@require_POST
def operator_reject_service(request, service_id):
    """رد کردن کار"""
    operator = get_operator(request)
    if not operator:
        return JsonResponse({'success': False, 'error': 'لطفاً وارد شوید'}, status=401)

    service = get_object_or_404(Service, id=service_id, status='pending')
    service.status = 'rejected'
    service.save()

    return JsonResponse({'success': True})


@require_POST
def operator_upload_file(request, service_id):
    """آپلود فایل نتیجه"""
    operator = get_operator(request)
    if not operator:
        return JsonResponse({'success': False, 'error': 'لطفاً وارد شوید'}, status=401)

    service = get_object_or_404(Service, id=service_id, operator=operator)

    if 'file' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'فایلی ارسال نشده'}, status=400)

    uploaded_file = request.FILES['file']
    service.result_file = uploaded_file
    service.result_file_name = uploaded_file.name
    service.result_file_size = uploaded_file.size
    service.save()

    # ثبت در چت
    service.chat.add_file('operator', {
        'name': uploaded_file.name,
        'url': service.result_file.url,
        'size': uploaded_file.size
    })

    return JsonResponse({'success': True, 'file_name': uploaded_file.name})


@require_POST
def operator_complete_service(request, service_id):
    """تکمیل کار"""
    operator = get_operator(request)
    if not operator:
        return JsonResponse({'success': False, 'error': 'لطفاً وارد شوید'}, status=401)

    service = get_object_or_404(Service, id=service_id, operator=operator)

    if not service.result_file:
        return JsonResponse({'success': False, 'error': 'ابتدا فایل را آپلود کنید'}, status=400)

    service.status = 'completed'
    service.completed_at = timezone.now()
    service.save()

    # آپدیت آمار اپراتور
    operator.completed_jobs += 1
    operator.pending_payment += (service.final_price - service.commission_amount)
    operator.save()

    service.chat.update_status('completed')

    return JsonResponse({'success': True})