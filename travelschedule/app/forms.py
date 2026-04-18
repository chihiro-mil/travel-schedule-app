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

#フォームのバリエーションの役割：ユーザーの入力内容が正しいかチェック

#アカウント登録画面用 from django import formsとfrom .models import Userが必要
class RegisterForm(forms.ModelForm): #forms.ModelFormはDjangoが用意しているクラス モデルと連動してdBに保存できるフォームを自動で作る
    name = forms.CharField( #CharFieldは文字を入力する欄
        max_length=20, #最大文字数
        label='ユーザー名', #HTML上のラベル名
        help_text='', 
        widget=forms.TextInput #入力欄の種類（ここでは普通のテキストボックス）
    )
    
    email = forms.EmailField( #EmailFieldはメールアドレス専用の入力欄
        label='メールアドレス', 
        widget=forms.TextInput
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput, #PasswordInputで入力文字が○○で隠れる
        min_length=8, #8文字以上
        label="パスワード"
    )
    
    password_confirm = forms.CharField(
        widget=forms.PasswordInput, 
        label='パスワード(確認用)'
    )
    
    #ラベル名の後に自動で付くコロンを消すコード
    def __init__(self, *args, **kwargs): #フォーム生成時に自動で実行される初期設定、*args, **kwargsでどんな引数でも受け取る設定
        super().__init__(*args, **kwargs) #親クラス（ModelForm）の初期設定を実行
        self.label_suffix = '' #初期設定を実行した後にラベル名のコロンを消す（フォームが壊れないように）
    
    
    class Meta: #Meta=フォーム全体（RegisterForm）の設定表みたいなもの　※パスワードは暗号化必要のためMeta.fieldsに入れない
        model = User #Userモデル使用するように指示
        fields = ['name', 'email'] #使いたいフィールドを指定。modelsの名前と一致させる
        labels = {
            'name': 'ユーザー名',
            'email': 'メールアドレス',
        } #ラベル名の上書き。modelsの名前と一致させる
        
    #個別の項目チェック emailはEmailField自体にDjangoが自動でチェック
    def clean_name(self): #nameフィールドのチェック
        name = self.cleaned_data['name'] #一時的にクリーンと判断されたデータを入れる辞書。'name'キーを取り出してnameの変数に代入
        if not (1 <= len(name) <= 20): #1文字未満、20文字より多い場合
            raise forms.ValidationError("ユーザー名は１文字以上２０文字以下で入力してください。") #エラーメッセージ表示
        if User.objects.filter(name=name).exists(): #Userテーブルに入力されたnameがすでに存在しているか確認
            raise forms.ValidationError("このユーザー名はすでに使われています。") #エラーメッセージ表示
        return name #問題なければnameを返して、この値を次の処理に渡す
    
    def clean_password(self): #passwordフィールドのチェック
        password = self.cleaned_data['password'] #一時的にクリーンと判断されたデータを入れる辞書。'password'キーを取り出してpasswordの変数に代入
        if len(password) < 8 or not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password): #8文字未満、英数字が１文字も含まれていない。3つのうち1つでも当てはまるとエラー
            raise forms.ValidationError("パスワードは英字と数字を含む８文字以上で入力してください。") #エラーメッセージ表示
        return password #問題なければpasswordを返して、この値を次の処理に渡す
    
    #複数の項目を比較してチェック（パスワード専用チェック）
    def clean(self):
        cleaned_data = super().clean() #まず標準バリエーションを実行
        password = cleaned_data.get("password") #入力されたパスワードを取り出す
        password_confirm = cleaned_data.get("password_confirm") #入力された確認パスワードを取り出す
        
        if password and password_confirm and password != password_confirm: #2つの項目が不一致ならフォーム全体と個別フォームの2つエラーを表示
            self.add_error('password_confirm', "パスワードが一致しません。") #self(RegisterFormのインスタンス)に対してエラー追加。password_confirmにエラーを出す。
            self.add_error(None, "パスワードと確認用パスワードが一致していません。") #None=フォーム全体のエラーpassword_confirmにエラーを出す。
            

