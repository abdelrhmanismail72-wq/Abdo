from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

class LoginForm(AuthenticationForm):
    username = forms.CharField(label='اسم المستخدم')
    password = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput)

from .models import Lesson, Test, Question
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm

class LessonForm(forms.ModelForm):
    add_test = forms.BooleanField(required=False, label='أضف اختبار مع الدرس')
    class Meta:
        model = Lesson
        fields = ['title', 'lesson_type', 'content', 'video_file', 'pdf_file', 'text_position', 'is_hidden']

class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['title', 'time_limit', 'time_unit', 'prevent_review']

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['text', 'image', 'choices', 'correct_answer']

class AdminSetPasswordForm(SetPasswordForm):
    # wrapper حول SetPasswordForm لتسهيل إعادة تعيين كلمة السر من الداشبورد
    pass

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label=_("البريد الإلكتروني"),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('أدخل البريد الإلكتروني المسجل لدينا'),
            'autocomplete': 'email',
            'dir': 'rtl'
        })
    )

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email']
        labels = {
            'first_name': _('الاسم الأول'),
            'last_name': _('الاسم الأخير'),
            'email': _('البريد الإلكتروني'),
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'dir': 'rtl'}),
        }

class PasswordChangeForm(SetPasswordForm):
    old_password = forms.CharField(
        label=_("كلمة المرور الحالية"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'current-password',
            'class': 'form-control',
            'dir': 'rtl'
        }),
    )
    new_password1 = forms.CharField(
        label=_("كلمة المرور الجديدة"),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'dir': 'rtl'
        }),
        strip=False,
    )
    new_password2 = forms.CharField(
        label=_("تأكيد كلمة المرور الجديدة"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'new-password',
            'class': 'form-control',
            'dir': 'rtl'
        }),
    )

