from django.contrib import admin

from education.models import Lesson, LessonPart


# Register your models here.

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    pass


@admin.register(LessonPart)
class LessonPartAdmin(admin.ModelAdmin):
    pass
