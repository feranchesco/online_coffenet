# account_module/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Customer,Operator
from django.utils.safestring import mark_safe


@admin.register(Customer)
class CustomerAdmin(UserAdmin):
    """پنل مدیریت مشتریان"""

    list_display = ['phone', 'full_name', 'email', 'walallet_balance_display',
                    'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_verified', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['phone', 'full_name', 'email', 'username']
    ordering = ['-created_at']

    fieldsets = (
        ('اطلاعات ورود', {
            'fields': ('username', 'phone', 'password')
        }),
        ('اطلاعات شخصی', {
            'fields': ('full_name', 'email', 'avatar')
        }),
        ('اطلاعات مالی', {
            'fields': ('wallet_balance',)
        }),
        ('دسترسی‌ها', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified')
        }),
        ('گروه‌ها و دسترسی‌ها', {
            'fields': ('groups', 'user_permissions')
        }),
        ('تاریخ‌ها', {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'full_name', 'username', 'password1', 'password2'),
        }),
    )

    readonly_fields = ['created_at', 'updated_at', 'last_login']

    def walallet_balance_display(self, obj):
        """نمایش موجودی کیف پول با فرمت تومان"""
        return f"{obj.wallet_balance:,} تومان"

    walallet_balance_display.short_description = 'اعتبار کیف پول'


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