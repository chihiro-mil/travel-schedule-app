from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import User

from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        print("フォーム送信あり")
        if form.is_valid():
            print("バリエーション成功")
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('/accounts/login/') #()の中は仮
        else:
            print("バリエーションNG!")
            print(form.errors)
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html')

def edit_profile_view(request):
    return render(request, 'accounts/edit_profile.html')