# account_module/models.py
from PIL.ImImagePlugin import number
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
import uuid
import hashlib


# ============================================
# Customer Manager
# ============================================
class CustomerManager(BaseUserManager):
    """مدیریت ایجاد مشتریان"""

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('شماره تلفن الزامی است')

        # پاک کردن فیلدهایی که توی Customer وجود ندارن
        extra_fields.pop('role', None)
        extra_fields.pop('specialties', None)
        extra_fields.pop('rating', None)
        extra_fields.pop('total_reviews', None)
        extra_fields.pop('completed_jobs', None)
        extra_fields.pop('is_available', None)
        extra_fields.pop('total_earned', None)
        extra_fields.pop('pending_payment', None)

        extra_fields.setdefault('username', phone)

        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        # پاک کردن فیلدهای اضافی
        extra_fields.pop('role', None)
        extra_fields.pop('specialties', None)
        extra_fields.pop('rating', None)
        extra_fields.pop('total_reviews', None)
        extra_fields.pop('completed_jobs', None)
        extra_fields.pop('is_available', None)
        extra_fields.pop('total_earned', None)
        extra_fields.pop('pending_payment', None)

        if not extra_fields.get('username'):
            extra_fields['username'] = phone

        return self.create_user(phone, password, **extra_fields)


# ============================================
# Customer Model
# ============================================
class Customer(AbstractUser):
    """مدل مشتری - کاربران سایت"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='نام کاربری',
        error_messages={
            'unique': "این نام کاربری قبلاً استفاده شده است.",
        },
    )
    phone = models.CharField(
        max_length=11,
        unique=True,
        verbose_name='شماره تلفن',
        error_messages={
            'unique': "این شماره تلفن قبلاً ثبت شده است.",
        },
    )
    full_name = models.CharField(max_length=255, verbose_name='نام کامل')
    email = models.EmailField(null=True, blank=True, verbose_name='ایمیل')
    avatar = models.ImageField(
        upload_to='avatars/customers/',
        null=True,
        blank=True,
        verbose_name='آواتار'
    )

    # اطلاعات مالی
    wallet_balance = models.BigIntegerField(default=0, verbose_name='اعتبار کیف پول (تومان)')

    # وضعیت
    is_verified = models.BooleanField(default=False, verbose_name='تأیید شده')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت‌نام')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    # رفع تداخل related_name با auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='گروه‌ها',
        blank=True,
        help_text='گروه‌هایی که این کاربر عضو آن است.',
        related_name="customer_set",
        related_query_name="customer",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='دسترسی‌ها',
        blank=True,
        help_text='دسترسی‌های خاص برای این کاربر.',
        related_name="customer_set",
        related_query_name="customer",
    )

    objects = CustomerManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['full_name', 'username']

    class Meta:
        db_table = 'customers'
        verbose_name = 'مشتری'
        verbose_name_plural = 'مشتریان'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['username']),
        ]

    def __str__(self):
        return f"{self.full_name} | {self.phone}"

    def get_full_name(self):
        return self.full_name

    def get_short_name(self):
        if self.full_name:
            return self.full_name.split()[0]
        return self.phone


# ============================================
# Operator Model
# ============================================
class Operator(models.Model):
    """مدل اپراتور - کاملاً مستقل از Customer"""

    ROLE_CHOICES = [
        ('operator', 'اپراتور عادی'),
        ('owner', 'صاحب سایت'),
        ('admin', 'مدیر'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='نام کاربری'
    )
    phone = models.CharField(
        max_length=11,
        unique=True,
        verbose_name='شماره تلفن'
    )
    full_name = models.CharField(max_length=255, verbose_name='نام کامل')
    email = models.EmailField(null=True, blank=True, verbose_name='ایمیل')
    password = models.CharField(max_length=255, verbose_name='رمز عبور')
    avatar = models.ImageField(
        upload_to='avatars/operators/',
        null=True,
        blank=True,
        verbose_name='آواتار'
    )

    # نقش و تخصص
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='operator',
        verbose_name='نقش'
    )
    specialties = models.JSONField(
        default=list,
        blank=True,
        verbose_name='تخصص‌ها',
        help_text='لیست تخصص‌های اپراتور: ["چاپ", "تایپ", "طراحی"]'
    )

    # امتیازدهی
    rating = models.FloatField(default=0, verbose_name='امتیاز')
    total_reviews = models.IntegerField(default=0, verbose_name='تعداد نظرات')
    completed_jobs = models.IntegerField(default=0, verbose_name='کارهای تکمیل شده')

    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_available = models.BooleanField(default=True, verbose_name='آماده به کار')
    is_verified = models.BooleanField(default=False, verbose_name='تأیید شده')

    # اطلاعات مالی
    wallet_balance = models.BigIntegerField(default=0, verbose_name='اعتبار کیف پول (تومان)')
    total_earned = models.BigIntegerField(default=0, verbose_name='کل درآمد (تومان)')
    pending_payment = models.BigIntegerField(default=0, verbose_name='در انتظار پرداخت (تومان)')

    # زمان‌ها
    last_login = models.DateTimeField(null=True, blank=True, verbose_name='آخرین ورود')
    last_seen = models.DateTimeField(null=True, blank=True, verbose_name='آخرین فعالیت')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ثبت‌نام')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        db_table = 'operators'
        verbose_name = 'اپراتور'
        verbose_name_plural = 'اپراتورها'
        indexes = [
            models.Index(fields=['phone']),
            models.Index(fields=['role']),
            models.Index(fields=['is_available']),
        ]

    def __str__(self):
        return f"{self.full_name} | {self.get_role_display()}"

    @property
    def is_owner(self):
        """بررسی صاحب سایت بودن"""
        return self.role == 'owner'

    @property
    def is_admin(self):
        """بررسی مدیر بودن"""
        return self.role in ['admin', 'owner']

    def set_password(self, raw_password):
        """تنظیم رمز عبور هش شده"""
        self.password = hashlib.sha256(raw_password.encode()).hexdigest()

    def check_password(self, raw_password):
        """بررسی رمز عبور"""
        hashed = hashlib.sha256(raw_password.encode()).hexdigest()
        return self.password == hashed

    def get_active_services_count(self):
        """تعداد خدمات فعال"""
        return self.services.filter(
            status__in=['accepted', 'in_progress']
        ).count()


