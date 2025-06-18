from django.contrib import admin

from chat.models import ChatSession


# Register your models here.
@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    pass