import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter

from education.forms import LessonPartForm, LessonForm
from education.models import Lesson, LessonPart, Answer, TestPart
from education.serializers import LessonSerializer


# Create your views here.


def courses_list(request, teacher_id=None):
    print(teacher_id)
    if teacher_id:
        teacher = get_object_or_404(User, id=teacher_id)
        lessons = Lesson.objects.filter(creator=teacher).order_by('-dt_created')
    else:
        teacher = None
        lessons = Lesson.objects.all().order_by('-dt_created')

    # Фильтрация по сложности
    difficulty = request.GET.get('difficulty')
    if difficulty:
        lessons = lessons.filter(difficulty=difficulty)

    # Поиск по названию
    search_query = request.GET.get('search')
    if search_query:
        lessons = lessons.filter(name__icontains=search_query)

    return render(request, 'education/list_of_courses.html', {'lessons': lessons})


def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    parts = lesson.parts.all().order_by('number')  # Сортируем здесь

    # Считаем статистику
    lecture_count = parts.filter(type='LECTURE').count()
    test_count = parts.filter(type='TEST').count()
    total_time = lecture_count * 5 + test_count * 3  # 5 мин лекция, 3 мин тест, 10 мин практика

    return render(request, 'education/lesson_detail.html', {
        'lesson': lesson,
        'parts': parts,
        'lecture_count': lecture_count,
        'test_count': test_count,
        'total_time': total_time
    })


def full_course(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    parts = lesson.parts.all().order_by('number')

    if request.method == 'POST' and request.user == lesson.creator:
        # 1. Сначала обрабатываем сохранение изменений существующих частей
        for part in parts:
            # Для лекций
            if part.type == 'LECTURE':
                content_key = f'part_{part.id}_content'
                if content_key in request.POST:
                    part.content = request.POST[content_key]

                    # Обработка загрузки изображения для существующей части
                    image_key = f'part_{part.id}_image'
                    if image_key in request.FILES:
                        image = request.FILES[image_key]
                        fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'lesson_images'))
                        filename = fs.save(f'part_{part.id}_{image.name}', image)
                        part.image = os.path.join('lesson_images', filename)

                    part.save()

            # Для тестов
            elif part.type == 'TEST':
                content_key = f'part_{part.id}_content'
                if content_key in request.POST:
                    part.content = request.POST[content_key]
                    part.save()

        # 2. Затем обрабатываем создание новой части (если указано название)
        part_name = request.POST.get('new_part_name')
        if part_name:  # Только если указано название новой части
            part_type = request.POST.get('new_part_type')

            if part_type == 'LECTURE':
                content = request.POST.get('new_part_content', '')
                new_part = LessonPart.objects.create(
                    name=part_name,
                    lesson=lesson,
                    number=lesson.parts.count() + 1,
                    content=content,
                    type='LECTURE'
                )

                # Обработка загрузки изображения для новой части
                if 'new_part_image' in request.FILES:
                    image = request.FILES['new_part_image']
                    fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'lesson_images'))
                    filename = fs.save(f'part_{new_part.id}_{image.name}', image)
                    new_part.image = os.path.join('lesson_images', filename)
                    new_part.save()

            elif part_type == 'TEST':
                description = request.POST.get('new_test_description', '')
                test_data = json.loads(request.POST.get('test_data', '[]'))

                new_part = LessonPart.objects.create(
                    name=part_name,
                    lesson=lesson,
                    number=lesson.parts.count() + 1,
                    content=description,
                    type='TEST'
                )

                # Создаем вопросы и ответы
                for i, question_data in enumerate(test_data):
                    test_part = TestPart.objects.create(
                        lesson_part=new_part,
                        content=question_data['question'],
                        number=i + 1
                    )

                    for j, answer_data in enumerate(question_data['answers']):
                        Answer.objects.create(
                            test_part=test_part,
                            content=answer_data['text'],
                            is_correct=answer_data['is_correct'],
                            # Можно добавить порядковый номер ответа, если нужно
                        )

        return redirect('full_course', lesson_id=lesson.id)

    return render(request, 'education/full_course.html', {
        'lesson': lesson,
        'parts': parts
    })


@require_POST
def remove_part(request, part_id):
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Требуется авторизация'}, status=403)

    try:
        part = LessonPart.objects.get(id=part_id)
        if part.lesson.creator != request.user:
            return JsonResponse({'success': False, 'error': 'Недостаточно прав'}, status=403)

        part_number = part.number
        lesson_id = part.lesson.id

        # Удаляем связанные изображения
        if part.image:
            image_path = os.path.join(settings.MEDIA_ROOT, str(part.image))
            if os.path.exists(image_path):
                os.remove(image_path)

        # Удаляем часть
        part.delete()

        # Перенумеровываем оставшиеся части
        remaining_parts = LessonPart.objects.filter(lesson_id=lesson_id).order_by('number')
        for i, p in enumerate(remaining_parts, start=1):
            if p.number != i:
                p.number = i
                p.save()

        return JsonResponse({'success': True})
    except LessonPart.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Часть не найдена'}, status=404)
    except Exception as e:
        print(str(e))
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
@csrf_exempt
def check_test(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            data = json.loads(request.body)
            correct = data.get('correct', 0)
            total = data.get('total', 1)
            user_answers = data.get('answers', {})

            # Проверяем ответы пользователя
            answer_objects = Answer.objects.filter(id__in=user_answers.keys())
            detailed_results = []

            for answer in answer_objects:
                detailed_results.append({
                    'answer_id': answer.id,
                    'content': answer.content,
                    'is_correct': answer.is_correct,
                    'user_selected': user_answers.get(str(answer.id), False)
                })

            return JsonResponse({
                'status': 'success',
                'score': round((correct / total) * 100) if total > 0 else 0,
                'correct': correct,
                'total': total,
                'detailed_results': detailed_results
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def create_lesson(request):
    if request.method == 'POST':
        form = LessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.creator = request.user
            lesson.save()
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonForm()

    return render(request, 'education/create_lesson.html', {'form': form})
