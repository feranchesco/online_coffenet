# home_module/admin.py

from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Operator, Service, Transaction, HomeService


# ============================================
# HomeService Admin
# ============================================
@admin.register(HomeService)
class HomeServiceAdmin(admin.ModelAdmin):
    """پنل مدیریت خدمات صفحه اصلی"""

    list_display = ['icon_display', 'title', 'price_display', 'is_active_icon',
                    'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['order', '-created_at']
    list_editable = ['order']  # ✅ فقط order قابل ویرایش سریع

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('icon', 'title', 'description')
        }),
        ('قیمت‌گذاری', {
            'fields': ('price',),
            'description': 'اگر قیمت ۰ باشد، عبارت "تماس بگیرید" نمایش داده می‌شود'
        }),
        ('تنظیمات نمایش', {
            'fields': ('is_active', 'order'),
            'description': 'ترتیب کمتر = نمایش زودتر. غیرفعال = نمایش داده نشود'
        }),
    )

    @admin.display(description='آیکون')
    def icon_display(self, obj):
        return f'{obj.icon} {obj.title}'

    @admin.display(description='قیمت')
    def price_display(self, obj):
        if obj.price == 0:
            return 'تماس بگیرید'
        return f'{obj.price:,} تومان'

    @admin.display(description='وضعیت')
    def is_active_icon(self, obj):
        if obj.is_active:
            return mark_safe('<span style="color:#4ade80;">✅ فعال</span>')
        return mark_safe('<span style="color:#ef4444;">❌ غیرفعال</span>')

    # ✅ اکشن‌های گروهی
    actions = ['make_active', 'make_inactive']

    @admin.action(description='✅ فعال کردن خدمات انتخاب شده')
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} خدمت فعال شدند.')

    @admin.action(description='❌ غیرفعال کردن خدمات انتخاب شده')
    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} خدمت غیرفعال شدند.')


