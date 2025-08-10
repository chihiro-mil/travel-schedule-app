from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Prefetch
from django.views.decorators.http import require_POST
from django.utils.timezone import localtime
from django.forms import inlineformset_factory
from app.models import Plan



from .forms import (
    RegisterForm,
    LoginForm,
    ScheduleForm,
    PlanForm,
    LinkFormSet,
    PictureFormSet,
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
from datetime import datetime

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
            user.username = form.cleaned_data['username']
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('/app/login/')
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
        form = ChangeUsernameForm(instance=request.user)
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
        form = ScheduleForm()
    
    return render(request, 'app/home.html', {
        'form': form,
        'schedules': schedules,
        'sort_label': sort_label,
        'next_sort': next_sort,
    })
    
#予定表のタイトル編集ケバブ
def edit_schedule_title(request):
    if request.method == 'POST':
        schedule_id = request.POST.get('schedule_id')
        new_title = request.POST.get('title')
        schedule = get_object_or_404(Schedule, id=schedule_id)
        
        #未使用
        old_start = schedule.trip_start_date
        old_end = schedule.trip_end_date
        
        new_start_str = request.POST.get('start_date')
        new_end_str = request.POST.get('end_date')
        
        if new_start_str and new_end_str:
            new_start = datetime.strptime(new_start_str, '%Y-%m-%d').date()
            new_end = datetime.strptime(new_end_str, '%Y-%m-%d').date()
            
            delta = (new_start - old_start).days
            
            if delta != 0:
                plans = Plan.objects.filter(schedule=schedule)
                for plan in plans:
                    if plan.start_datetime:
                        plan.start_datetime += timedelta(days=delta)
                    if plan.end_datetime:
                        plan.end_datetime += timedelta(days=delta)
                    plan.save()
            
            Plan.objects.filter(
                schedule=schedule,
                start_datetime__date__lt=new_start
            ).delete()
            Plan.objects.filter(
                schedule=schedule,
                end_datetime__date__gt=new_end
            ).delete()
        
            schedule.title = new_title
            schedule.trip_start_date = new_start
            schedule.trip_end_date = new_end        
            schedule.save()
        
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


PictureFormSet = inlineformset_factory(
    Plan, Picture, form=PictureForm, formset=BasePictureFormSet,
    extra=10, can_delete=True
)
LinkFormSet = inlineformset_factory(
    Plan, Link, form=LinkForm, formset=BaseLinkFormSet,
    extra=5, can_delete=True
)

#予定追加・編集画面
@login_required
def plan_create_or_edit_view(request, schedule_id, plan_id=None):
    schedule = get_object_or_404(Schedule, id=schedule_id)
    plan = get_object_or_404(Plan, id=plan_id)if plan_id else None

    trip_choices = generate_trip_date_choices(schedule)
    
    if request.method == 'POST':
        print('post成功')
        print("post中身", request.POST)
        form = PlanForm(
            request.POST,
            request.FILES,
            instance=plan,
            trip_dates=trip_choices
        )
        
        link_formset = LinkFormSet(request.POST, request.FILES, instance=plan, prefix='links')
        picture_formset = PictureFormSet(request.POST, request.FILES, instance=plan, prefix='pictures')
        
        selected_category = request.POST.get('action_category') or ''
        print("selected_category from POST:", selected_category)
        
                
        print("form.is_valid():", form.is_valid())
        print("link_formset.is_valid():", link_formset.is_valid())
        print("picture_formset.is_valid():", picture_formset.is_valid())
        
        print("form.errors:", form.errors)
        print("link_formset.errors:", link_formset.errors)
        print("picture_formset.errors:", picture_formset.errors)
        
        if form.is_valid() and link_formset.is_valid() and picture_formset.is_valid():
            print("フォームから受けとったスタート日", form.cleaned_data.get("start_date"))
            print("フォームから受けとったスタート時間", form.cleaned_data.get("start_time"))
            print('フォームバリア:', form.is_valid())
            print('クリーン:', form.cleaned_data)
            print('このフォームは有効')
            print('cleaned_dataの中身:')
            for key, value in form.cleaned_data.items():
                print(f' {key} : {value}')
            print("form.instanceの中身：")
            print(f'action_category: {form.instance.action_category}')
            print('start_datetime:', form.cleaned_data.get('start_datetime'))
            print('end_datetime:', form.cleaned_data.get('end_datetime'))
            
            print(">>> form.instance.start_datetime(保存前のフォームインスタンス：)", form.instance.start_datetime)
            print(">>> form.instance.end_datetime(保存前のフォームインスタンス：)", form.instance.end_datetime)
            
            plan_instance = form.save(commit=False)
            
            print(">>> plan_instance.start_datetime(save(commit=False) 直後)", plan_instance.start_datetime)
            print(">>> plan_instance.end_datetime(保存前のフォームインスタンス：)", plan_instance.end_datetime)
            
            
            print("保存直前の plan_instans:")
            print("schedule_id:", plan_instance.schedule_id)
            print("start_datetime:", plan_instance.start_datetime)
            print("end_datetime:", plan_instance.end_datetime)
            print("action_category:", plan_instance.action_category)
            
            plan_instance.schedule = schedule
            
            print(">>>保存直前のスケジュールid:", plan_instance.schedule_id)
            print(">>>保存直前のスケジュールオブジェクト:", plan_instance.schedule)
            
            
            plan_instance.save()
            print("保存直後 一覧:", Plan.objects.all())
            print(">>>保存ごのスケジュールid:", plan_instance.schedule_id)
            
            latest_plan = Plan.objects.get(pk=plan_instance.pk)
            print("保存直後のDB上のstart_datetime", latest_plan.start_datetime)
            print("保存直後のDB上のend_datetime", latest_plan.end_datetime)
            
            for link in link_formset.save(commit=False):
                link.plan = plan_instance
                link.action_category = plan_instance.action_category
                link.save()
                
            for picture in picture_formset.save(commit=False):
                picture.plan = plan_instance
                picture.save()
                
            return redirect('app:schedule_detail', schedule_id=schedule.id)
            
        else:
            return render(request, 'app/plan_form.html', {
                'form': form, 
                'link_formset': link_formset,
                'picture_formset': picture_formset,
                'schedule': schedule,
                'form_title': '予定編集' if plan else '予定追加',
                'schedule_id': schedule_id,
                'transportation_methods': TransportationMethod.objects.all(),
                'selected_category': selected_category,
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
            form = PlanForm(instance=plan, trip_dates=trip_choices, initial=initial)

            
            link_formset = LinkFormSet(instance=plan, prefix='links')
            picture_formset = PictureFormSet(instance=plan, prefix='pictures')
        else:
            form = PlanForm(trip_dates=trip_choices)
            link_formset = LinkFormSet(queryset=Link.objects.none(), prefix='links')
            picture_formset = PictureFormSet(queryset=Picture.objects.none(), prefix='pictures')
        print("PlanForm errors:", form.errors)
        print("LinkFormSet errors:", link_formset.errors)
        print("PictureFormSet errors:" , picture_formset.errors)
        print("selected_category from PORT:", selected_category)
        
        return render(request, 'app/plan_form.html', {
            'form': form, 
            'link_formset': link_formset,
            'picture_formset': picture_formset,
            'schedule': schedule,
            'form_title': '予定編集' if plan else '予定追加',
            'schedule_id': schedule_id,
            'transportation_methods': TransportationMethod.objects.all(),
            'selected_category': selected_category,
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
    print(type(plans_by_date))
    
    for plan in plans:
        print(f"Plan ID: {plan.id}, start: {plan.start_datetime}, end: {plan.end_datetime}")
        if plan.start_datetime and plan.end_datetime:
            print(f"[VALID] Plan ID: {plan.id}, start:{plan.start_datetime}, end:{plan.end_datetime}")
            current_date = localtime(plan.start_datetime).date()
            end_date = localtime(plan.end_datetime).date()
            print("start_day", plan.start_datetime)
            print("current_date", current_date)
            print("end_date", end_date)
            
            while current_date <= end_date:
                print(f"name={plan.name or 'None'}, category={plan.action_category}, date={current_date}")
                plans_by_date[current_date].append(plan)
                current_date += timedelta(days=1)
        
        for date, day_plans in plans_by_date.items():
            sorted_day_plans = sorted(day_plans, key=lambda p: p.start_datetime)
            
            for plan in sorted_day_plans:
                print(f"{plan.name}: {plan.start_datetime}")
            
            active_ends = []
            for plan in sorted_day_plans:
                plan.nest_level = 0
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
        
    sorted_dates = date_list
    
    transportation_icon_map = {
        'walk': 'fa-person-walking',
        'train': 'fa-train',
        'subway': 'fa-subway',
        'bus': 'fa-bus',
        'plane': 'fa-plane',
        'car': 'fa-car',
        'compass': 'fa-compass',
    }
    
    context = {
        'schedule_id': schedule.id,
        'plans_by_date': plans_by_date,
        'sorted_dates': sorted_dates,
        'transportation_icon_map': transportation_icon_map,
        'schedule': schedule,
        'sorted_dates': sorted(plans_by_date.keys()),
    }
    return render(request, 'app/schedule_detail.html', context)

#予定削除モーダル
@login_required
def plan_delete_view(request, plan_id):
    if request.method == 'POST':
        plan = get_object_or_404(Plan, id=plan_id)
        schedule_id = plan.schedule.id
        plan.delete()
        return redirect('app:schedule_detail', schedule_id =  schedule_id)