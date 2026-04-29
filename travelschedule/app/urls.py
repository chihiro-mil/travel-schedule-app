# DjangoのURLルーティングで使うpath関数（urlとviewを結びつける関数）を読み込む
from django.urls import path
# . は同じ階層を意味する
# このアプリのviews.pyを読み込む
from . import views

# URLの名前空間(他のアプリと区別するため)
app_name = "app"

# urlとviewを対応させる設定
urlpatterns = [
    path('', views.index_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('schedule/<int:schedule_id>/', views.schedule_detail_view, name='schedule_detail'),
    path('schedule/<int:schedule_id>/plan/add/', views.plan_create_or_edit_view, name='plan_create_or_edit'),
    path('schedule/<int:schedule_id>/plan/<int:plan_id>/edit/', views.plan_create_or_edit_view, name='plan_edit'),
    path('mypage/', views.mypage_view, name='mypage'),
    path('mypage/username/', views.change_username_view, name='change_username'),
    path('mypage/email/', views.change_email_view, name='change_email'),
    path('mypage/password/', views.change_password_view, name='change_password'),
    path('edit_schedule_title/', views.edit_schedule_title, name='edit_schedule_title'),
    path('delete_schedule/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),
    path('plan/<int:plan_id>/delete/', views.plan_delete_view, name='plan_delete_view'),
    # path('schedule/<int:schedule_id>/packing_item_list/', views.packing_item_list_view, name='packing_item_list'),
    # path('schedule/<int:schedule_id>/packing_item/add/', views.packing_item_create_or_edit_view, name='packing_item_add'),
    # path('schedule/<int:schedule_id>/packing_item/<int:item_id>/edit/', views.packing_item_create_or_edit_view, name='packing_item_edit'),
]

# path('URL', 実行するview関数, name='URLの名前'(テンプレで使用))