# ============================================
# Operator Admin
# ============================================
@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    """پنل مدیریت اپراتورها"""

    list_display = ['full_name', 'phone', 'role_badge', 'rating_stars',
                    'completed_jobs', 'total_earned_display', 'status_badge']
    list_filter = ['role', 'is_active', 'is_available', 'is_verified']
    search_fields = ['full_name', 'phone', 'email', 'username']
    ordering = ['-created_at']

    fieldsets = (
        ('اطلاعات کاربری', {
            'fields': ('username', 'phone', 'password')
        }),
        ('اطلاعات شخصی', {
            'fields': ('full_name', 'email', 'avatar')
        }),
        ('نقش و تخصص', {
            'fields': ('role', 'specialties')
        }),
        ('امتیازدهی', {
            'fields': ('rating', 'total_reviews', 'completed_jobs')
        }),
        ('اطلاعات مالی', {
            'fields': ('wallet_balance', 'total_earned', 'pending_payment')
        }),
        ('وضعیت', {
            'fields': ('is_active', 'is_available', 'is_verified')
        }),
        ('زمان‌ها', {
            'fields': ('last_login', 'last_seen', 'created_at', 'updated_at')
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login', 'last_seen']

    @admin.display(description='نقش')
    def role_badge(self, obj):
        colors = {
            'operator': '#6366f1',
            'owner': '#fbbf24',
            'admin': '#ef4444',
        }
        color = colors.get(obj.role, '#6b7280')
        role_name = obj.get_role_display()
        html = f'<span style="background:{color};color:white;padding:2px 10px;border-radius:10px;font-size:12px;">{role_name}</span>'
        return mark_safe(html)

    @admin.display(description='امتیاز')
    def rating_stars(self, obj):
        if obj.rating > 0:
            stars = '⭐' * int(obj.rating)
        else:
            stars = '-'
        html = f'{stars} <small>({obj.total_reviews})</small>'
        return mark_safe(html)

    @admin.display(description='کل درآمد')
    def total_earned_display(self, obj):
        return f"{obj.total_earned:,} تومان"

    @admin.display(description='وضعیت')
    def status_badge(self, obj):
        if obj.is_active and obj.is_available:
            html = '<span style="color:#4ade80;">🟢 آماده</span>'
        elif obj.is_active:
            html = '<span style="color:#fbbf24;">🟡 مشغول</span>'
        else:
            html = '<span style="color:#ef4444;">🔴 غیرفعال</span>'
        return mark_safe(html)


# ============================================
# Service Admin
# ============================================
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """پنل مدیریت خدمات/سفارشات"""

    list_display = ['tracking_code', 'title', 'customer_name', 'operator_name',
                    'price_display', 'status_badge', 'is_paid_icon', 'created_at']
    list_filter = ['status', 'priority', 'is_paid', 'created_at']
    search_fields = ['tracking_code', 'title', 'customer__full_name',
                     'operator__full_name', 'customer__phone']
    ordering = ['-created_at']
    readonly_fields = ['tracking_code', 'created_at', 'updated_at']

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('tracking_code', 'title', 'description')
        }),
        ('مشتری و اپراتور', {
            'fields': ('customer', 'operator')
        }),
        ('وضعیت و اولویت', {
            'fields': ('status', 'priority')
        }),
        ('اطلاعات مالی', {
            'fields': ('price', 'discount_amount', 'final_price',
                       'commission_percent', 'commission_amount')
        }),
        ('پرداخت', {
            'fields': ('is_paid', 'payment_date', 'payment_ref')
        }),
        ('فایل‌ها', {
            'fields': ('result_file', 'result_file_name', 'result_file_size')
        }),
        ('توضیحات', {
            'fields': ('customer_note', 'operator_note')
        }),
        ('زمان‌بندی', {
            'fields': ('deadline', 'accepted_at', 'started_at',
                       'completed_at', 'delivered_at')
        }),
        ('امتیازدهی', {
            'fields': ('rating', 'review')
        }),
    )

    @admin.display(description='مشتری', ordering='customer__full_name')
    def customer_name(self, obj):
        return obj.customer.full_name

    @admin.display(description='اپراتور', ordering='operator__full_name')
    def operator_name(self, obj):
        if obj.operator:
            return obj.operator.full_name
        return '❌ تعیین نشده'

    @admin.display(description='قیمت')
    def price_display(self, obj):
        price = obj.final_price or obj.price
        return f"{price:,} تومان"

    @admin.display(description='وضعیت')
    def status_badge(self, obj):
        colors = {
            'pending': '#fbbf24',
            'accepted': '#60a5fa',
            'in_progress': '#3b82f6',
            'completed': '#4ade80',
            'delivered': '#22c55e',
            'cancelled': '#f87171',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        status_text = obj.get_status_display()
        html = f'<span style="background:{color};color:white;padding:2px 10px;border-radius:10px;font-size:12px;">{status_text}</span>'
        return mark_safe(html)

    @admin.display(description='پرداخت')
    def is_paid_icon(self, obj):
        if obj.is_paid:
            html = '<span style="color:#4ade80;">✅ پرداخت شده</span>'
        else:
            html = '<span style="color:#fbbf24;">⏳ در انتظار</span>'
        return mark_safe(html)


# ============================================
# Transaction Admin
# ============================================
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """پنل مدیریت تراکنش‌ها"""

    list_display = ['ref_code', 'type_badge', 'amount_display', 'customer_name',
                    'operator_name', 'is_successful_icon', 'created_at']
    list_filter = ['transaction_type', 'is_successful', 'created_at']
    search_fields = ['ref_code', 'customer__full_name', 'operator__full_name']
    ordering = ['-created_at']
    readonly_fields = ['ref_code', 'created_at']

    @admin.display(description='مشتری')
    def customer_name(self, obj):
        if obj.customer:
            return obj.customer.full_name
        return '-'

    @admin.display(description='اپراتور')
    def operator_name(self, obj):
        if obj.operator:
            return obj.operator.full_name
        return '-'

    @admin.display(description='مبلغ')
    def amount_display(self, obj):
        return f"{obj.amount:,} تومان"

    @admin.display(description='نوع')
    def type_badge(self, obj):
        colors = {
            'deposit': '#4ade80',
            'payment': '#60a5fa',
            'commission': '#fbbf24',
            'operator_pay': '#a78bfa',
            'refund': '#f87171',
        }
        color = colors.get(obj.transaction_type, '#6b7280')
        type_text = obj.get_transaction_type_display()
        html = f'<span style="background:{color};color:white;padding:2px 10px;border-radius:10px;font-size:12px;">{type_text}</span>'
        return mark_safe(html)

    @admin.display(description='وضعیت')
    def is_successful_icon(self, obj):
        if obj.is_successful:
            html = '<span style="color:#4ade80;">✅ موفق</span>'
        else:
            html = '<span style="color:#ef4444;">❌ ناموفق</span>'
        return mark_safe(html)