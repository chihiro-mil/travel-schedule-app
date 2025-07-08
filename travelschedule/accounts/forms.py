from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re


class RegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=20, 
        label='ユーザー名', 
        help_text='',
        widget=forms.TextInput(attrs={
            'placeholder': '１文字２０文字以下',
            'class': 'input-field'
        })
    )
    
    email = forms.EmailField(
        label='メールアドレス', 
        widget=forms.TextInput(attrs={
            'placeholder': '〇〇〇＠〇〇.〇〇',
            'class': 'input-field'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': '英数字＋６文字以上',
            'class': 'input-field'
        }),
        min_length=6, 
        label="パスワード"
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-field'
        }), 
        label='パスワード(確認用)'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        labels = {
            'username': 'ユーザー名',
            'email': 'メールアドレス',
            'password': 'パスワード',
        }
        
    def clean_username(self):
        username = self.cleaned_data['username']
        if not (1 <= len(username) <= 20):
            raise ValidationError("ユーザー名は１文字以上２０文字以下で入力してください。")
        return username
    
    def clean_password(self):
        password = self.cleaned_password['password']
        if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]+$', password):
            raise ValidationError("パスワードは英字と数字を含めてください。")
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "パスワードが一致しません。")