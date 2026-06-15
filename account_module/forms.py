import re
from django import forms
from django.core.exceptions import ValidationError
from account_module.models import Customer
from home_module.models import Operator


class OperatorSignupForm(forms.ModelForm):
    specialties = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'auth-input',
                'rows': 3,
                'placeholder': 'چاپ، تایپ، طراحی'
            }
        ),
        required=False
    )

    class Meta:
        model = Operator
        fields = ['full_name', 'username', 'phone', 'email', 'role', 'specialties', 'password']

        widgets = {
            'full_name': forms.TextInput(attrs={'type': 'text', 'class': 'auth-input', 'required': '', 'placeholder': 'علی محمدی'}),
            'username': forms.TextInput(attrs={'type': 'text', 'class': 'auth-input', 'required': '', 'placeholder': 'نام کاربری'}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'class': 'auth-input', 'required': '', 'placeholder': '09xxxxxxxxx',
                       'pattern': '09[0-9]{9}'}),
            'email': forms.EmailInput(attrs={'type': 'email', 'class': 'auth-input', 'placeholder': 'ایمیل'}),
            'role': forms.Select(attrs={'class': 'auth-input', 'placeholder': 'نقش'}),
            'password': forms.PasswordInput(attrs={'type': 'password', 'class': 'auth-input', 'placeholder': 'حداقل 4 کاراکتر', 'minlength': 4,
                       'required': '', 'id': 'signupPasswordInput'}),
        }
        error_messages = {
            'username': {
                'required': "لطفاً نام کاربری را وارد کنید",
                'unique':'این نام کاربری قبلاً استفاده شده است.'
            },
            'full_name': {
                'required': "لطفاً نام و نام خانوادگی را وارد کنید"
            },
            'phone': {
                'required': "تلفن همراه را وارد کنید",
                'unique': 'این تلفن همراه قبلاً در سیستم ثبت شده است.'
            },
            'email': {
                'required': "ایمیل را وارد کنید"
            },
            'role': {
                'required': "نقش را انتخاب کنید"
            },
            'password': {
                'required': "رمز عبور را وارد کنید"
            },
        }

    def clean_phone(self):
        user_phone = self.cleaned_data['phone']
        if not re.fullmatch(r'09\d{9}', user_phone):
            raise ValidationError("تلفن همراه نامعتبر است.")
        return user_phone


class OperatorLoginForm(forms.Form):
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'auth-input',
                                      'id': 'loginPhoneInput',
                                      'placeholder': '09xxxxxxxxx',
                                      'type': 'tel',
                                      'required': ''}),
        error_messages={
            'required': "لطفاً تلفن همراه خود را وارد کنید."
        }
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'type': "password", 'class': "auth-input", 'id': "loginPasswordInput",
                                          'placeholder': '••••••••', 'required': ''}),
        error_messages={
            'required': "لطفاً رمز خود را وارد کنید."
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')
        password = cleaned_data.get('password','').strip()
        operator = Operator.objects.filter(phone=phone).first()
        if not operator or not operator.check_password(password):
            raise ValidationError("شماره ی همراه یا رمز عبور اشتباه است.")
        cleaned_data['operator'] = operator
        return cleaned_data


class CustomerSignupForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'phone', 'email', 'password']

        widgets = {
            'full_name': forms.TextInput(
                attrs={'type': 'text', 'class': 'auth-input', 'required': '', 'placeholder': 'علی محمدی'}),
            'phone': forms.TextInput(
                attrs={'type': 'tel', 'class': 'auth-input', 'required': '', 'placeholder': '09xxxxxxxxx',
                       'pattern': '09[0-9]{9}'}),
            'email': forms.EmailInput(
                attrs={'type': 'email', 'class': 'auth-input', 'placeholder': 'ایمیل'}),
            'password': forms.PasswordInput(
                attrs={'type': 'password', 'class': 'auth-input', 'placeholder': 'حداقل 4 کاراکتر', 'minlength': 4,
                       'required': '', 'id': 'signupPasswordInput'}),
        }
        error_messages = {
            'username': {
                'required': "لطفاً نام کاربری را وارد کنید"
            },
            'full_name': {
                'required': "لطفاً نام و نام خانوادگی خود را وارد کنید"
            },
            'phone': {
                'required': "تلفن همراه را وارد کنید"
            },
            'password': {
                'required': "رمز عبور را وارد کنید"
            },
        }

    def clean_phone(self):
        user_phone = self.cleaned_data['phone']
        if not re.fullmatch(r'09\d{9}', user_phone):
            raise ValidationError("تلفن همراه نامعتبر است.")
        return user_phone

    def clean_full_name(self):
        full_name = self.cleaned_data.get('full_name', '').strip()
        if not full_name:
            raise ValidationError("لطفاً نام و نام خانوادگی را وارد کنید.")
        return full_name


class CustomerLoginForm(forms.Form):
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'auth-input',
                                      'id': 'loginPhoneInput',
                                      'placeholder': '09xxxxxxxxx',
                                      'type': 'tel',
                                      'required': ''}),
        error_messages={
            'required': "لطفاً تلفن همراه خود را وارد کنید."
        }
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'type': "password", 'class': "auth-input", 'id': "loginPasswordInput",
                                          'placeholder': '••••••••','required':''}),
        error_messages={
            'required': "لطفاً رمز خود را وارد کنید."
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')
        password = cleaned_data.get('password')
        customer = Customer.objects.filter(phone=phone).first()
        if not customer or not customer.check_password(password):
            raise ValidationError("شماره ی همراه یا رمز عبور اشتباه است.")
        cleaned_data['customer'] = customer
        return cleaned_data
