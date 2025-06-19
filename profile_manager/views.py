from django import urls
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter

from profile_manager.forms import LoginForm, RegisterForm, ProfileEditForm, InterestingFactFormSet, EducationFormSet
from profile_manager.models import UserInformation, Town, InterestingFact, Education
from profile_manager.serializers import UserInformationSerializer


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['email'], password=cd['password'])
            if user:
                if user.is_active:
                    login(request, user)
                    return redirect(urls.reverse(list_of_profiles))
                else:
                    return HttpResponse('Disabled account')
            else:
                return HttpResponse('Invalid login')
    else:
        form = LoginForm()
    return render(request, 'profile_manager/login.html', {'form': form})


def user_register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            cd['username'] = cd['email']
            del cd['password_again']
            user = User.objects.create_user(**cd)
            login(request, user)
            UserInformation.objects.create(user_id=user.id)
            return redirect(urls.reverse(get_concrete_profile, args=[user.id]))
    else:
        form = RegisterForm()
    return render(request, 'profile_manager/register.html', {'form': form})


def get_concrete_profile(request, user_id: int):
    profile_user = get_object_or_404(User, id=user_id)
    user_info = get_object_or_404(UserInformation, user=profile_user)
    interesting_facts = InterestingFact.objects.filter(user=user_info)
    educations = Education.objects.filter(user=user_info)

    is_owner = request.user.id == user_id

    context = {
        'profile_user': profile_user,
        'user_info': user_info,
        'interesting_facts': interesting_facts,
        'educations': educations,
        'is_owner': is_owner,
    }

    return render(request, 'profile_manager/profile.html', context)


def list_of_profiles(request):
    # Получаем параметры фильтрации из GET-запроса
    search_query = request.GET.get('search', '')
    city_id = request.GET.get('city', '')

    # Начинаем с базового QuerySet
    profiles = UserInformation.objects.select_related('user', 'town').all()

    # Применяем фильтры
    if search_query:
        profiles = profiles.filter(
            models.Q(user__first_name__icontains=search_query) |
            models.Q(user__last_name__icontains=search_query)
        )

    if city_id:
        profiles = profiles.filter(town_id=city_id)

    # Получаем список всех городов для фильтра
    cities = Town.objects.all()

    context = {
        'profiles': profiles,
        'cities': cities,
        'search_query': search_query,
    }

    return render(request, 'profile_manager/list_of_profiles.html', context)


@login_required
def edit_profile(request):
    user_info = get_object_or_404(UserInformation, user=request.user)
    facts = InterestingFact.objects.filter(user=user_info)
    educations = Education.objects.filter(user=user_info)

    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user_info)

        if form.is_valid():
            form.save()

            # Обработка фактов
            fact_ids = [int(id) for id in request.POST.getlist('fact_id') if id]
            fact_texts = request.POST.getlist('fact_text')

            # Удаляем факты, которых нет в отправленных данных
            facts.exclude(id__in=fact_ids).delete()

            # Обновляем или создаем факты
            for fact_id, text in zip(fact_ids, fact_texts):
                if text.strip():  # Не сохраняем пустые факты
                    if fact_id > 0:
                        fact = InterestingFact.objects.get(id=fact_id)
                        fact.text = text
                        fact.save()
                    else:
                        InterestingFact.objects.create(user=user_info, text=text)

            # Обработка образования
            edu_ids = [int(id) for id in request.POST.getlist('edu_id') if id]
            edu_universities = request.POST.getlist('edu_university')

            # Собираем подтверждения в словарь
            confirmed_map = {}
            for key in request.POST:
                if key.startswith('edu_confirmed_'):
                    confirmed_map[key.split('_')[-1]] = True

            # Удаляем отсутствующие записи
            educations.exclude(id__in=edu_ids).delete()

            # Обновляем/создаём записи
            for edu_id, university in zip(edu_ids, edu_universities):
                if university.strip():
                    # Определяем ключ подтверждения
                    confirm_key = str(edu_id) if edu_id > 0 else university + str(edu_id)
                    is_confirmed = confirm_key in confirmed_map

                    if edu_id > 0:
                        edu = Education.objects.get(id=edu_id)
                        edu.university = university
                        edu.is_confirmed = is_confirmed
                        edu.save()
                    else:
                        Education.objects.create(
                            user=user_info,
                            university=university,
                            is_confirmed=is_confirmed
                        )

            return redirect('get_concrete_profile', user_id=request.user.id)
    else:
        form = ProfileEditForm(instance=user_info)

    context = {
        'form': form,
        'facts': facts,
        'educations': educations,
    }
    return render(request, 'profile_manager/edit_profile.html', context)