from django.urls import path
from . import views


app_name = "app"

urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('edit/', views.edit_profile_view, name='edit_profile'),
    path('home/', views.home_view, name='home'),
    path('schedule/<int:schedule_id>/', views.schedule_detail_view, name='schedule_detail'),
    path('schedule/<int:schedule_id>/plan/add/', views.plan_create_or_edit_view, name='plan_create_or_edit'),
    path('schedule/<int:schedule_id>/plan/<int:plan_id>/edit/', views.plan_create_or_edit_view, name='plan_edit'),
    path('mypage/', views.mypage_view, name='mypage'),
    path('mypage/username/', views.change_username_view, name='change_username'),
    path('mypage/email/', views.change_email_view, name='change_email'),
    path('mypage/password/', views.change_password_view, name='change_password'),
]