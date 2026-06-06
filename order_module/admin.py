# order_module/admin.py

from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.utils import timezone
from django.db import models
from .models import Payment, DiscountCode


# ============================================
# Payment Admin
# ============================================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """پنل مدیریت پرداخت‌ها"""

    list_display = [
        'ref_id_display',
        'user_info',
        'service_info',
        'amount_display',
        'status_badge',
        'payment_method',
        'payment_date_jalali',
        'created_at_jalali'
    ]
    list_filter = [
        'status',
        'created_at',
        'payment_date'
    ]
    search_fields = [
        'ref_id',
        'authority',
        'user__full_name',
        'user__phone',
        'service__title',
        'service__tracking_code'
    ]
    ordering = ['-created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_per_page = 50
    date_hierarchy = 'created_at'

    fieldsets = (
        ('اطلاعات اصلی پرداخت', {
            'fields': (
                'id',
                ('user', 'service'),
                'amount',
                'status',
            )
        }),
        ('اطلاعات درگاه پرداخت', {
            'fields': (
                'authority',
                'ref_id',
                'description',
            )
        }),
        ('تاریخ‌ها', {
            'fields': (
                'payment_date',
                'created_at',
                'updated_at',
            )
        }),
    )

    # ============================================
    # نمایش‌های سفارشی
    # ============================================

    @admin.display(description='کد پیگیری')
    def ref_id_display(self, obj):
        if obj.ref_id:
            return obj.ref_id[:30]
        return '-'

    @admin.display(description='کاربر', ordering='user__full_name')
    def user_info(self, obj):
        if obj.user:
            return mark_safe(
                f'<div style="line-height:1.4;">'
                f'<strong>{obj.user.full_name}</strong><br>'
                f'<small style="color:#94a3b8;">📱 {obj.user.phone}</small>'
                f'</div>'
            )
        return '-'

    @admin.display(description='سرویس')
    def service_info(self, obj):
        if obj.service:
            url = reverse('admin:home_module_service_change', args=[obj.service.id])
            return mark_safe(
                f'<div style="line-height:1.4;">'
                f'<a href="{url}" style="color:#a78bfa;text-decoration:none;">{obj.service.title[:40]}</a><br>'
                f'<small style="color:#94a3b8;">کد: {obj.service.tracking_code}</small>'
                f'</div>'
            )
        return '-'

    @admin.display(description='مبلغ', ordering='amount')
    def amount_display(self, obj):
        # ✅ اصلاح: استفاده از f-string به جای format_html
        amount_str = f'{obj.amount:,}'
        return mark_safe(
            f'<span style="color:#4ade80;font-weight:700;font-size:14px;">'
            f'{amount_str} تومان'
            f'</span>'
        )

    @admin.display(description='وضعیت', ordering='status')
    def status_badge(self, obj):
        status_config = {
            'pending': {'color': '#fbbf24', 'icon': '⏳', 'text': 'در انتظار'},
            'success': {'color': '#4ade80', 'icon': '✅', 'text': 'موفق'},
            'failed': {'color': '#ef4444', 'icon': '❌', 'text': 'ناموفق'},
        }
        config = status_config.get(obj.status, {
            'color': '#6b7280', 'icon': '❓', 'text': obj.status
        })

        return mark_safe(
            f'<span style="background:{config["color"]};color:white;padding:4px 12px;'
            f'border-radius:20px;font-size:12px;font-weight:600;'
            f'display:inline-block;min-width:80px;text-align:center;">'
            f'{config["icon"]} {config["text"]}</span>'
        )

    @admin.display(description='روش پرداخت')
    def payment_method(self, obj):
        if obj.ref_id and 'WALLET' in obj.ref_id:
            return mark_safe(
                '<span style="background:#6366f1;color:white;padding:3px 10px;'
                'border-radius:12px;font-size:11px;">💰 کیف پول</span>'
            )
        elif obj.authority:
            return mark_safe(
                '<span style="background:#f59e0b;color:white;padding:3px 10px;'
                'border-radius:12px;font-size:11px;">🏦 درگاه بانکی</span>'
            )
        return '-'

    @admin.display(description='تاریخ پرداخت', ordering='payment_date')
    def payment_date_jalali(self, obj):
        if obj.payment_date:
            return obj.payment_date.strftime('%Y/%m/%d - %H:%M')
        return '-'

    @admin.display(description='تاریخ ایجاد', ordering='created_at')
    def created_at_jalali(self, obj):
        return obj.created_at.strftime('%Y/%m/%d - %H:%M')

    # ============================================
    # اکشن‌های دسته‌جمعی
    # ============================================
    actions = ['mark_as_success', 'mark_as_failed']

    @admin.action(description='✅ علامت‌گذاری به عنوان پرداخت موفق')
    def mark_as_success(self, request, queryset):
        updated = queryset.filter(status='pending').update(
            status='success',
            payment_date=timezone.now(),
            ref_id=f'ADMIN-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        )
        self.message_user(request, f'{updated} پرداخت به عنوان موفق علامت‌گذاری شد.')

    @admin.action(description='❌ علامت‌گذاری به عنوان پرداخت ناموفق')
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} پرداخت به عنوان ناموفق علامت‌گذاری شد.')

    # ============================================
    # آمار در لیست
    # ============================================
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}

        total_payments = Payment.objects.count()
        successful = Payment.objects.filter(status='success').count()
        failed = Payment.objects.filter(status='failed').count()
        pending = Payment.objects.filter(status='pending').count()

        total_amount = Payment.objects.filter(status='success').aggregate(
            total=models.Sum('amount')
        )['total'] or 0

        today = timezone.now().date()
        today_payments = Payment.objects.filter(
            created_at__date=today,
            status='success'
        ).count()
        today_amount = Payment.objects.filter(
            created_at__date=today,
            status='success'
        ).aggregate(total=models.Sum('amount'))['total'] or 0

        extra_context.update({
            'total_payments': total_payments,
            'successful': successful,
            'failed': failed,
            'pending': pending,
            'total_amount': total_amount,
            'today_payments': today_payments,
            'today_amount': today_amount,
        })

        return super().changelist_view(request, extra_context)


