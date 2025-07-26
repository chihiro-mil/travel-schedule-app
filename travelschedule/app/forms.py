from django import forms
from .models import User
from django.core.exceptions import ValidationError
import re
from django.contrib.auth import authenticate
from .models import Schedule
from .models import Plan, Link, Picture, TransportationMethod
from datetime import datetime
from datetime import date
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


ACTION_CATEGORY_CHOICES = [
    ('move', '移動'),
    ('sightseeing', '観光地'),
    ('meal', '食事'),
    ('stay', '宿泊'),
]

class PlanForm(forms.ModelForm):
    action_category = forms.ChoiceField(
        choices=ACTION_CATEGORY_CHOICES,
        label='',
        widget=forms.RadioSelect(attrs={'class': 'category-radio'})
    )
    transportation = forms.ModelChoiceField(
        queryset=TransportationMethod.objects.all(),
        required=False,
        widget=forms.Select(attrs={'style': 'display:none;'}),
        empty_label=None
    )
    start_date = forms.DateField()
    end_date = forms.DateField()
    
    start_date = forms.DateField(
        widget=forms.Select(),
        input_formats=['%Y-%m-%d'],
        required=False,
        label='開始日',
    )
    start_time = forms.TimeField(
        label='開始時刻',
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': '例：09:00'
        })
    )
    end_date = forms.DateField(
        widget=forms.Select(),
        input_formats=['%Y-%m-%d'],
        required=False,
        label='終了日',
    )
    end_time = forms.TimeField(
        label='終了時刻',
        required=False,
        widget=forms.TimeInput(attrs={
            'type': 'time',
            'class': 'form-control',
            'placeholder': '例：18:00'
        })
    )
    
    start_date = forms.DateField()
    end_date = forms.DateField()
    
    class Meta:
        model = Plan
        fields = [
            'action_category', 'name',
            'memo', 'departure_location', 'arrival_location',
            'transportation', 'start_date', 'start_time', 'end_date', 'end_time'
        ]

    def __init__(self, *args, trip_dates=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if trip_dates:
            date_choices = [(date, date.strftime('%Y-%m-%d')) for date in trip_dates]
            self.fields['start_date'].widget = forms.Select(choices=date_choices)
            self.fields['end_date'].widget = forms.Select(choices=date_choices)
            
    def clean_action_category(self):
        value = self.cleaned_data.get('action_category')
        if not value:
            raise forms.ValidationError("カテゴリを選択してください")
        return value
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_date = cleaned_data.get('end_date')
        end_time = cleaned_data.get('end_time')
        
        print("clean()内の値確認：")
        print("start_date =", start_date)
        print("start_time =", start_time)
        print("end_date =", end_date)
        print("end_time =", end_time)
        
        if start_date and start_time and end_date and end_time:
            try:
                print("combine開始")
                start_datetime = datetime.combine(start_date, start_time)
                end_datetime = datetime.combine(end_date, end_time)
                print("combine成功")
                
                if start_datetime > end_datetime:
                    print("! start_datetime:", start_datetime)
                    print("! end_datetime:", end_datetime)
                    raise forms.ValidationError(f"到着時刻は出発時刻より後にしてください。")
        
                cleaned_data['start_datetime'] = datetime.combine(start_date, start_time)
                cleaned_data['end_datetime'] = datetime.combine(end_date, end_time)
                print("cleaned_data 格納完了")
                
            except Exception as e:
                print("例外発生:", e)
                raise forms.ValidationError(f"日時の形式が正しくありません。日付と時刻を正しく入力してください。")
            
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.start_datetime = self.cleaned_data.get('start_datetime')
        instance.end_datetime = self.cleaned_data.get('end_datetime')
        if commit:
            instance.save()
        return instance
    
    
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
