from django.contrib import admin
from .models import User
from .models import TransportationMethod
from .models import PackingItem

admin.site.register(User)
admin.site.register(TransportationMethod)
admin.site.register(PackingItem)
