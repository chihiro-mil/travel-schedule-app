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
]