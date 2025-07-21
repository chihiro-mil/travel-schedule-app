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

def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    #plans = Plan.objects.filter(schedule_id=schedule.id)
    return render(request, 'app/schedule_detail.html', {
        'schedule': schedule,
        #'plans': plans,
    })
    
    
#予定追加・編集画面
def plan_create_or_edit_view(request, schedule_id, plan_id=None):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    plan = get_object_or_404(Plan, id=plan_id)if plan_id else None

    trip_choices = generate_trip_date_choices(schedule)
        
    if request.method == 'POST':
        form = PlanForm(request.POST, request.FILES, instance=plan, trip_date_choices=trip_choices)
        link_formset = LinkFormSet(request.POST, prefix='links')
        picture_formset = PictureFormSet(request.POST, request.FILES, prefix='pictures')
        
        if form.is_valid() and link_formset.is_valid() and picture_formset.is_valid():
            plan_instance = form.save(commit=False)
            plan_instance.schedule = schedule
            plan_instance.start_datetime = form.cleaned_data['start_datetime']
            plan_instance.end_datetime = form.cleaned_data['end_datetime']
            plan_instance.save()
            
            for link in link_formset.save(commit=False):
                link.plan = plan_instance
                link.save()
                
            for picture in picture_formset.save(commit=False):
                picture.plan = plan_instance
                picture.save()
                
            return redirect('app:schedule_detail', schedule_id=schedule.id)
    else:
        form = PlanForm(instance=plan, trip_date_choices=trip_choices)
        link_formset = LinkFormSet(queryset=Link.objects.none(), prefix='links')
        picture_formset = PictureFormSet(queryset=Picture.objects.none(), prefix='pictures')
        
    return render(request, 'app/plan_form.html', {
        'form': form, 
        'link_formset': link_formset,
        'picture_formset': picture_formset,
        'schedule': schedule,
        'form_title': '予定編集' if plan else '予定追加',
        'schedule_id': schedule_id,
    })

def generate_trip_date_choices(schedule):
    trip_dates = []
    current_date = schedule.trip_start_date
    while current_date <= schedule.trip_end_date:
        label = current_date.strftime('%Y/%m/%d(%a)')
        trip_dates.append((current_date, label))
        current_date += timedelta(days=1)
    return trip_dates

#追加・編集共通
@login_required
def plan_form_view(request, schedule_id, plan_id=None):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    plan = get_object_or_404(Plan, id=plan_id) if plan_id else None
    
    trip_date_choices = generate_trip_date_choices(schedule)
    
    if request.method == 'POST':
        form = PlanForm(request.POST, request.FILES, trip_date_choices=trip_date_choices, instance=plan)
        if form.is_valid():
            new_plan = form.save(commit=False)
            new_plan.schedule = schedule
            new_plan.start_datetime = form.cleaned_data.get('start_datetime')
            new_plan.end_datetime = form.cleaned_data.get('end_datetime')
            new_plan.save()
            return redirect('app:schedule_detail', schedule_id=schedule.id)
    else:
        form = PlanForm(instance=plan, trip_date_choices=trip_date_choices)
        
    return render(request, 'app/plan_form.html', {
        'form': form,
        'schedule': schedule,
        'plan': plan,
        'form_title': '予定編集' if plan else '予定追加',
    })

#予定表画面
@login_required
def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    plans = Plan.objects.filter(schedule=schedule).order_by('start_datetime')
    
    plans_by_date = defaultdict(list)
    for plan in plans:
        if plan.start_datetime:
            day = plan.start_datetime.date()
            plans_by_date[day].append(plan)
        
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
    transportation_map ={
        tm.plan_id: tm.transportation for tm in TransportationMethod.objects.filter(plan__in=plans)
    }
    
    icon_class_map = {
        plan_id: transportation_icon_map.get(transportation, 'fa-question')
        for plan_id, transportation in transportation_map.items()
    }
    
    context = {
        'schedule_id': schedule.id,
        'plans_by_date': plans_by_date,
        'sorted_dates': sorted_dates,
        'transportation_map': transportation_map,
        'transportation_icon_map': transportation_icon_map,
    }
    return render(request, 'app/schedule_detail.html', {
        'schedule': schedule,
        'plans_by_date': plans_by_date,
    })