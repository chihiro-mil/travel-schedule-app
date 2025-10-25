from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.db.models import  Q
from django.db.models.functions import Coalesce
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime
from django.utils.dateparse import parse_date
from django.forms import inlineformset_factory
from app.models import Plan
from django.utils import timezone
from copy import deepcopy
from django.urls import reverse


from .forms import (
    RegisterForm,
    LoginForm,
    ScheduleForm,
    PlanForm,
    ChangeUsernameForm, 
    ChangeEmailForm,
    CustomPasswordChangeForm,
    BasePictureFormSet,
    BaseLinkFormSet,
    PictureForm,
    LinkForm,
)

from .models import User, Schedule, Plan, Link, Picture, TransportationMethod

from datetime import timedelta
from datetime import datetime, time

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
            login(request, user)
            return redirect('app:home')
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


#マイページ設定画面
@login_required
def mypage_view(request):
    request.user.refresh_from_db()
    
    referer = request.META.get('HTTP_REFERER')
    return render(request, 'app/mypage.html', {
        'user': request.user,
        'back_url': referer
    })

#ユーザー名変更画面
@login_required
def change_username_view(request):
    if request.method == 'POST':
        form = ChangeUsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            request.user.refresh_from_db()
            messages.success(request, 'ユーザー名を変更しました')
            return redirect('app:mypage')
    else:
        form = ChangeUsernameForm()
    return render(request, 'app/change_username.html', {'form': form})

#メールアドレス変更画面
@login_required
def change_email_view(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            request.user.refresh_from_db()
            messages.success(request, 'メールアドレスを変更しました')
            return redirect('app:mypage')
    else:
        form = ChangeEmailForm(instance=request.user)
        form.initial["email"] = ""
    return render(request, 'app/change_email.html', {'form': form})
    
#パスワード変更画面
@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            request.user.refresh_from_db()
            update_session_auth_hash(request, user)
            messages.success(request, 'パスワードを変更しました')
            return redirect('app:mypage')
    else:
        form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'app/change_password.html', {'form': form})

#ログアウト
def logout_view(request):
    logout(request)
    return redirect('app:login')

#ホーム画面（予定表一覧画面）
@login_required
def home_view(request):
    sort = request.GET.get('sort', 'date')
    
    if sort == 'updated':
        schedules = Schedule.objects.filter(user=request.user).order_by('-updated_at')
        sort_label ='予定日降順'
        next_sort = 'date'
    else:
        schedules = Schedule.objects.filter(user=request.user).order_by('-trip_start_date')
        sort_label = '更新順'
        next_sort = 'updated'
        
    if request.method == 'POST':
        form = ScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.user = request.user
            schedule.save()
            return redirect('app:plan_create_or_edit', schedule_id=schedule.id)
        else:
            no_schedules = not schedules.exists()
            return render(request, 'app/home.html', {
                'form': form,
                'schedules': schedules,
                'sort_label': sort_label,
                'next_sort': next_sort,
                'show_add_modal': True,
                'no_schedules': no_schedules,
            })
    else:
        form = ScheduleForm()
        no_schedules = not schedules.exists()
        return render(request, 'app/home.html', {
            'form': form,
            'schedules': schedules,
            'sort_label': sort_label,
            'next_sort': next_sort,
            'show_add_modal': False,
            'no_schedules': no_schedules,
        })
    
#予定表のタイトル編集ケバブ
def edit_schedule_title(request):
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        new_title = request.POST.get('title')
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        old_start = schedule.trip_start_date
        old_end = schedule.trip_end_date
        
        new_start_str = request.POST.get('start_date')
        new_end_str = request.POST.get('end_date')
        
        if new_start_str and new_end_str:
            new_start = datetime.strptime(new_start_str, '%Y-%m-%d').date()
            new_end = datetime.strptime(new_end_str, '%Y-%m-%d').date()
            
            schedule.title = new_title
            schedule.trip_start_date = new_start
            schedule.trip_end_date = new_end
            schedule.save()
            
            shortened = (new_start > old_start) or (new_end < old_end)
            if shortened:
                start_naive =  datetime.combine(new_start, time.min)
                end_naive = datetime.combine(new_end, time.max)
                if timezone.is_naive(start_naive):
                    new_start_dt = timezone.make_aware(start_naive)
                    new_end_dt = timezone.make_aware(end_naive)
                    new_start_dt = timezone.make_aware(start_naive) if timezone.is_naive(start_naive) else start_naive
                    new_end_dt = timezone.make_aware(end_naive) if timezone.is_naive(end_naive) else end_naive
                
                    plans_to_delete = Plan.objects.filter(schedule=schedule).filter(
                        Q(start_datetime__lt=new_start_dt) | 
                        Q(end_datetime__gt=new_end_dt) | 
                        (Q(end_datetime__isnull=True) & Q(start_datetime__gt=new_end_dt))
                    )
                    plans_to_delete.delete()
        
    return redirect('app:home')

