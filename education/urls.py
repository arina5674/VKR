from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from education import views
from education.views import courses_list, lesson_detail, full_course

urlpatterns = [
    # post views
    path('', courses_list, name='list_of_courses'),
    path('create/', views.create_lesson, name='create_lesson'),
    path('courses/<int:lesson_id>/', lesson_detail, name='lesson_detail'),
    path('full_courses/<int:lesson_id>/', full_course, name='full_course'),
    path('<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('<int:lesson_id>/full/', views.full_course, name='full_course'),
    path('check_test/', views.check_test, name='check_test'),
    path('remove_part/<int:part_id>/', views.remove_part, name='remove_part'),
    path('profiles/<int:teacher_id>/', courses_list, name='list_of_courses_for_profile'),
    # path('<int:user_id>/', views.get_concrete_course, name='get_concrete_course'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
