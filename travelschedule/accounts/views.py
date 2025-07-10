from django.shortcuts import render, redirect
from .forms import RegisterForm
from django.contrib.auth.models import User


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
    return render(request, 'accounts/login.html')

def edit_profile_view(request):
    return render(request, 'accounts/edit_profile.html')