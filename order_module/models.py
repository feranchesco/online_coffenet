# order_module/models.py

from django.db import models
from django.conf import settings
import uuid


class Payment(models.Model):
    """مدل پرداخت‌های سایت"""

    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('success', 'پرداخت موفق'),
        ('failed', 'پرداخت ناموفق'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # کاربر (می‌تونه مشتری باشه)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='کاربر'
    )

    # سرویس مرتبط (از home_module)
    service = models.ForeignKey(
        'home_module.Service',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='سرویس'
    )

    # اطلاعات پرداخت
    amount = models.BigIntegerField(verbose_name='مبلغ (تومان)')
    authority = models.CharField(max_length=255, null=True, blank=True, verbose_name='کد اتوریتی')
    ref_id = models.CharField(max_length=255, null=True, blank=True, verbose_name='کد پیگیری')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='وضعیت')

    # اطلاعات اضافی
    description = models.TextField(null=True, blank=True, verbose_name='توضیحات')
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'payments'
        verbose_name = 'پرداخت'
        verbose_name_plural = 'پرداخت‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['authority']),
            models.Index(fields=['ref_id']),
        ]

    def __str__(self):
        return f"پرداخت {self.amount:,} تومان - {self.get_status_display()}"


class DiscountCode(models.Model):
    """مدل کد تخفیف"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True, verbose_name='کد تخفیف')
    discount_percent = models.IntegerField(verbose_name='درصد تخفیف')
    max_uses = models.IntegerField(default=1, verbose_name='حداکثر استفاده')
    used_count = models.IntegerField(default=0, verbose_name='تعداد استفاده شده')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    expire_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ انقضا')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'discount_codes'
        verbose_name = 'کد تخفیف'
        verbose_name_plural = 'کدهای تخفیف'

    def __str__(self):
        return f"{self.code} - {self.discount_percent}%"

    def is_valid(self):
        """بررسی اعتبار کد تخفیف"""
        from django.utils import timezone
        if not self.is_active:
            return False
        if self.used_count >= self.max_uses:
            return False
        if self.expire_date and self.expire_date < timezone.now():
            return False
        return True