from django import forms
from .models import Lesson, LessonPart, TestPart, Answer

class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['name', 'difficulty', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'name': 'Название урока',
            'description': 'Описание урока',
            'difficulty': 'Сложность'
        }

class LessonPartForm(forms.ModelForm):
    class Meta:
        model = LessonPart
        fields = ['name', 'type', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }
        labels = {
            'name': 'Название части',
            'type': 'Тип части',
            'content': 'Содержание'
        }

class TestPartForm(forms.ModelForm):
    class Meta:
        model = TestPart
        fields = ['content']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['content', 'is_correct']