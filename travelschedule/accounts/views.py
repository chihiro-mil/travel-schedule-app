from django.shortcuts import render


def register_view(request):
    return render(request, 'accounts/register.html')

def login_view(request):
    return render(request, 'accounts/login.html')

def edit_profile_view(request):
    return render(request, 'accounts/edit_profile.html')