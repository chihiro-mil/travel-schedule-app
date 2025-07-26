from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required


from .forms import (
    RegisterForm,
    LoginForm,
    ScheduleForm,
    PlanForm,
    LinkFormSet,
    PictureFormSet,
)

from .models import User, Schedule, Plan, Link, Picture, TransportationMethod

from datetime import timedelta

from collections import defaultdict


#portfolio
def index_view(request):
    return render(request, 'app/index.html')


#アカウント登録
def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('/app/login/') #()の中は仮
    else:
        form = RegisterForm()
    return render(request, 'app/register.html', {'form': form})
    
#ログイン
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('app:home')
            else:
                form.add_error(None, 'メールアドレスまたはパスワードが間違っています')
    else:
        form = LoginForm()
    return render(request, 'app/login.html', {'form': form})


def edit_profile_view(request):
    return render(request, 'app/edit_profile.html')

#ログアウト
def logout_view(request):
    logout(request)
    return redirect('app:login')

#ホーム画面（予定表一覧画面）
@login_required
def home_view(request):
    if request.method =="POST":
        form = ScheduleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('app:home')
    else:
        form = ScheduleForm()
    
    schedules = Schedule.objects.all().order_by('-created_at')
    return render(request, 'app/home.html', {
        'form': form,
        'schedules': schedules
    })
    
    
#予定追加・編集画面
@login_required
def plan_create_or_edit_view(request, schedule_id, plan_id=None):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    plan = get_object_or_404(Plan, id=plan_id)if plan_id else None

    trip_choices = generate_trip_date_choices(schedule)
    
    if request.method == 'POST':
        form = PlanForm(
            request.POST,
            request.FILES,
            instance=plan,
            trip_dates=trip_choices
        )
        link_formset = LinkFormSet(request.POST, request.FILES, prefix='links')
        picture_formset = PictureFormSet(request.POST, request.FILES, prefix='pictures')
        
        if form.is_valid() and link_formset.is_valid() and picture_formset.is_valid():
            print("cleaned_data の中身：")
            print('cleaned_dataの中身:')
            for key, value in form.cleaned_data.items():
                print(f' {key} : {value}')
            print("form.instanceの中身：")
            print(f'action_category: {form.instance.action_category}')
            print('start_datetime:', form.cleaned_data.get('start_datetime'))
            print('end_datetime:', form.cleaned_data.get('end_datetime'))
            plan_instance = form.save(commit=False)
            plan_instance.schedule = schedule
            plan_instance.start_datetime = form.cleaned_data.get('start_datetime')
            plan_instance.end_datetime = form.cleaned_data.get('end_datetime')
            
            print("保存直前の plan_instans:")
            print("schedule_id:", plan_instance.schedule_id)
            print("start_datetime:", plan_instance.start_datetime)
            print("end_datetime:", plan_instance.end_datetime)
            
            plan_instance.save()
            print("保存直後 一覧:", Plan.objects.all())
            
            for link in link_formset.save(commit=False):
                link.plan = plan_instance
                link.action_category = plan_instance.action_category
                link.save()
                
            for picture in picture_formset.save(commit=False):
                picture.plan = plan_instance
                picture.save()
                
            return redirect('app:schedule_detail', schedule_id=schedule.id)
            
    else:
        form = PlanForm(instance=plan, trip_dates=trip_choices)
        link_formset = LinkFormSet(queryset=Link.objects.none(), prefix='links')
        picture_formset = PictureFormSet(queryset=Picture.objects.none(), prefix='pictures')
        print("PlanForm errors:", form.errors)
        print("LinkFormSet errors:", link_formset.errors)
        print("PictureFormSet errors:" , picture_formset.errors)
    
    return render(request, 'app/plan_form.html', {
        'form': form, 
        'link_formset': link_formset,
        'picture_formset': picture_formset,
        'schedule': schedule,
        'form_title': '予定編集' if plan else '予定追加',
        'schedule_id': schedule_id,
        'transportation_methods': TransportationMethod.objects.all(),
    })
    
def generate_trip_date_choices(schedule):
    start = schedule.trip_start_date
    end = schedule.trip_end_date
    delta = (end - start).days
    
    return [start + timedelta(days=i) for i in range(delta + 1)]

#予定表画面
@login_required
def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    plans = Plan.objects.filter(schedule_id=schedule_id,).order_by('start_datetime')
    print("取得されたplan一覧：", plans)
    for plan in plans:
        print("plan.schedule_id:", plan.schedule_id, "start:", plan.start_datetime)
    
    plans_by_date = {}
    for plan in plans:
        if plan.start_datetime:
            date = plan.start_datetime.date()
            if date not in plans_by_date:
                plans_by_date[date] = []
            plans_by_date[date].append(plan)
            
    print("plans_by_date:", plans_by_date)
            
    
        
    sorted_dates = sorted(plans_by_date.keys())
    
    transportation_icon_map = {
        'walk': 'fa-person-walking',
        'train': 'fa-train',
        'subway': 'fa-subway',
        'bus': 'fa-bus',
        'plane': 'fa-plane',
        'car': 'fa-car',
        'compass': 'fa-compass',
    }
    for plan in plans:
        print("plan:", plan)
        print("start_datetime:", plan.start_datetime)
        print("カテゴリ:", plan.action_category)
        if plan.transportation:
            icon_class = transportation_icon_map.get(plan.transportation.transportation, 'fa-question')
        else:
            icon_class = 'fa-question'
    
    context = {
        'schedule_id': schedule.id,
        'plans_by_date': plans_by_date,
        'sorted_dates': sorted_dates,
        'transportation_icon_map': transportation_icon_map,
        'schedule': schedule,
    }
    return render(request, 'app/schedule_detail.html', context)