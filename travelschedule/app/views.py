from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import User

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout

#portfolio
def index_view(request):
    return render(request, 'app/index.html')



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
    
    
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'app/login.html')

def edit_profile_view(request):
    return render(request, 'app/edit_profile.html')

def logout_view(request):
    logout(request)
    return redirect('app:login')