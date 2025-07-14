from django import forms
from .models import User
from django.core.exceptions import ValidationError
import re
from django.contrib.auth import authenticate
from .models import Schedule
from .models import Plan, Link, Picture, TransportationMethod


#アカウント登録画面用
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
    
    
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
        password = self.cleaned_data['password']
        if not re.match(r'^(?=.*[a-zA-Z])(?=.*\d)[a-zA-Z\d]+$', password):
            raise ValidationError("パスワードは英字と数字を含めてください。")
        return password
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "パスワードが一致しません。")
            self.add_error(None, "パスワードと確認用パスワードが一致していません。")
            

#ログイン画面用            
class LoginForm(forms.Form):
    email = forms.EmailField(label='メールアドレス')
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput)
    
    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        
        if email and password:
            self.user = authenticate(email=email, password=password)
            if self.user is None:
                return forms.ValidationError("メールアドレスまたはパスワードが正しくありません")
        return self.cleaned_data
    
    def get_user(self):
        return self.user
    
    
#予定表用
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['title', 'trip_start_date', 'trip_end_date']
        
    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) > 50:
            raise forms.ValidationError("タイトルは50文字以内で入力してください。")
        return title
    
#予定本体フォーム用
class PlanForm(forms.ModelForm):
    trip_date = forms.CharField(
        choices=[],
        label="出発日",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    start_time = forms.TimeField(
        label="出発時刻",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': '例：09:00'
        })
    )
    
    end_time = forms.TimeField(
        label="到着時刻",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': '例：18:00'
        })
    )
    
    class Meta:
        model = Plan
        fields = [
            'action_category', 'name',
            'memo', 'departure_location', 'arrival_location'
            ]
        
    def __init__(self, *args, trip_date_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if trip_date_choices:
            self.fields['trip_date'].choices = trip_date_choices
        
#リンクフォーム用
class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['url']
        
#写真フォーム用
class PictureForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields = ['image']
        
#移動手段（移動カテゴリのみ）
class TransportationMethodForm(forms.ModelForm):
    class Meta:
        model = TransportationMethod
        fields = ['transportation']