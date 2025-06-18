from rest_framework import serializers

from education.models import LessonPart, Lesson


class LessonPartSerializer(serializers.ModelSerializer):

    class Meta:
        model = LessonPart
        fields = '__all__'


class LessonSerializer(serializers.ModelSerializer):
    lesson_part_set = LessonPartSerializer(many=True)

    class Meta:
        model = Lesson
        fields = '__all__'