# ============================================
# DiscountCode Admin
# ============================================
@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    """پنل مدیریت کدهای تخفیف"""

    list_display = [
        'code',
        'discount_percent_display',
        'usage_progress',
        'validity_status',
        'max_uses_display',
        'expire_date_jalali',
        'created_at_jalali'
    ]
    list_filter = [
        'is_active',
        'created_at',
        'expire_date'
    ]
    search_fields = ['code']
    ordering = ['-created_at']
    list_per_page = 30

    fieldsets = (
        ('اطلاعات کد تخفیف', {
            'fields': (
                'code',
                'discount_percent',
                'is_active',
            )
        }),
        ('محدودیت‌های استفاده', {
            'fields': (
                ('max_uses', 'used_count'),
                'expire_date',
            )
        }),
    )

    readonly_fields = ['used_count', 'created_at']

    @admin.display(description='درصد تخفیف')
    def discount_percent_display(self, obj):
        return mark_safe(
            f'<span style="background:linear-gradient(135deg,#fbbf24,#f59e0b);'
            f'color:#1a1c2e;padding:4px 12px;border-radius:20px;'
            f'font-weight:700;font-size:14px;">٪ {obj.discount_percent}</span>'
        )

    @admin.display(description='حداکثر استفاده')
    def max_uses_display(self, obj):
        return f'{obj.used_count} / {obj.max_uses}'

    @admin.display(description='میزان استفاده')
    def usage_progress(self, obj):
        percent = int((obj.used_count / obj.max_uses) * 100) if obj.max_uses > 0 else 0

        if percent >= 100:
            color = '#ef4444'
        elif percent >= 70:
            color = '#fbbf24'
        else:
            color = '#4ade80'

        return mark_safe(
            f'<div style="display:flex;align-items:center;gap:8px;">'
            f'<div style="background:rgba(255,255,255,0.1);border-radius:10px;'
            f'width:100px;height:8px;overflow:hidden;">'
            f'<div style="background:{color};width:{percent}%;height:100%;border-radius:10px;"></div>'
            f'</div>'
            f'<span style="font-size:12px;">{obj.used_count}/{obj.max_uses}</span>'
            f'</div>'
        )

    @admin.display(description='وضعیت')
    def validity_status(self, obj):
        if not obj.is_active:
            return mark_safe(
                '<span style="background:#ef4444;color:white;padding:4px 12px;'
                'border-radius:20px;font-size:11px;">❌ غیرفعال</span>'
            )

        if obj.used_count >= obj.max_uses:
            return mark_safe(
                '<span style="background:#f87171;color:white;padding:4px 12px;'
                'border-radius:20px;font-size:11px;">🔒 ظرفیت تمام شد</span>'
            )

        if obj.expire_date and obj.expire_date < timezone.now():
            return mark_safe(
                '<span style="background:#fbbf24;color:#1a1c2e;padding:4px 12px;'
                'border-radius:20px;font-size:11px;">⏰ منقضی شده</span>'
            )

        return mark_safe(
            '<span style="background:#4ade80;color:#1a1c2e;padding:4px 12px;'
            'border-radius:20px;font-size:11px;">✅ فعال</span>'
        )

    @admin.display(description='تاریخ انقضا')
    def expire_date_jalali(self, obj):
        if obj.expire_date:
            return obj.expire_date.strftime('%Y/%m/%d')
        return mark_safe('<span style="color:#94a3b8;">نامحدود</span>')

    @admin.display(description='تاریخ ایجاد')
    def created_at_jalali(self, obj):
        return obj.created_at.strftime('%Y/%m/%d')

    # ============================================
    # اکشن‌ها
    # ============================================
    actions = ['activate_codes', 'deactivate_codes', 'reset_usage']

    @admin.action(description='✅ فعال کردن کدهای انتخاب شده')
    def activate_codes(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} کد تخفیف فعال شد.')

    @admin.action(description='❌ غیرفعال کردن کدهای انتخاب شده')
    def deactivate_codes(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} کد تخفیف غیرفعال شد.')

    @admin.action(description='🔄 ریست کردن تعداد استفاده')
    def reset_usage(self, request, queryset):
        updated = queryset.update(used_count=0)
        self.message_user(request, f'{updated} کد تخفیف ریست شد.')