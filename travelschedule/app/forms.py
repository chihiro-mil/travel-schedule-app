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
from django.forms import inlineformset_factory
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import validate_password



#アカウント登録画面用
class RegisterForm(forms.ModelForm):
    username = forms.CharField(
        max_length=20, 
        label='ユーザー名', 
        help_text='',
        widget=forms.TextInput
    )
    
    email = forms.EmailField(
        label='メールアドレス', 
        widget=forms.TextInput
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput,
        min_length=8, 
        label="パスワード"
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, 
        label='パスワード(確認用)'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = ''
    
    
    class Meta:
        model = User
        fields = ['username', 'email']
        labels = {
            'name': 'ユーザー名',
            'email': 'メールアドレス',
        }
        
    def clean_username(self):
        username = self.cleaned_data['username']
        if not (1 <= len(username) <= 20):
            raise forms.ValidationError("ユーザー名は１文字以上２０文字以下で入力してください。")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("このユーザー名はすでに使われています。")
        return username
    
    def clean_password(self):
        password = self.cleaned_data['password']
        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise forms.ValidationError("パスワードは英字と数字を含む８文字以上で入力してください。")
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
        fields = ['username']
        labels = {'username': '新しいユーザー名'}
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.username:
            self.fields['username'].initial = self.instance.username
        
class ChangeEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        labels = {'email': '新しいメールアドレス'}
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = ''
        
class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError("元のパスワードが間違っています。")
        return old_password
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if len(password) < 8:
            raise ValidationError("このパスワードは短すぎます。")
        
        if not any(c.isalpha() for c in password) or not any(c.isalpha() for c in password):
            raise ValidationError("このパスワードは英字と数字を含めてください。")
        
        if password.lower() in ["password", "password123", "12345678"]:
            raise ValidationError("このパスワードは一般的すぎます。")

        return password
    
    def clean_new_password2(self):
        password2 = self.cleaned_data.get('new_password2')
        
        if not password2:
            raise ValidationError("確認用のパスワードを入力してください。")
        
        if len(password2) < 8:
            raise ValidationError("このパスワードは短すぎます。")
        
        if not any(c.isalpha() for c in password2) or not any(c.isalpha() for c in password2):
            raise ValidationError("このパスワードは英字と数字を含めてください。")
        
        if password2.lower() in ["password", "password123", "12345678"]:
            raise ValidationError("このパスワードは一般的すぎます。")

        return password2

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if old_password and new_password1 and old_password == new_password1:
            self.add_error('new_password1', "新しいパスワードは現在のパスワードと同じにできません。")
        
        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', "新しいパスワードと確認用パスワードが一致していません。")
        return cleaned_data
    
#予定表用
class ScheduleForm(forms.ModelForm):
    class Meta:
        model = Schedule
        fields = ['title', 'trip_start_date', 'trip_end_date']
        widgets = {
            'title': forms.TextInput(attrs={
                'maxlength': 20,
                'class': 'trip-title',
                'style': 'width: 10em; white-space: pre-wrap; word-break: break-all;'
            }),
        }
    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) > 20:
            raise forms.ValidationError("タイトルは20文字以内で入力してください。")
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
        widget=forms.Select(attrs={'class': 'transport-select'}),
        empty_label=None,
        label=''
    )
    departure_location = forms.CharField(
        required=False,
        max_length=24,
        widget=forms.TextInput(attrs={
            'style': 'width: 8em;',
            'maxlength': '24',
            'onbeforeinput': (
                "const m=24;"
                "const t=this;"
                "const et=event;"
                "if(!et.inputTyoe) return;"
                "const ins = et.inputTyoe.startsWith('insert');"
                "if(!ins) return;"
                "const sel=t.selectionEnd - t.selectionStart;"
                "const add=(et.data||'').length;"
                "const newLen=t.value.length - sel + add;"
                "if(newLen>m){ et.preventDefault(); }"
            ),
            'oninput': "if(this.value.length>24){this.value=this.value.slice(0,24)}",
            'oncompositionend': "if(this.value.length>24){this.value=this.value.slice(0,24)}",
        })
    )
    arrival_location = forms.CharField(
        required=False,
        max_length=24,
        widget=forms.TextInput(attrs={
            'style': 'width: 8em;',
            'maxlength': '24',
            'onbeforeinput': (
                "const m=24;"
                "const t=this;"
                "const et=event;"
                "if(!et.inputTyoe) return;"
                "const ins = et.inputTyoe.startsWith('insert');"
                "if(!ins) return;"
                "const sel=t.selectionEnd - t.selectionStart;"
                "const add=(et.data||'').length;"
                "const newLen=t.value.length - sel + add;"
                "if(newLen>m){ et.preventDefault(); }"
            ),
            'oninput': "if(this.value.length>24){this.value=this.value.slice(0,24)}",
            'oncompositionend': "if(this.value.length>24){this.value=this.value.slice(0,24)}",
        })
    )
    name = forms.CharField(
        required=False,
        max_length=24,
        widget=forms.TextInput(attrs={
            'style': 'width: 8em;',
            'maxlength': '24',
            'onbeforeinput': (
                "const m=24;"
                "const t=this;"
                "const et=event;"
                "if(!et.inputTyoe) return;"
                "const ins = et.inputTyoe.startsWith('insert');"
                "if(!ins) return;"
                "const sel=t.selectionEnd - t.selectionStart;"
                "const add=(et.data||'').length;"
                "const newLen=t.value.length - sel + add;"
                "if(newLen>m){ et.preventDefault(); }"
            ),
            'oninput': "if(this.value.length>24){this.value=this.value.slice(0,24)}",
            'oncompositionend': "if(this.value.length>24){this.value=this.value.slice(0,24)}",
        })
    )
    memo = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'maxlength': 150,
            'rows': 5,
            'style': 'width: 15em; white-space: pre-wrap; word-break: break-all;'
        })
    )
    #start_date = forms.DateField()
    #end_date = forms.DateField()
    
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
            date_choices = [
                (d.isoformat(), d.strftime('%Y-%m-%d'))
                for d in trip_dates
            ]
            self.fields['start_date'].widget = forms.Select(choices=date_choices)
            self.fields['end_date'].widget = forms.Select(choices=date_choices)
            
            self.fields['start_date'].input_fprmats = ['%Y-%m-%d']
            self.fields['end_date'].input_fprmats = ['%Y-%m-%d']
            
        cat = (
            self.data.get('action_category')
            or self.initial.get('action_category')
            or getattr(self.instance, 'action_category', None)
        )
        if cat =='move':
            self.fields['transportation'].required = True
            self.fields['transportation'].widget.attrs.pop('style', None)
        else:
            self.fields['transportation'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        
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
        
        if (cleaned_data.get('action_category') or self.data.get('action_category')) == 'move' \
            and not cleaned_data.get('transportation'):
                self.add_error('transportation', '移動手段を選択してください')
        
        
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
        
        instance.start_datetime = self.cleaned_data.get('start_datetime')
        instance.end_datetime = self.cleaned_data.get('end_datetime')
        if commit:
            instance.save()
        return instance
    

    
#リンクフォーム用
class LinkForm(forms.ModelForm):
    class Meta:
        model = Link
        fields = ['title', 'url']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'タイトル(任意・16文字まで)',
                'maxlength': 16,
            }),
            'url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '例：https://example.com'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url'].required = False
        
class BaseLinkFormSet(BaseInlineFormSet):
    can_delete = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            if not form.instance.pk:
                form.empty_permitted = True
    
    def clean(self):
        super().clean()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            
            if form.cleaned_data.get('DELETE'):
                continue
            
            title = form.cleaned_data.get("title")
            url = form.cleaned_data.get("url")
            
            if not title and not url:
                continue
            if title and not url:
                form.add_error("url", "ＵＲＬを入力してください。")



#写真フォーム用
class PictureForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['image'].required = False
        
class BasePictureFormSet(BaseInlineFormSet):
    can_delete = True
    
    def  __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = True