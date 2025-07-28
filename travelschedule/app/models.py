from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.db import models

#ユーザーテーブル
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError('メールアドレスは必須です')
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, name, password, **extra_fields)


class User(AbstractUser, PermissionsMixin):
    name = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']
    
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        
        
#予定表テーブル
class Schedule(models.Model):
    user = models.ForeignKey('app.User', on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    trip_start_date = models.DateField()
    trip_end_date = models.DateField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
#予定テーブル
class Plan(models.Model):
    CATEGORY_CHOICES = [
        ('move', '移動'),
        ('sightseeing', '観光'),
        ('meal', '食事'),
        ('stay', '宿泊'),
    ]
    schedule = models.ForeignKey('Schedule', on_delete=models.CASCADE, related_name='plans')
    action_category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        blank=True
    )
    transportation = models.ForeignKey(
        'TransportationMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plans'
    )
    name = models.CharField(max_length=24)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    memo = models.TextField(blank=True, null=True)
    departure_location = models.CharField(max_length=24, blank=True, null=True)
    arrival_location = models.CharField(max_length=24, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_action_category_display()})"
    
#リンクテーブル
class Link(models.Model):
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='links')
    url = models.URLField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.url
    
#写真テーブル
class Picture(models.Model):
    plan = models.ForeignKey('Plan', on_delete=models.CASCADE, related_name='pictures')
    image = models.ImageField(upload_to='plan_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.caption or "画像"
    
#移動カテゴリテーブル
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
        unique=True
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