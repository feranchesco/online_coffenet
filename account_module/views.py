import json

from django.contrib.auth.handlers.modwsgi import check_password
from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from django.views.generic import CreateView, FormView

from .forms import OperatorSignupForm, OperatorLoginForm, CustomerSignupForm, CustomerLoginForm
from .models import Customer
from home_module.models import Service, Operator


# ============================================
# پنل مشتری
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


class CustomerSignup(CreateView):
    model = Customer
    form_class = CustomerSignupForm
    template_name = "account_module/customer_signup.html"
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        customer = form.save(commit=False)
        customer.set_password(form.cleaned_data['password'])
        customer.save()
        login(self.request, customer)
        return redirect(self.success_url)

class CustomerLogin(FormView):
    form_class = CustomerLoginForm
    template_name = "account_module/customer_login.html"
    success_url = reverse_lazy('profile')
    def form_valid(self, form):
        customer = form.cleaned_data['customer']
        login(self.request, customer)
        return redirect(self.success_url)

def customer_logout(request):
    """خروج مشتری"""
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    customer = request.user
    services = Service.objects.filter(
        customer=customer
    ).select_related('operator').order_by('-created_at')

    services_data = []
    for service in services:
        if not service.chat.exists():
            service.chat.create()

        services_data.append({
            'id': str(service.id),
            'tracking_code': service.tracking_code,
            'title': service.title,
            'description': service.description or '',
            'status': service.status,
            'status_display': service.get_status_display(),
            'price': service.price,
            'final_price': service.final_price or service.price,
            'is_paid': service.is_paid,
            'operator_name': service.operator.full_name if service.operator else None,
            'operator_role': service.operator.get_role_display() if service.operator else None,
            'has_file': bool(service.result_file),
        })

    context = {
        'customer': customer,
        'services': json.dumps(services_data, ensure_ascii=False),
    }

    return render(request, 'account_module/profile.html', context)


# ============================================
# پنل اپراتور
# ============================================

class OperatorSignup(CreateView):
    model = Operator
    form_class = OperatorSignupForm
    template_name = "account_module/operator_signup.html"
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        operator = form.save(commit=False)
        operator.set_password(form.cleaned_data['password'])
        operator.specialties = form.cleaned_data['specialties']
        operator.save()
        return redirect(self.success_url)

class OperatorLogin(FormView):
    form_class = OperatorLoginForm
    template_name = 'account_module/operator_login.html'
    success_url = reverse_lazy('operator_panel')

    def form_valid(self, form):
        operator = form.cleaned_data['operator']
        self.request.session['operator_id'] = str(operator.id)
        self.request.session['operator_name'] = operator.full_name
        return redirect(self.success_url)

def operator_logout(request):
    """خروج اپراتور"""
    request.session.flush()
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
