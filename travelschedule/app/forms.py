from django import forms
from .models import User
from django.core.exceptions import ValidationError
import re
from django.contrib.auth import authenticate
from .models import Schedule
from .models import Plan, Link, Picture, TransportationMethod
from datetime import datetime
from django.forms import modelformset_factory


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
    start_date = forms.ChoiceField(
        choices=[],
        label="開始日",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    start_time = forms.TimeField(
        label="開始時刻",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': '例：09:00'
        })
    )
    end_date = forms.ChoiceField(
        choices=[],
        label="終了日",
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        })
    )
    end_time = forms.TimeField(
        label="終了時刻",
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': '例：18:00'
        })
    )
    transportation = forms.ModelChoiceField(
        queryset=TransportationMethod.objects.all(),
        label="移動手段",
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    transportation = forms.ChoiceField(
        choices=[('徒歩', '徒歩'), ('電車', '電車'), ('新幹線', '新幹線'), ('バス', 'バス'), 
                ('飛行機', '飛行機'), ('車', '車'), ('その他', 'その他')],
        widget=forms.RadioSelect,
        required=False,
        label="移動手段"
    )
    
    class Meta:
        model = Plan
        fields = [
            'action_category', 'name',
            'memo', 'departure_location', 'arrival_location',
            'transportation',
            ]

    def __init__(self, *args, trip_date_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        if trip_date_choices:
            self.fields['start_date'].choices = trip_date_choices
            self.fields['end_date'].choices = trip_date_choices
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_date = cleaned_data.get('end_date')
        end_time = cleaned_data.get('end_time')
        
        if start_date and end_date:
            if start_date > end_date:
                    raise forms.ValidationError(f"到着日は出発日と同じか、それ以降の日付にしてください。")
        
        if start_date and start_time and end_date and end_time:
            try:
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(end_date, end_time)
                
                if start_datetime > end_datetime:
                    raise forms.ValidationError(f"到着時刻は出発時刻より後にしてください。")
        
                cleaned_data['start_datetime'] = datetime.combine(start_date, start_time)
                cleaned_data['end_datetime'] = datetime.combine(end_date, end_time)
                
            except Exception as e:
                raise forms.ValidationError(f"日時の形式が正しくありません。日付と時刻を正しく入力してください。")
            
        return cleaned_data
    
    
#リンクフォーム用
class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['url']
        widgets = {
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '例：https://example.com'
            }),
        }
LinkFormSet = modelformset_factory(Link, form=LinkForm, extra=1, can_delete=True)

#写真フォーム用
class PictureForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields = ['image']
        widgets = {
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control-file'
            }),
        }
PictureFormSet = modelformset_factory(Picture, form=PictureForm, extra=1, can_delete=True)