#予定表の削除モーダル
@login_required
def delete_schedule(request, schedule_id):
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
        schedule.delete()
        return redirect('app:home')
    return redirect('app:home')

#予定追加・編集画面
@login_required
def plan_create_or_edit_view(request, schedule_id, plan_id=None):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    plan = get_object_or_404(Plan, id=plan_id)if plan_id else None
    
    selected_day = None

    trip_choices = generate_trip_date_choices(schedule)
    
    extra_links = 1
    LinkFormSet = inlineformset_factory(
        Plan,
        Link,
        form=LinkForm,
        formset=BaseLinkFormSet,
        extra=extra_links,
        max_num=5,
        validate_max=True,
        can_delete=True
    )

    extra_pictures = 1
    PictureFormSet = inlineformset_factory(
        Plan,
        Picture,
        form=PictureForm,
        formset=BasePictureFormSet,
        extra=extra_pictures,
        max_num=6,
        validate_max=True,
        can_delete=True,
    )
    
    if request.method == 'POST':
        form = PlanForm(
            request.POST,
            request.FILES,
            instance=plan,
            trip_dates=trip_choices
        )
        
        link_formset = LinkFormSet(request.POST or None, request.FILES or None, instance=plan, prefix='links')
        picture_formset = PictureFormSet(request.POST or None, request.FILES or None, instance=plan, prefix='pictures')
        
        for f in picture_formset:
            delete_flag = f.cleaned_data.get('DELETE', False) if f.is_valid() else False
            if delete_flag:
                f.empty_permitted = True
            
        selected_category = request.POST.get('action_category') or ''
        
        if form.is_valid() and link_formset.is_valid() and picture_formset.is_valid():
            
            plan_instance = form.save(commit=False)
            plan_instance.schedule = schedule
            plan_instance.save()
            
            for picture_form in picture_formset:
                instance = picture_form.instance
                delete_flag = picture_form.cleaned_data.get('DELETE', False)
                image = picture_form.cleaned_data.get('image')
                
                
                if not delete_flag and not image and not instance.pk:
                    continue
                
                if delete_flag and instance.pk:
                    instance.delete()
                    continue
                
                if not delete_flag:
                    picture = picture_form.save(commit=False)
                    picture.plan = plan_instance
                    picture.save()
        
            if plan_instance.start_datetime:
                trip_start = schedule.trip_start_date
                saved_date = localtime(plan_instance.start_datetime).date()
                selected_day = (saved_date - trip_start).days + 1
            else:
                selected_day = 1
                    
                    
            link_instances = link_formset.save(commit=False)
            
            for obj in link_formset.deleted_objects:
                obj.delete()
                
            for form in link_formset:
                if form.instance.pk:
                    url_value = form.cleaned_data.get('url') if form.is_valid() else form.data.get(form.add_prefix('url'))
                    if not url_value:
                        form.instance.delete()
                
            for link in link_instances:
                if link.url and link.url.strip():
                    link.plan = plan_instance
                    link.action_category = plan_instance.action_category
                    link.save()
                
                schedule.updated_at = timezone.now()
                schedule.save(update_fields=['updated_at'])
                
            return redirect(reverse('app:schedule_detail', args=[schedule_id]) + f'?selected_day={selected_day}')
            
        else:
            tm = []
            for m in TransportationMethod.objects.all():
                tm.append({
                    'id': m.id,
                    'label': m.transportation,
                    'icon': m.transportation_icon_class,
                })
                
            return render(request, 'app/plan_form.html', {
                'form': form, 
                'link_formset': link_formset,
                'picture_formset': picture_formset,
                'schedule': schedule,
                'form_title': '予定編集' if plan else '予定追加',
                'schedule_id': schedule_id,
                'transportation_methods': tm,
                'selected_category': selected_category,
                'plan': plan,
            })
    else:
        selected_category = plan.action_category if plan else ''
        if plan:
            initial = {}
            if plan.start_datetime:
                local_start = localtime(plan.start_datetime)
                initial['start_date'] = local_start.date()
                initial['start_time'] = local_start.time()
            if plan.end_datetime:
                local_end = localtime(plan.end_datetime)
                initial['end_date'] = local_end.date()
                initial['end_time'] = local_end.time()
                
            print("編集画面", plan.transportation_id)
            form = PlanForm(instance=plan, trip_dates=trip_choices, initial=initial)
            
            link_formset = LinkFormSet(
                request.POST or None,
                request.FILES or None,
                instance=plan,
                prefix='links',
            )
            
            picture_formset = PictureFormSet(instance=plan, prefix='pictures')
        else:
            date_str = request.GET.get('date') or request.GET.get('start')
            end_str = request.GET.get('end')
            
            start_date = parse_date(date_str) if date_str else None
            end_date = parse_date(end_str) if end_str else start_date
            
            initial = {}
            if start_date:
                initial['start_date'] = start_date
            if end_date:
                initial['end_date'] = end_date
                
                
            form = PlanForm(trip_dates=trip_choices, initial=initial)
            link_formset = LinkFormSet(request.POST or None, request.FILES or None, instance=plan, prefix='links')
            picture_formset = PictureFormSet(instance=plan, prefix='pictures')
            
        tm = []
        for m in TransportationMethod.objects.all():
            tm.append({
                'id': m.id,
                'label': m.transportation,
                'icon': m.transportation_icon_class,
            })
        
        return render(request, 'app/plan_form.html', {
            'form': form, 
            'link_formset': link_formset,
            'picture_formset': picture_formset,
            'schedule': schedule,
            'form_title': '予定編集' if plan else '予定追加',
            'schedule_id': schedule_id,
            'transportation_methods': tm,
            'selected_category': selected_category,
            'plan': plan,
        })
    
