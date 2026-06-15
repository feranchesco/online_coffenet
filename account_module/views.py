import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django.views.generic import CreateView, FormView
from functools import wraps
from .forms import OperatorSignupForm, OperatorLoginForm, CustomerSignupForm, CustomerLoginForm
from .models import Customer
from home_module.models import Service, Operator, Transaction
from django.contrib import messages


# ============================================
# دکوریتور ها
# ============================================
def anonymous_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated or request.session.get('operator_id',default=False):
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
def superuser_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper

# ============================================
# پنل مشتری
# ============================================
@method_decorator(anonymous_required, name='dispatch')
class CustomerSignup(CreateView):
    model = Customer
    form_class = CustomerSignupForm
    template_name = "account_module/customer_signup.html"
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        customer = form.save(commit=False)
        customer.set_password(form.cleaned_data['password'])
        customer.username = form.cleaned_data['phone']
        customer.save()
        login(self.request, customer)
        messages.success(self.request, 'حساب شما با موفقیت ساخته شد!')
        return redirect(self.success_url)
@method_decorator(anonymous_required, name='dispatch')
class CustomerLogin(FormView):
    form_class = CustomerLoginForm
    template_name = "account_module/customer_login.html"
    success_url = reverse_lazy('profile')
    def form_valid(self, form):
        customer = form.cleaned_data['customer']
        login(self.request, customer)
        messages.success(self.request, f'{customer.full_name} عزیز خوش آمدید.')
        return redirect(self.success_url)
def user_logout(request):
    """خروج مشتری"""
    logout(request)
    messages.error(request, 'شما از سایت خارج شدید.')
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
@method_decorator(superuser_required, name='dispatch')
class OperatorSignup(CreateView):
    model = Operator
    form_class = OperatorSignupForm
    template_name = "account_module/operator_signup.html"
    success_url = reverse_lazy('admin_dashboard')

    def form_valid(self, form):
        operator = form.save(commit=False)
        operator.set_password(form.cleaned_data['password'])
        operator.specialties = form.cleaned_data['specialties']
        operator.save()
        messages.success(self.request, f'حساب اپراتور {operator.full_name} باموفقیت ساخته شد!')
        return redirect(self.success_url)
@method_decorator(anonymous_required, name='dispatch')
class OperatorLogin(FormView):
    form_class = OperatorLoginForm
    template_name = 'account_module/operator_login.html'
    success_url = reverse_lazy('operator_panel')

    def form_valid(self, form):
        operator = form.cleaned_data['operator']
        self.request.session['operator_id'] = str(operator.id)
        self.request.session['operator_name'] = operator.full_name
        messages.success(self.request, f'{operator.full_name} عزیز خوش آمدید.')
        return redirect(self.success_url)

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
    """تکمیل کار - با محاسبه کمیسیون و آپدیت کیف پول"""
    operator = get_operator(request)
    if not operator:
        return JsonResponse({'success': False, 'error': 'لطفاً وارد شوید'}, status=401)

    service = get_object_or_404(Service, id=service_id, operator=operator)

    if not service.result_file:
        return JsonResponse({'success': False, 'error': 'ابتدا فایل را آپلود کنید'}, status=400)

    # محاسبه مالی
    final_price = service.final_price or service.price
    commission = int(final_price * service.commission_percent / 100)
    operator_share = final_price - commission

    # آپدیت سرویس
    service.status = 'completed'
    service.completed_at = timezone.now()
    service.commission_amount = commission
    service.save()

    # آپدیت اپراتور
    operator.completed_jobs += 1
    operator.total_earned += final_price
    operator.wallet_balance += operator_share  # اضافه کردن سهم به کیف پول
    operator.pending_payment = operator.total_earned - operator.wallet_balance  # مبلغی که هنوز پرداخت نشده
    operator.save()

    # ثبت تراکنش
    Transaction.objects.create(
        operator=operator,
        service=service,
        amount=operator_share,
        transaction_type='operator_pay',
        description=f'درآمد خدمت: {service.title} (کمیسیون {commission} تومان)'
    )

    service.chat.update_status('completed')

    return JsonResponse({
        'success': True,
        'new_balance': operator.wallet_balance,
        'pending_payment': operator.pending_payment,
        'total_earned': operator.total_earned,
        'commission': commission,
        'operator_share': operator_share,
    })
