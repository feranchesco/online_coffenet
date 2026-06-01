# account_module/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Customer


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