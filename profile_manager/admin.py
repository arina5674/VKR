from django.contrib import admin
from django.contrib.auth.models import User

from profile_manager.models import UserInformation, Town


# Register your models here.


@admin.register(UserInformation)
class UserInformationAdmin(admin.ModelAdmin):
    pass

@admin.register(Town)
class TownAdmin(admin.ModelAdmin):
    pass
