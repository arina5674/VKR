import uuid

from django import urls
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect

from chat.models import ChatSession


# Create your views here.


@login_required
def start_chat(request, teacher_id):
    teacher = get_object_or_404(User, id=teacher_id)

    # Проверяем, существует ли уже чат между пользователями
    chat_session = ChatSession.objects.filter(
        models.Q(first_user=request.user, second_user=teacher) |
        models.Q(first_user=teacher, second_user=request.user)
    ).first()

    # Если чата нет - создаем новый
    if not chat_session:
        chat_session = ChatSession.objects.create(
            first_user=request.user,
            second_user=teacher,
            uuid=uuid.uuid4(),
        )

    return redirect('room', room_name=chat_session.uuid)


def room(request, room_name):
    chat_session = get_object_or_404(ChatSession, uuid=room_name)

    # Определяем, кто является собеседником
    if request.user == chat_session.first_user:
        companion = chat_session.second_user
    else:
        companion = chat_session.first_user

    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'companion_name': companion.username if companion else "Unknown",
        'companion_fullname': f"{companion.first_name} {companion.last_name}".strip() if companion else "Unknown User",
    })


@login_required
def chat_list(request):
    # Получаем все чаты, где пользователь является участником
    chat_sessions = ChatSession.objects.filter(
        models.Q(first_user=request.user) | models.Q(second_user=request.user)
    ).order_by('-dt_last_message')

    return render(request, 'chat/chat_list.html', {
        'chat_sessions': chat_sessions,
    })
