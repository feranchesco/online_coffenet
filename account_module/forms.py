from django import forms
from django.core.exceptions import ValidationError

from account_module.models import Customer
from home_module.models import Operator


class OperatorSignupForm(forms.ModelForm):
    specialties = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control',
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
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کامل'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تلفن همراه'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل'}),
            'role': forms.Select(attrs={'class': 'form-control form-select', 'placeholder': 'نقش'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'}),
        }
        error_messages = {
            'username': {
                'required': "لطفاً نام کاربری را وارد کنید"
            },
            'phone': {
                'required': "تلفن همراه را وارد کنید"
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
        duplicate_phon = Operator.objects.filter(phone=user_phone).exists()
        if duplicate_phon:
            raise ValidationError("این تلفن همراه قبلاً در سیستم ثبت شده است.")

        return user_phone

    def clean_username(self):
        entered_username = self.cleaned_data['username']
        duplicate_username = Operator.objects.filter(username=entered_username).exists()
        if duplicate_username:
            raise ValidationError("این نام کاربری قبلاً در سیستم ثبت شده است.")

        return entered_username


class OperatorLoginForm(forms.Form):
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تلفن همراه'}),
        error_messages={
            'required': "لطفاً تلفن همراه خود را وارد کنید."
        }
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'}),
        error_messages={
            'required': "لطفاً رمز خود را وارد کنید."
        }
    )

    def clean(self):
        cleaned_data = super().clean()
        phone = cleaned_data.get('phone')
        password = cleaned_data.get('password')
        operator = Operator.objects.filter(phone=phone).first()
        if not operator or not operator.check_password(password):
            raise ValidationError("شماره ی همراه یا رمز عبور اشتباه است.")
        cleaned_data['operator'] = operator
        return cleaned_data

class CustomerSignupForm(forms.ModelForm):

    class Meta:
        model = Customer
        fields = ['full_name', 'username', 'phone', 'email', 'password']

        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کامل'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'نام کاربری'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'تلفن همراه'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ایمیل'}),
            'password': forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'رمز عبور'}),
        }
        error_messages = {
            'username': {
                'required': "لطفاً نام کاربری را وارد کنید"
            },
            'phone': {
                'required': "تلفن همراه را وارد کنید"
            },
            'email': {
                'required': "ایمیل را وارد کنید"
            },
            'password': {
                'required': "رمز عبور را وارد کنید"
            },
        }

    def clean_phone(self):
        user_phone = self.cleaned_data['phone']
        duplicate_phon = Customer.objects.filter(phone=user_phone).exists()
        if duplicate_phon:
            raise ValidationError("این تلفن همراه قبلاً در سیستم ثبت شده است.")
        return user_phone

    def clean_username(self):
        entered_username = self.cleaned_data['username']
        duplicate_username = Operator.objects.filter(username=entered_username).exists()
        if duplicate_username:
            raise ValidationError("این نام کاربری قبلاً در سیستم ثبت شده است.")

        return entered_username

class CustomerLoginForm(forms.Form):
    phone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'auth-input',
            'id': 'loginPhoneInput',
            'placeholder': '09xxxxxxxxx',
            'type': 'tel',}),
        error_messages={
            'required': "لطفاً تلفن همراه خود را وارد کنید."
        }
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'type':"password", 'class':"auth-input", 'id':"loginPasswordInput",
                       'placeholder':'••••••••'}),
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