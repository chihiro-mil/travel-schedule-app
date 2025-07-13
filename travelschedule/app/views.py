from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegisterForm
from .models import User
from django.contrib.auth import authenticate, login
from .forms import LoginForm

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.contrib.auth import logout
from django.shortcuts import redirect

from .models import Schedule#, Plan
from .forms import ScheduleForm



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
    

#plan/add(仮)ページ
def plan_add(request):
    if request.method == "POST":
        print(request.POST.get('title'))
        print(request.POST.get('trip_start_date'))
        print(request.POST.get('trip_end_date'))
        return redirect('app:home')
    return redirect('app:home')