def generate_trip_date_choices(schedule):
    start = schedule.trip_start_date
    end = schedule.trip_end_date
    delta = (end - start).days
    
    return [start + timedelta(days=i) for i in range(delta + 1)]

#予定詳細画面
@login_required
def schedule_detail_view(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    plans = Plan.objects.filter(schedule_id=schedule_id,).prefetch_related(
        Prefetch('links'),
        Prefetch('pictures'),
    ).order_by('start_datetime')

    
    plans_by_date = defaultdict(list)
    
    for plan in plans:
        if not plan.start_datetime or not plan.end_datetime:
            continue
        start_date = localtime(plan.start_datetime).date()
        end_date = localtime(plan.end_datetime).date()
        
        if plan.action_category == 'stay':
            ci = deepcopy(plan)
            ci.display_type = 'checkin'
            ci.display_datetime = plan.start_datetime
            ci.is_stay_display = True
            plans_by_date[start_date].append(ci)
            
            co = deepcopy(plan)
            co.display_type = 'checkout'
            co.display_datetime = plan.end_datetime
            co.is_stay_display = True
            plans_by_date[end_date].append(co)
            
        else:
            current_date = start_date
            while current_date <= end_date:
                plans_by_date[current_date].append(plan)
                current_date += timedelta(days=1)
        
        for date, day_plans in plans_by_date.items():
            sorted_day_plans = sorted(day_plans, key=lambda plan: getattr(plan, 'display_datetime', plan.start_datetime))

            active_ends = []
            for plan in sorted_day_plans:
                plan.nest_level = 0
                
                if getattr(plan, 'is_stay_display', False):
                    continue
                
                for end in active_ends:
                    if plan.start_datetime < end:
                        plan.nest_level += 1
                active_ends.append(plan.end_datetime)
                
            plans_by_date[date] = sorted_day_plans


    date_list = []
    current_date = schedule.trip_start_date
    while current_date <= schedule.trip_end_date:
        date_list.append(current_date)
        current_date += timedelta(days=1)
    
    for d in date_list:
        if d not in plans_by_date:
            plans_by_date[d] = []
        
    sorted_dates = date_list
    
    tm = []
    for m in TransportationMethod.objects.all():
        tm.append({
            'id': m.id,
            'label': m.transportation,
            'icon': m.transportation_icon_class,
        })

    context = {
        'schedule_id': schedule.id,
        'plans_by_date': plans_by_date,
        'sorted_dates': sorted_dates,
        'schedule': schedule,
        'transportation_methods': tm,
        'sorted_dates': sorted(plans_by_date.keys()),
    }
    return render(request, 'app/schedule_detail.html', context)

#予定削除モーダル
@login_required
def plan_delete_view(request, plan_id):
    if request.method == 'POST':
        plan = get_object_or_404(Plan, id=plan_id)
        schedule = plan.schedule
        
        if plan.start_datetime:
            trip_start = schedule.trip_start_date
            deleted_date = localtime(plan.start_datetime).date()
            selected_day = (deleted_date - trip_start).days + 1
        else:
            selected_day = 1
            
        plan.delete()
        schedule.updated_at = timezone.now()
        schedule.save(update_fields=['updated_at'])
        
        return redirect(f"{reverse('app:schedule_detail', args=[schedule.id])}?selected_day={selected_day}")