#ログイン画面用            
class LoginForm(forms.Form): #普通のフォームを作る宣言　forms.Formなのでモデルとは直接繋がらない、バリエーションや入力チェックを自分で書く
    email = forms.EmailField(label='メールアドレス') #EmailFieldはメールアドレス専用の入力欄 forms.EmailFieldでDjangoが自動的にメール専用の入力欄を作成してくれるため、widgetいらない
    password = forms.CharField(label='パスワード', widget=forms.PasswordInput) #CharFieldは文字を入力する欄
    
    #フォーム全体のチェック関数　emailとパスワードを入力した後、本当にそのユーザーが存在するか確認
    def clean(self):
        email = self.cleaned_data.get('email') #フォームに入力されたemailを取り出す、入力が空の時はNoneが返る
        password = self.cleaned_data.get('password') #フォームに入力されたパスワードを取り出す、入力が空の時はNoneが返る
        
        if email and password: #どちらも入力されている時だけ認証チェック
            self.user = authenticate(email=email, password=password) #authenticate()でDjangoにこのメールとパスワードユーザーは存在するか聞く　パスワードはDjangoが自動でハッシュ比較
            if self.user is None: #emailかパスワードが間違ってる時
                raise forms.ValidationError("メールアドレスまたはパスワードが\n正しくありません")
        return self.cleaned_data #フォームに入力されたデータを返す
    
    def get_user(self): #view側でform.get_user()呼ぶとauthenticateに成功したユーザーが取得できる
        return self.user
    
#アカウント設定変更
User = get_user_model() #今使われているUserモデルを取得するため。Djangoの標準Userなら標準Userを返す、カスタムUserならカスタムUserを返す

#ユーザー名変更
class ChangeUsernameForm(forms.ModelForm):
    name = forms.CharField(
        max_length=20,
        label='新しいユーザー名',
        error_messages={
            'required': 'ユーザー名は必須です。',
            'max_length': 'ユーザー名は１文字以上２０文字以下で入力してください。',
        }
    )
    class Meta:
        model = User #どのフォームを使うか→User
        fields = ['name'] #どの項目をフォームで使うか→name
        
    #dif__init__で編集画面で現在のユーザー名を入力欄に最初から入れておくための関数
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.name: #viewsでform = ChangeUsernameForm(instance=request.user)を渡してログインしているユーザー情報が入ってくる
            self.fields['name'].initial = self.instance.name #instance.name（現在の名前）をself.fields['name'].initialとして初期値にしている
        
#メールアドレス変更 設定内容はユーザー名変更とほぼ同じ
class ChangeEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        labels = {'email': '新しいメールアドレス'}
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].initial = ''
        
#パスワード変更 Djangoの標準のCustomPasswordChangeFormを拡張してバリエーション強化したフォーム
class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_old_password(self): #現在のパスワードが正しいか
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password): #self.user.check_password()で現在のパスワードと一致するかチェック
            raise ValidationError("現在のパスワードが間違っています。") #間違いならエラー
        return old_password
    
    def clean_new_password1(self): #新しいパスワード１のチェック
        password = self.cleaned_data.get('new_password1')
        if len(password) < 8: #文字数チェック
            raise ValidationError("このパスワードは短すぎます。")
        
        if not any(c.isalpha() for c in password) or not any(c.isalpha() for c in password): #英数字チェック
            raise ValidationError("このパスワードは英字と数字を含めてください。")
        
        if password.lower() in ["password", "password123", "12345678"]: #弱いパスワードチェック
            raise ValidationError("このパスワードは一般的すぎます。")

        return password
    
    def clean_new_password2(self): #新しいパスワード２のチェック（確認用）
        password2 = self.cleaned_data.get('new_password2')
        
        if not password2:
            raise ValidationError("確認用のパスワードを入力してください。")
        
        if len(password2) < 8: #文字数チェック
            raise ValidationError("このパスワードは短すぎます。")
        
        if not any(c.isalpha() for c in password2) or not any(c.isalpha() for c in password2): #英数字チェック
            raise ValidationError("このパスワードは英字と数字を含めてください。")
        
        if password2.lower() in ["password", "password123", "12345678"]: #弱いパスワードチェック
            raise ValidationError("このパスワードは一般的すぎます。")

        return password2

    def clean(self): #clean()で複数のフォームを比較してチェック
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if old_password and new_password1 and old_password == new_password1: #old_password and new_password1で両方の入力が存在する時だけチェック開始されるようになっている
            self.add_error('new_password1', "新しいパスワードは現在のパスワードと同じにできません。") #現在のパスワードと新しいパスワードが同じならエラー
        
        if new_password1 and new_password2 and new_password1 != new_password2: #新しいパスワード１と新しいパスワード２が違ったらエラー
            self.add_error('new_password2', "新しいパスワードと確認用パスワードが一致していません。")
        return cleaned_data
    
