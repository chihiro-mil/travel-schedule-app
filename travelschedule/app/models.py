# AbstractUser:Djangoのユーザーモデルをカスタマイズするためのベースクラス
# BaseUserManager:ユーザーを作る方法を管理するマネージャー
# PermissionsMixin:権限機能機能を追加するMixin
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin

# Djangoのモデル（テーブル作成の仕組み）を使う基本セット
from django.db import models

# ユーザーテーブル

# UserManagerでユーザー作成処理をまとめるクラス
# create_user/ create_superuser を定義する
# passwordのハッシュ化などユーザー作成ルールを管理する
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields): # create_user:一般ユーザー作成のための関数
        if not email: # メールアドレスが空欄の場合
            raise ValueError('メールアドレスは必須です') # エラーを出す
        email = self.normalize_email(email) # メールアドレスを標準化する
        user = self.model(email=email, name=name, **extra_fields) # self.model はこのManagerが管理しているモデル（User）
        user.set_password(password) # セキュリティ対策のためパスワードをハッシュ化
        user.save(using=self._db) # Userオブジェクトをデータベースに保存
        return user #作ったユーザーを返す
    def create_superuser(self, email, name, password=None, **extra_fields): #create_superuser:管理者ユーザー作成のための関数
        extra_fields.setdefault('is_staff', True) # is_staff(スタッフ権限)をTrueにする
        extra_fields.setdefault('is_superuser', True) # is_superuserで最上位の管理者(スタッフ権限より上)であることを示す
        return self.create_user(email, name, password, **extra_fields) # 特別なフラグを付けて、あとはcreate_userに任せる

#ユーザーの入れ物
class User(AbstractUser, PermissionsMixin): # AbstractUserをベースにカスタマイズユーザーモデルを作る。主キーのidはDjangoが自動作成、パスワードカラムはAbstractUserで継承しているのでコード記入不要
    name = models.CharField(max_length=20, unique=False) # unique=False でユーザー同士で同じ名前ok
    email = models.EmailField(max_length=255, unique=True) # unique=True でユーザー同士で被らないように
    created_at = models.DateTimeField(auto_now_add=True) # 作成日時
    updated_at = models.DateTimeField(auto_now=True) # 更新日時
    
    USERNAME_FIELD = 'email' # 認証でログインIDとして扱うフィールドをemailにする
    REQUIRED_FIELDS = ['name'] #管理者アカウント作成時はemailとnameが必要と宣言
    
    objects = UserManager() #UserManagerに紐づけ
    
    class Meta:
        db_table = 'users' #データベースに作られるテーブル名を指定
        
        
#予定表テーブル
class Schedule(models.Model): #Scheduleは予定1つ分を表すテーブル
    user = models.ForeignKey('app.User', on_delete=models.CASCADE) #ログインユーザーと結びつく。on_delete=models.CASCADEでユーザーが削除されればユーザーの旅行も削除
    title = models.CharField(max_length=50) #旅行タイトル
    trip_start_date = models.DateField() #旅行開始日
    trip_end_date = models.DateField() #旅行終了日
    
    created_at = models.DateTimeField(auto_now_add=True) #作成日時
    updated_at = models.DateTimeField(auto_now=True) #更新日時
    
    def __str__(self): #__str__でこのモデルを文字として見せる時の代表　admin画面、テンプレート、シェルのprintなどの時
        return self.title
    
#予定テーブル
class Plan(models.Model): #Planは予定表の中の1つ1つの予定を表すテーブル
    #action_categoryに入れられる選択肢 DBには'move'など英語表記、表示画面では'移動'と日本語表示
    #選択肢や設定値は先に定義してフィールドは後で書く　再利用などの利点あるため
    CATEGORY_CHOICES = [
        ('move', '移動'),
        ('sightseeing', '観光'),
        ('meal', '食事'),
        ('stay', '宿泊'),
    ]
    #scheduleとの関係　schedule = models.ForeignKey('Schedule',でschedule_idカラムが自動で追加　on_delete=models.CASCADEで予定表が消去されたら、その中の予定も消える　related_name='plans'でこの予定一覧が取れる
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE, related_name='plans')
    action_category = models.CharField(
        max_length=20, #保存されるデータの文字数にのため、予定カテゴリについては'move'などの文字数になる
        choices=CATEGORY_CHOICES, #CATEGORY_CHOICESを選択フィールドにする
        blank=True #デフォルトはblank=Falseになっているためあえてblank=Trueに設定（柔軟性高める）　models以外で設定を厳しくする
    )
    #transportation = models.ForeignKey('TransportationMethod',で選択肢を別のテーブルから参照
    transportation = models.ForeignKey(
        'TransportationMethod',
        on_delete=models.SET_NULL, #移動手段が消えても予定は消さずにtransportationをNoneにする
        null=True, #transportation_idが空でもOK
        blank=True, #フォーム未選択OK
        related_name='plans' #related_name='plans'でこの移動手段を使っている予定一覧が取れる
    )
    name = models.CharField(max_length=24, blank=True, null=True)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    memo = models.TextField(blank=True, null=True)
    departure_location = models.CharField(max_length=24, blank=True, null=True)
    arrival_location = models.CharField(max_length=24, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    #管理者画面でplanデータを分かりやすくする　下記のプリント実行で東京（移動）と表示
    def __str__(self):
        return f"{self.name} ({self.get_action_category_display()})"
    
#リンクテーブル
class Link(models.Model):
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='links') #どの予定のリンクか紐づけ on_delete=models.CASCADEで予定削除でリンクも削除
    title = models.CharField(max_length=16, blank=True, default='')
    url = models.URLField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.url or self.title or ''
    
#写真テーブル
class Picture(models.Model):
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='pictures')
    image = models.ImageField(upload_to='plan_pictures/', blank=True, null=True) #画像ファイル専用のフィールド　ファイルの保存とDBにはファイルのパスを保存
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return str(self.image.name) if self.image else "画像"
    
#移動カテゴリテーブル　選択肢に情報を持たせる、アイコン、並び順、将来カテゴリ追加できるようにテーブル分けた
class TransportationMethod(models.Model):
    TRANSPORTATION_CHOICES=[
        ('walk', '徒歩'),
        ('train', '電車'),
        ('bus', 'バス'),
        ('shinkansen', '新幹線'),
        ('plane', '飛行機'),
        ('car', '車'),
        ('other', 'その他'),
    ]
    transportation = models.CharField(
        max_length=20,
        choices=TRANSPORTATION_CHOICES,
        unique=True #同じ移動手段を重複登録できない
    )
    transportation_icon_class = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'{self.get_transportation_display()}'