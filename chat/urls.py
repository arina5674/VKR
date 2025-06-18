from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
path('start-chat/<int:teacher_id>/', views.start_chat, name='start_chat'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)