#予定表用
class ScheduleForm(forms.ModelForm): #フォームの設計図のクラス　ScheduleモデルをもとにHTMLフォームを自動で作ってくれるModelForm
    class Meta: #フォームがScheduleモデルのどの項目を使うかを指定する
        model = Schedule #Scheduleモデルとセットで動くという宣言
        fields = ['title', 'trip_start_date', 'trip_end_date'] #その中で、旅行タイトル、旅行開始日、旅行終了日のフォームだけをフォームに使うように
        #widgetsでフォームの見た目や属性を細かく設定
        widgets = {
            'title': forms.TextInput(attrs={
                'maxlength': 20,
                'class': 'trip-title',
                'style': 'width: 10em; white-space: pre-wrap; word-break: break-all;'
            }),
        }
        #'title': forms.TextInputでシンプルなテキストボックスとして表示
    #タイトルフィールド単体のチェック
    def clean_title(self): #タイトル専用のチェック　'maxlength': 20だけのチェックだとブラウザが対応していない場合や悪意のあるアクセスは突破されてしまう
        title = self.cleaned_data['title'] #ユーザーが入力したタイトルを取り出す
        if len(title) > 20: #もし20文字より多かったら下記エラーメッセージ表示
            raise forms.ValidationError("タイトルは20文字以内で入力してください。")
        return title #問題なければそのままタイトルをきれいな値として返す
    
    #フォーム全体のチェック　複数のフィールドの組み合わせでチェック
    def clean(self):
        cleaned_data = super().clean() #親クラス（ModelForm）のclean()を呼び出して、Djangoが通常やるチェック（必須、型チェック）を全部実行。その結果がcleaned_dataに返る
        #必要な値を取り出す
        trip_start_date = cleaned_data.get('trip_start_date')
        trip_end_date = cleaned_data.get('trip_end_date')
        
        if not trip_start_date or not trip_end_date: #どちらか片方でも空（None）の場合、trip_start_dateフィールドにエラーメッセージ表示
            self.add_error('trip_start_date', '旅行期間を入力してください') #self.add_error(フィールド名,　メッセージ)は特定のフィールドにエラーを付ける便利メゾット
        
        return cleaned_data #問題がなければそのままcleaned_data返す
    
#予定本体フォーム用

#予定カテゴリの選択肢一覧　（DBに保存される値, 画面に表示されるラベル）
ACTION_CATEGORY_CHOICES = [
    ('move', '移動'),
    ('sightseeing', '観光地'),
    ('meal', '食事'),
    ('stay', '宿泊'),
]

