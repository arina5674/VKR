from django.contrib import admin

from education.models import Lesson, LessonPart, TestPart, Answer


# Register your models here.

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    pass


@admin.register(LessonPart)
class LessonPartAdmin(admin.ModelAdmin):
    pass


@admin.register(TestPart)
class TestPartAdmin(admin.ModelAdmin):
    pass


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass