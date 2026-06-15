from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
import uuid
import os
import json
from datetime import datetime
from threading import Lock
from django.utils import timezone
from account_module.models import Operator

# ============================================
# Service Model
# ============================================
class Service(models.Model):
    """مدل اصلی خدمت/سفارش"""

    STATUS_CHOICES = [
        ('pending', 'در انتظار پذیرش'),
        ('accepted', 'پذیرفته شده'),
        ('in_progress', 'در حال انجام'),
        ('completed', 'آماده تحویل'),
        ('delivered', 'تحویل داده شده'),
        ('cancelled', 'لغو شده'),
        ('rejected', 'رد شده'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'کم'),
        ('medium', 'متوسط'),
        ('high', 'زیاد'),
        ('urgent', 'فوری'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tracking_code = models.CharField(
        max_length=12,
        unique=True,
        verbose_name='کد پیگیری'
    )

    # ارتباط با مشتری و اپراتور
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='مشتری'
    )
    operator = models.ForeignKey(
        Operator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        verbose_name='اپراتور'
    )

    # اطلاعات خدمت
    title = models.CharField(max_length=255, verbose_name='عنوان خدمت')
    description = models.TextField(verbose_name='توضیحات خدمت')
    customer_note = models.TextField(
        null=True,
        blank=True,
        verbose_name='توضیحات مشتری'
    )
    operator_note = models.TextField(
        null=True,
        blank=True,
        verbose_name='یادداشت اپراتور'
    )

    # وضعیت
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='وضعیت'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        verbose_name='اولویت'
    )

    # مالی
    price = models.BigIntegerField(
        validators=[MinValueValidator(0)],
        verbose_name='قیمت (تومان)'
    )
    discount_amount = models.BigIntegerField(default=0, verbose_name='مبلغ تخفیف (تومان)')
    final_price = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='قیمت نهایی (تومان)'
    )
    commission_percent = models.FloatField(default=40.0, verbose_name='درصد کمیسیون')
    commission_amount = models.BigIntegerField(default=0, verbose_name='مبلغ کمیسیون (تومان)')

    # پرداخت
    is_paid = models.BooleanField(default=False, verbose_name='پرداخت شده')
    payment_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ پرداخت')
    payment_ref = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name='کد پیگیری پرداخت'
    )

    # فایل‌ها
    result_file = models.FileField(
        upload_to='results/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='فایل نتیجه'
    )
    result_file_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='نام فایل نتیجه'
    )
    result_file_size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='حجم فایل نتیجه (بایت)'
    )

    # زمان‌بندی
    deadline = models.DateTimeField(null=True, blank=True, verbose_name='مهلت تحویل')
    accepted_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان پذیرش')
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان شروع')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تکمیل')
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان تحویل')

    # امتیازدهی
    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='امتیاز مشتری (۱ تا ۵)'
    )
    review = models.TextField(null=True, blank=True, verbose_name='نظر مشتری')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    # چت (property - در دیتابیس ذخیره نمیشه)
    _chat = None

    class Meta:
        db_table = 'services'
        verbose_name = 'خدمت'
        verbose_name_plural = 'خدمات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_code']),
            models.Index(fields=['status']),
            models.Index(fields=['customer', 'status']),
            models.Index(fields=['operator', 'status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} | {self.tracking_code}"

    def save(self, *args, **kwargs):
        # تولید کد پیگیری خودکار
        if not self.tracking_code:
            self.tracking_code = self._generate_tracking_code()

        # محاسبه قیمت نهایی
        if self.final_price is None:
            self.final_price = self.price - self.discount_amount

        # محاسبه کمیسیون
        if self.commission_amount == 0 and self.final_price:
            self.commission_amount = int(self.final_price * self.commission_percent / 100)

        is_new = self._state.adding
        super().save(*args, **kwargs)

        # ایجاد فایل چت برای خدمت جدید
        if is_new:
            self.chat.create()

    def _generate_tracking_code(self):
        """تولید کد پیگیری یکتا"""
        import random
        while True:
            code = 'KAF' + ''.join(random.choices('0123456789', k=9))
            if not Service.objects.filter(tracking_code=code).exists():
                return code

    @property
    def chat(self):
        """
        دسترسی به چت خدمت
        استفاده: service.chat.add_message(...)
        """
        if self._chat is None:
            self._chat = ServiceChat(self)
        return self._chat

    def can_chat(self, user) -> bool:
        """بررسی امکان چت برای کاربر"""
        from account_module.models import Customer

        if isinstance(user, Customer):
            return user == self.customer
        elif isinstance(user, Operator):
            return user == self.operator
        return False

    @property
    def is_owner_service(self):
        """بررسی اینکه اپراتور جزو صاحبان سایت است"""
        return self.operator and self.operator.is_owner

    @property
    def operator_earnings(self):
        """درآمد اپراتور از این خدمت (پس از کسر کمیسیون)"""
        if self.final_price and self.commission_amount:
            return self.final_price - self.commission_amount
        return 0

    def get_status_display_color(self):
        """دریافت رنگ وضعیت برای نمایش در UI"""
        colors = {
            'pending': '#fbbf24',
            'accepted': '#60a5fa',
            'in_progress': '#3b82f6',
            'completed': '#4ade80',
            'delivered': '#22c55e',
            'cancelled': '#f87171',
            'rejected': '#ef4444',
        }
        return colors.get(self.status, '#6b7280')

class HomeService(models.Model):
    """مدل خدمات نمایش داده شده در صفحه اصلی"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    icon = models.CharField(max_length=50, default='📋', verbose_name='آیکون (اموجی)')
    title = models.CharField(max_length=255, verbose_name='عنوان خدمت')
    description = models.TextField(verbose_name='توضیحات کوتاه')
    price = models.BigIntegerField(
        default=0,
        verbose_name='قیمت (تومان) - ۰ یعنی تماس بگیرید',
        help_text='اگر قیمت ۰ باشد، "تماس بگیرید" نمایش داده می‌شود'
    )
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    order = models.IntegerField(default=0, verbose_name='ترتیب نمایش')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='آخرین بروزرسانی')

    class Meta:
        db_table = 'home_services'
        verbose_name = 'خدمت صفحه اصلی'
        verbose_name_plural = 'خدمات صفحه اصلی'
        ordering = ['order', '-created_at']

    def __str__(self):
        return f"{self.icon} {self.title}"

    def get_price_display(self):
        """نمایش قیمت به صورت خوانا"""
        if self.price == 0:
            return 'تماس بگیرید'
        return f'{self.price:,} تومان'
# ============================================
# ServiceChat - مدیریت چت با JSON
# ============================================
class ServiceChat:
    """کلاس مدیریت چت برای هر خدمت"""

    CHAT_DIR = 'media/chats'
    _locks = {}

    def __init__(self, service):
        self.service = service
        self.service_id = str(service.id).replace('-', '')
        self.file_path = os.path.join(self.CHAT_DIR, f'service_{self.service_id}.json')
        self._ensure_dir()

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.CHAT_DIR, exist_ok=True)

    @classmethod
    def _get_lock(cls, service_id):
        key = str(service_id)
        if key not in cls._locks:
            cls._locks[key] = Lock()
        return cls._locks[key]

    def exists(self) -> bool:
        return os.path.exists(self.file_path)

    def create(self) -> dict:
        if self.exists():
            return self.read()

        chat_data = {
            "service_id": str(self.service.id),
            "tracking_code": self.service.tracking_code,
            "title": self.service.title,
            "status": self.service.status,
            "price": self.service.price,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "participants": {
                "customer": {
                    "id": str(self.service.customer.id),
                    "name": self.service.customer.full_name,
                    "phone": self.service.customer.phone
                },
                "operator": {
                    "id": str(self.service.operator.id) if self.service.operator else None,
                    "name": self.service.operator.full_name if self.service.operator else None,
                    "phone": self.service.operator.phone if self.service.operator else None
                }
            },
            "messages": [],
            "files": [],
            "metadata": {
                "total_messages": 0,
                "last_message_at": None,
                "last_message_by": None,
                "unread_customer": 0,
                "unread_operator": 0,
                "is_active": True
            }
        }

        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)

        return chat_data

    def read(self) -> dict:
        if not self.exists():
            return self.create()

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return self.create()

    def _write(self, data: dict):
        data['updated_at'] = datetime.now().isoformat()
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_message(self, sender_id: str, sender_name: str,
                    sender_type: str, content: str,
                    file_info: dict = None) -> dict:
        lock = self._get_lock(self.service_id)

        with lock:
            data = self.read()

            message = {
                "id": data['metadata']['total_messages'] + 1,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "sender_type": sender_type,
                "content": content,
                "file": file_info,
                "timestamp": datetime.now().isoformat(),
                "is_read": False,
                "edited": False
            }

            data['messages'].append(message)  # اضافه به آخر
            data['metadata']['total_messages'] += 1
            data['metadata']['last_message_at'] = message['timestamp']
            data['metadata']['last_message_by'] = sender_id

            if sender_type == 'customer':
                data['metadata']['unread_operator'] += 1
            else:
                data['metadata']['unread_customer'] += 1

            self._write(data)
            return message

    def get_messages(self, page: int = 1, page_size: int = 50,
                     user_type: str = None) -> dict:
        """
        دریافت پیام‌ها با pagination
        ترتیب: قدیمی‌ترین اول، جدیدترین آخر
        صفحه ۱ = جدیدترین پیام‌ها
        """
        data = self.read()
        all_messages = data['messages']
        total = len(all_messages)

        if user_type:
            self._mark_as_read(data, user_type)

        # محاسبه شروع و پایان برای pagination
        # صفحه ۱: آخرین page_size پیام
        # صفحه ۲: page_size پیام قبل از آن
        start = max(0, total - (page * page_size))
        end = total - ((page - 1) * page_size)

        messages = all_messages[start:end]
        # بدون reverse - پیام‌ها به ترتیب زمانی طبیعی نمایش داده میشن

        return {
            "messages": messages,
            "has_more": start > 0,
            "total": total,
            "page": page,
            "unread_count": data['metadata'].get(f'unread_{user_type}', 0),
            "participants": data['participants']
        }

    def _mark_as_read(self, data: dict, user_type: str):
        for msg in data['messages']:
            if not msg['is_read'] and msg['sender_type'] != user_type:
                msg['is_read'] = True

        data['metadata'][f'unread_{user_type}'] = 0
        self._write(data)

    def mark_as_read(self, user_type: str) -> bool:
        data = self.read()
        self._mark_as_read(data, user_type)
        return True

    def get_unread_count(self, user_type: str) -> int:
        data = self.read()
        return data['metadata'].get(f'unread_{user_type}', 0)

    def get_last_message(self) -> dict:
        data = self.read()
        if data['messages']:
            return data['messages'][-1]  # آخرین عنصر = جدیدترین
        return None

    def add_file(self, uploaded_by: str, file_info: dict):
        data = self.read()

        file_record = {
            "id": len(data['files']) + 1,
            "uploaded_by": uploaded_by,
            "file_name": file_info.get('name'),
            "file_url": file_info.get('url'),
            "file_size": file_info.get('size'),
            "uploaded_at": datetime.now().isoformat()
        }

        data['files'].append(file_record)
        self._write(data)
        return file_record

    def update_status(self, status: str):
        data = self.read()
        data['status'] = status
        self._write(data)

    def update_operator(self, operator):
        data = self.read()
        data['participants']['operator'] = {
            "id": str(operator.id),
            "name": operator.full_name,
            "phone": operator.phone
        }
        self._write(data)

# ============================================
# Transaction Model
# ============================================
class Transaction(models.Model):
    """مدل تراکنش‌های مالی"""
    TYPE_CHOICES = [
        ('deposit', 'شارژ کیف پول'),
        ('payment', 'پرداخت خدمت'),
        ('commission', 'کمیسیون سایت'),
        ('operator_pay', 'پرداخت به اپراتور'),
        ('refund', 'بازگشت وجه'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # طرفین تراکنش
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='مشتری'
    )
    operator = models.ForeignKey(
        Operator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='اپراتور'
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name='خدمت مرتبط'
    )

    # اطلاعات تراکنش
    amount = models.BigIntegerField(verbose_name='مبلغ (تومان)')
    transaction_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        verbose_name='نوع تراکنش'
    )
    description = models.TextField(null=True, blank=True, verbose_name='توضیحات')
    ref_code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='کد پیگیری'
    )
    is_successful = models.BooleanField(default=True, verbose_name='موفق')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ تراکنش')

    class Meta:
        db_table = 'transactions'
        verbose_name = 'تراکنش'
        verbose_name_plural = 'تراکنش‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['operator', 'created_at']),
            models.Index(fields=['transaction_type']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} | {self.amount:,} تومان"

    def save(self, *args, **kwargs):
        # تولید کد پیگیری خودکار
        if not self.ref_code:
            self.ref_code = self._generate_ref_code()
        super().save(*args, **kwargs)

    def _generate_ref_code(self):
        """تولید کد پیگیری یکتا برای تراکنش"""
        import random
        import string
        while True:
            code = 'TRX' + ''.join(random.choices(string.digits, k=12))
            if not Transaction.objects.filter(ref_code=code).exists():
                return code

# ============================================
# 👈 مدل اخبار (جدید)
# ============================================
class News(models.Model):
    """اخبار و اطلاعیه‌های سایت"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name='عنوان خبر')
    content = models.TextField(verbose_name='متن خبر')
    summary = models.CharField(max_length=500, null=True, blank=True, verbose_name='خلاصه')
    icon = models.CharField(max_length=10, default='📰', verbose_name='آیکون')
    link = models.URLField(null=True, blank=True, verbose_name='لینک')
    image = models.ImageField(upload_to='news/', null=True, blank=True, verbose_name='تصویر')

    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_pinned = models.BooleanField(default=False, verbose_name='سنجاق شده')
    order = models.IntegerField(default=0, verbose_name='ترتیب نمایش')

    publish_date = models.DateTimeField(default=timezone.now, verbose_name='تاریخ انتشار')
    expire_date = models.DateTimeField(null=True, blank=True, verbose_name='تاریخ انقضا')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'news'
        verbose_name = 'خبر'
        verbose_name_plural = 'اخبار'
        ordering = ['-is_pinned', '-publish_date', 'order']
        indexes = [
            models.Index(fields=['is_active', 'publish_date']),
            models.Index(fields=['is_pinned']),
        ]

    def __str__(self):
        return self.title

    def is_valid(self):
        """بررسی اعتبار خبر"""
        if not self.is_active:
            return False
        if self.expire_date and self.expire_date < timezone.now():
            return False
        return True

    def get_relative_date(self):
        """نمایش تاریخ نسبی (امروز، دیروز، ...)"""
        now = timezone.now()
        diff = now - self.publish_date

        if diff.days == 0:
            return 'امروز'
        elif diff.days == 1:
            return 'دیروز'
        elif diff.days == 2:
            return '۲ روز پیش'
        elif diff.days == 3:
            return '۳ روز پیش'
        elif diff.days == 4:
            return '۴ روز پیش'
        elif diff.days < 7:
            return f'{diff.days} روز پیش'
        elif diff.days < 14:
            return 'هفته گذشته'
        elif diff.days < 30:
            return f'{diff.days // 7} هفته پیش'
        else:
            return self.publish_date.strftime('%Y/%m/%d')


class ChatSession(models.Model):
    """مدل ذخیره تاریخچه چت با هوش مصنوعی"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(
        'account_module.Customer',
        on_delete=models.CASCADE,
        related_name='ai_chats',
        verbose_name='مشتری'
    )
    title = models.CharField(max_length=255, default='چت جدید', verbose_name='عنوان چت')

    # تنظیمات چت
    model_name = models.CharField(
        max_length=50,
        default='gpt-4o-mini',
        verbose_name='مدل هوش مصنوعی'
    )

    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    total_messages = models.IntegerField(default=0, verbose_name='تعداد پیام‌ها')
    total_tokens = models.IntegerField(default=0, verbose_name='کل توکن‌های مصرفی')

    # زمان‌بندی
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_chat_sessions'
        verbose_name = 'جلسه چت هوشمند'
        verbose_name_plural = 'جلسات چت هوشمند'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.customer.full_name} - {self.title}"


class ChatMessage(models.Model):
    """مدل ذخیره پیام‌های چت"""

    ROLE_CHOICES = [
        ('user', 'کاربر'),
        ('assistant', 'دستیار'),
        ('system', 'سیستم'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='جلسه چت'
    )

    # محتوای پیام
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, verbose_name='نقش')
    content = models.TextField(verbose_name='متن پیام')

    # اطلاعات اضافی
    tokens_used = models.IntegerField(default=0, verbose_name='توکن مصرفی')
    cost = models.FloatField(default=0, verbose_name='هزینه (دلار)')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_chat_messages'
        verbose_name = 'پیام چت'
        verbose_name_plural = 'پیام‌های چت'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.get_role_display()}: {self.content[:50]}"