#planモデル用の入力フォーム　予定追加、編集の両方
class PlanForm(forms.ModelForm):
    #カテゴリ　ChoiceField：選択肢から１つ選ぶフィールド　choices：上記で定義したカテゴリ一覧を使用　RadioSelect：ラジオボタン（カテゴリを並べて表示するため）
    action_category = forms.ChoiceField(
        choices=ACTION_CATEGORY_CHOICES,
        label='',
        widget=forms.RadioSelect(attrs={'class': 'category-radio'})
    )
    #移動手段　ModelChoiceField：外部キー用のフォーム　queryset：DBに入っている移動手段全部取得　required=False：移動カテゴリ以外では使わないので必須にしない　
    transportation = forms.ModelChoiceField(
        queryset=TransportationMethod.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'transport-select'}),
        empty_label=None,
        label=''
    )
    #出発地
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
    #到着地
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
    #start_dateやstart_timeなど、モデルにないフィールドでもフォーム作成してOK　viewsでdatetimeとしてまとめている
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
    
    #このフォームはどのモデルをどのフィールドで扱うか
    class Meta:
        model = Plan
        fields = [
            'action_category', 'name',
            'memo', 'departure_location', 'arrival_location',
            'transportation', 'start_date', 'start_time', 'end_date', 'end_time'
        ]

    #フォームのカスタマイズ
    #initで画面の状態に応じてフォームの振る舞いを動的に変える処理　フォームの初期化をしてからカスタマイズ開始
    def __init__(self, *args, trip_dates=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        #日付の候補を受け取る
        date_choices = trip_dates or []
        
        #nameは未入力OK、start_dateとend_dateはSelectにする
        self.fields['name'].required = False
        self.fields['start_date'].widget = forms.Select(choices=date_choices)
        self.fields['end_date'].widget = forms.Select(choices=date_choices)
        
        #食事カテゴリの時はend_date不要
        if self.data.get('action_category') == 'meal':
            self.fields['end_date'].required = False
        
        #trip_datesがある場合はchoicesを作り直す
        if trip_dates:
            date_choices = [
                (d.isoformat(), d.strftime('%Y-%m-%d'))
                for d in trip_dates
            ]
            #Selectを正式にセットし直す　旅行期間が確定した後の本命
            self.fields['start_date'].widget = forms.Select(choices=date_choices)
            self.fields['end_date'].widget = forms.Select(choices=date_choices)
            
            self.fields['start_date'].input_fprmats = ['%Y-%m-%d']
            self.fields['end_date'].input_fprmats = ['%Y-%m-%d']
            
        #フォームで選んでいるaction_categoryをどんな状況でも１つ取り出すコード（新規作成、入力してPOSTした後のエラー、編集）
        cat = (
            self.data.get('action_category')#入力してPOSTした後のエラーの時
            or self.initial.get('action_category')#新規作成の時
            or getattr(self.instance, 'action_category', None)#編集の時　self.instance＝編集対象のplanモデル
        )
        #移動カテゴリの時はtransportationを必須
        if cat =='move':
            self.fields['transportation'].required = True
            self.fields['transportation'].widget.attrs.pop('style', None)
        #移動カテゴリ以外はtransportationを必須にしない
        else:
            self.fields['transportation'].required = False
    
    #保存前の最終チェック
    def clean(self):
        cleaned_data = super().clean()#Djangoが標準でやってくれる基本チェック→その結果がcleaned_dataに入る
        
        #カテゴリと名前のチェック
        action_category = cleaned_data.get('action_category')
        name = cleaned_data.get('name')
        #観光、宿泊、食事の時はnameを必須にする
        if action_category in ["sightseeing", "stay", 'meal']:
            if not name:
                self.add_error('name', '')
        #変数にして読みやすくしている
        memo = cleaned_data.get('memo')
        departure = cleaned_data.get('departure_location')
        arrival = cleaned_data.get('arrival_location')
        
        start_date = cleaned_data.get('start_date')
        start_time = cleaned_data.get('start_time')
        end_date = cleaned_data.get('end_date')
        #食事カテゴリの時は開始日と終了日を同じ日に自動補完する
        if action_category == 'meal':
            if not end_date:
                end_date = start_date
                cleaned_data['end_date'] = start_date
        #食事カテゴリ以外はend_dateが空ならエラー（条件付きの残りのため、elifを使う）
        elif not end_date:
            self.add_error('end_date', '')
        end_time = cleaned_data.get('end_time')
        
        #移動カテゴリの時の移動手段は必須（initと二重にチェック）
        if (cleaned_data.get('action_category') or self.data.get('action_category')) == 'move' \
            and not cleaned_data.get('transportation'):
                self.add_error('transportation', '移動手段を選択してください')
        
        #いったん空にしておく　後で条件分岐しても変数が存在しないというエラーにならない
        start_datetime = None
        end_datetime = None
        
        #日づけと時刻が揃っている時だけdatetimeを作成　datetime.combine()で結合
        if start_date and start_time:
            start_datetime = datetime.combine(start_date, start_time)
            
        if end_date and end_time:
            end_datetime = datetime.combine(end_date, end_time)
        
        #ここからカテゴリ別の必須チェック
        #カテゴリは必ずどれか１つ選択する仕様　例）moveを処理したらsightseeingは見ない、sightseeingを処理したらmealは見ない
        
        #移動カテゴリの時：出発地と到着地を必須
        if action_category == 'move':
            if not departure:
                self.add_error('departure_location', '出発地を入力してください。')
            if not arrival:
                self.add_error('arrival_location', '到着地を入力してください。')
        
        #観光、食事、宿泊カテゴリの時：名前を必須でエラーメッセージは別にする
        elif action_category == 'sightseeing':
            if not name:
                self.add_error('name', '観光地名を入力してください。')
            
        elif action_category == 'meal':
            if not name:
                self.add_error('name', '店名を入力してください。')
            
        elif action_category == 'stay':
            if not name:
                self.add_error('name', '宿泊施設を入力してください。')
            
        #meal以外は日付の範囲チェックする
        if action_category != 'meal':
            if start_date and end_date and start_date > end_date: #開始日＞終了日の時のエラーメッセージ
                    if action_category =='move':
                        self.add_error('start_date', '出発日は到着日より前にしてください。')
                    elif action_category =='sightseeing':
                        self.add_error('start_date', '滞在開始日は終了日より前にしてください。')
                    elif action_category =='stay':
                        self.add_error('start_date', '宿泊の開始日は終了日より前にしてください。')
                
        #開始時刻＞終了時刻の時のエラーメッセージ
        if start_datetime and end_datetime and start_datetime > end_datetime:
                if action_category =='move':
                    self.add_error('start_time', '出発時刻は到着時刻より前にしてください。')
                elif action_category =='sightseeing':
                    self.add_error('start_time', '滞在開始時刻は滞在終了時刻より前にしてください。')
                elif action_category =='meal':
                    self.add_error('start_time', '開始時刻は終了時刻より前にしてください。')
                elif action_category =='stay':
                    self.add_error('start_time', '滞在開始時刻は滞在終了時刻より前にしてください。')
                    
        #開始日は入力しているのに開始時刻が空の時のエラーメッセージ
        if start_date and not start_time:
            if action_category == 'move':
                self.add_error('start_time', '出発時刻を入力してください。')
            elif action_category =='sightseeing':
                self.add_error('start_time', '滞在開始時刻を入力してください。')
            elif action_category =='meal':
                self.add_error('start_time', '食事開始時刻を入力してください。')
            elif action_category =='stay':
                self.add_error('start_time', '滞在開始時刻を入力してください。')
                
        #終了日は入力しているのに終了時刻が空の時のエラーメッセージ
        if end_date and not end_time:
            if action_category == 'move':
                self.add_error('end_time', '到着時刻を入力してください。')
            elif action_category =='sightseeing':
                self.add_error('end_time', '滞在終了時刻を入力してください。')
            elif action_category =='meal':
                self.add_error('end_time', '食事終了時刻を入力してください。')
            elif action_category =='stay':
                self.add_error('end_time', '滞在終了時刻を入力してください。')
                    
        #開始日と開始時刻が入力されていたら、start_datetimeを作る　
        if start_date and start_time:
            cleaned_data['start_datetime'] = timezone.make_aware(datetime.combine(start_date, start_time))
        else:
            cleaned_data['start_datetime'] =  None
            
        #終了日と終了時刻が入力されていたら、end_datetimeを作る
        if end_date and end_time:
            cleaned_data['end_datetime'] = timezone.make_aware(datetime.combine(end_date, end_time))
        else:
            cleaned_data['end_datetime'] = None
            
        return cleaned_data #最終的に整えたデータをDjangoに返す
        
    #datetimeを分解して結合したデータは普通にModelFormに保存しても入らない→clean()で作ったcleaned_dataをsave()でinstanceに手動でセット
    def save(self, commit=True):
        instance = super().save(commit=False) #ここではフォーム入力からplanのインスタンスは作るが、DBにはまだ保存しない
        
        instance.start_datetime = self.cleaned_data.get('start_datetime')
        instance.end_datetime = self.cleaned_data.get('end_datetime')
        if commit:
            instance.save()
        return instance
    

    
#リンクフォーム用
#LinkForm（1件分のリンク入力フォーム）
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
    #URLは任意にする設定
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url'].required = False
        
#リンク全体の管理(複数のLinkFormをまとめて管理)　削除、空欄、入力ルールもまとめてチェック
class BaseLinkFormSet(BaseInlineFormSet):
    can_delete = True
    
    #新規追加用のフォームは空でもOKにする　既存データのフォームは対象外
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            if not form.instance.pk:
                form.empty_permitted = True
    
    #全リンクフォームを１つずつチェック
    def clean(self):
        super().clean()
        for form in self.forms:
            if not hasattr(form, "cleaned_data"): #Djangoがスキップしたフォームは触らない
                continue
            
            if form.cleaned_data.get('DELETE'): #削除対象は無視　削除チェックが入ったものはバリエーション不要
                continue
            #入力値を取得
            title = form.cleaned_data.get("title")
            url = form.cleaned_data.get("url")
            
            #両方空なら存在しないものとしてスキップ
            if not title and not url:
                continue
            #タイトルだけあってURLがない場合はエラー
            if title and not url:
                form.add_error("url", "ＵＲＬを入力してください。")



#写真フォーム用
#PictureForm（1件分の写真入力フォーム）
class PictureForm(forms.ModelForm):
    class Meta:
        model = Picture
        fields = ['image']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control-file'
            }),
        }
    #新規追加用のフォームは空でもOKにする　既存データのフォームは対象外
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['image'].required = False
        
#写真全体の管理(複数のPictureFormをまとめて管理)　削除、空欄、入力ルールもまとめてチェック
class BasePictureFormSet(BaseInlineFormSet):
    can_delete = True
    
    def  __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for form in self.forms:
            form.empty_permitted = True