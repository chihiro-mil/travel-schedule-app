from django import forms
from .models import User
from django.core.exceptions import ValidationError
import re
from django.contrib.auth import authenticate, get_user_model
from .models import Schedule
from .models import Plan, Link, Picture, TransportationMethod
from datetime import datetime
from django.forms import modelformset_factory
from django.utils import timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.forms import BaseInlineFormSet



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
                raise forms.ValidationError("メールアドレスまたはパスワードが\n正しくありません")
        return self.cleaned_data
    
    def get_user(self):
        return self.user
    
#アカウント設定変更
User = get_user_model()

class ChangeUsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name']
        labels = {'name': '新しいユーザー名'}
        
class ChangeEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        labels = {'email': '新しいメールアドレス'}
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = ''
        
class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = '現在のパスワード'
        self.fields['new_password1'].label = '新しいパスワード'
        self.fields['new_password2'].label = '新しいパスワード(確認）'
        
        self.fields['new_password1'].widget.attrs['placeholder'] = '英数字＋６文字以上'
    
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
    
    def clean(self):
        cleaned_data = super().clean()
        trip_start_date = cleaned_data.get('trip_start_date')
        trip_end_date = cleaned_data.get('trip_end_date')
        
        if not trip_start_date or not trip_end_date:
            self.add_error('trip_start_date', '旅行期間を入力してください')
        
        return cleaned_data
    
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
    departure_location = forms.CharField(
        required=False,
        max_length=24,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'style': 'width: 8em; white-space: pre-wrap; word-break: break-all;'
        })
    )
    arrival_location = forms.CharField(
        required=False,
        max_length=24,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'style': 'width: 8em; white-space: pre-wrap; word-break: break-all;'
        })
    )
    name = forms.CharField(
        required=False,
        max_length=24,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'style': 'width: 8em; white-space: pre-wrap; word-break: break-all;'
        })
    )
    memo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'メモを入力',
            'style': 'width: 15em; white-space: pre-wrap; word-break: break-all;'
        })
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
        
        date_choices = trip_dates or []
        
        self.fields['name'].required = False
        self.fields['start_date'].widget = forms.Select(choices=date_choices)
        self.fields['end_date'].widget = forms.Select(choices=date_choices)
        
        if self.data.get('action_category') == 'meal':
            self.fields['end_date'].required = False
        
        
        if trip_dates:
            date_choices = [(date, date.strftime('%Y-%m-%d')) for date in trip_dates]
            self.fields['start_date'].widget = forms.Select(choices=date_choices)
            self.fields['end_date'].widget = forms.Select(choices=date_choices)
    
    def clean(self):
        cleaned_data = super().clean()
        print("planform.cleand=", cleaned_data)
        
        action_category = cleaned_data.get('action_category')
        name = cleaned_data.get('name')
        if action_category in ["sightseeing", "stay", 'meal']:
            if not name:
                self.add_error('name', '')
        memo = cleaned_data.get('memo')
        departure = cleaned_data.get('departure_location')
        arrival = cleaned_data.get('arrival_location')
        
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_date = cleaned_data.get('end_date')
        if action_category == 'meal':
            if not end_date:
                end_date = start_date
                cleaned_data['end_date'] = start_date
        elif not end_date:
            self.add_error('end_date', '')
        end_time = cleaned_data.get('end_time')
        
        print("[forms.py - clean()] 入力内容:")
        print("category:", action_category)
        print("name:", name)
        print("memo:", memo)
        print("departure_location:", departure)
        print("arrival_location:", arrival)
        print("start_date:", start_date)
        print("start_time:", start_time)
        print("end_date:", end_date)
        print("end_time:", end_time)
        
        
        start_datetime = None
        end_datetime = None
        
        if start_date and start_time:
            start_datetime = datetime.combine(start_date, start_time)
            
        if end_date and end_time:
            end_datetime = datetime.combine(end_date, end_time)
        
        
        if action_category == 'move':
            if not departure:
                self.add_error('departure_location', '出発地を入力してください。')
            if not arrival:
                self.add_error('arrival_location', '到着地を入力してください。')
            
        elif action_category == 'sightseeing':
            if not name:
                self.add_error('name', '観光地名を入力してください。')
            
        elif action_category == 'meal':
            if not name:
                self.add_error('name', '店名を入力してください。')
            
        elif action_category == 'stay':
            if not name:
                self.add_error('name', '宿泊施設を入力してください。')
            
        if action_category != 'meal':
            if start_date and end_date and start_date > end_date:
                    if action_category =='move':
                        self.add_error('start_date', '出発日は到着日より前にしてください。')
                    elif action_category =='sightseeing':
                        self.add_error('start_date', '滞在開始日は終了日より前にしてください。')
                    elif action_category =='stay':
                        self.add_error('start_date', '宿泊の開始日は終了日より前にしてください。')
                
            
        if start_datetime and end_datetime and start_datetime > end_datetime:
                if action_category =='move':
                    self.add_error('start_time', '出発時刻は到着時刻より前にしてください。')
                elif action_category =='sightseeing':
                    self.add_error('start_time', '滞在開始時刻は滞在終了時刻より前にしてください。')
                elif action_category =='meal':
                    self.add_error('start_time', '開始時刻は終了時刻より前にしてください。')
                elif action_category =='stay':
                    self.add_error('start_time', '滞在開始時刻は滞在終了時刻より前にしてください。')
                    
        if start_date and not start_time:
            if action_category == 'move':
                self.add_error('start_time', '出発時刻を入力してください。')
            elif action_category =='sightseeing':
                self.add_error('start_time', '滞在開始時刻を入力してください。')
            elif action_category =='meal':
                self.add_error('start_time', '食事開始時刻を入力してください。')
            elif action_category =='stay':
                self.add_error('start_time', '滞在開始時刻を入力してください。')
                
        if end_date and not end_time:
            if action_category == 'move':
                self.add_error('end_time', '到着時刻を入力してください。')
            elif action_category =='sightseeing':
                self.add_error('end_time', '滞在終了時刻を入力してください。')
            elif action_category =='meal':
                self.add_error('end_time', '食事終了時刻を入力してください。')
            elif action_category =='stay':
                self.add_error('end_time', '滞在終了時刻を入力してください。')
                    
        if start_date and start_time:
            cleaned_data['start_datetime'] = timezone.make_aware(datetime.combine(start_date, start_time))
        else:
            cleaned_data['start_datetime'] =  None
            
        if end_date and end_time:
            cleaned_data['end_datetime'] = timezone.make_aware(datetime.combine(end_date, end_time))
        else:
            cleaned_data['end_datetime'] = None
            
        return cleaned_data
        
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        print("保存前 start_datetime:", self.cleaned_data.get('start_datetime'))
        print("保存前 end_datetime:", self.cleaned_data.get('end_datetime'))
        
        instance.start_datetime = self.cleaned_data.get('start_datetime')
        instance.end_datetime = self.cleaned_data.get('end_datetime')
        if commit:
            instance.save()
            print("保存完了 instance:", instance.start_datetime, instance.end_datetime)
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

LinkFormSet = modelformset_factory(Link, form=LinkForm, extra=5, max_num=5, can_delete=True)


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
PictureFormSet = modelformset_factory(Picture, form=PictureForm, extra=10, max_num=10, can_delete=False)

class BasePictureFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        form.empty_permitted = True
        return form

class BaseLinkFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super()._construct_form(i, **kwargs)
        form.empty_permitted = True
        return form
