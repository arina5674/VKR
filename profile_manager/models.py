import datetime

from django.db import models


class Town(models.Model):
    name = models.CharField(max_length=30, unique=True, verbose_name='Название города')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


class UserInformation(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, verbose_name='Пользователь')
    description = models.CharField(max_length=500, blank=True, verbose_name='Описание')
    town = models.ForeignKey(
        'profile_manager.Town',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        verbose_name='Город',
    )
    address = models.CharField(max_length=150, blank=True, verbose_name='Адрес')
    image = models.ImageField(
        upload_to='profile_images/',
        default='profile_images/default.png',
        verbose_name='Изображение',
    )
    dt_birthday = models.DateField(null=True, verbose_name='Дата рождения')
    status = models.CharField(max_length=150, blank=True, verbose_name='Статус')

    class Meta:
        verbose_name = 'Информация о пользователе'
        verbose_name_plural = 'Информации о пользователях'

    @property
    def age(self):
        if not self.dt_birthday:
            return None
        today = datetime.datetime.now().date()
        return (today - self.dt_birthday).years


class Education(models.Model):
    user = models.ForeignKey(
        'profile_manager.UserInformation',
        on_delete=models.CASCADE,
        verbose_name='Информация о пользователе',
    )
    university = models.CharField(max_length=150, verbose_name='Учебное заведение', default='')
    is_confirmed = models.BooleanField(default=False, verbose_name='Подтверждено')

    class Meta:
        verbose_name = 'Образование'
        verbose_name_plural = 'Образования'


class InterestingFact(models.Model):
    user = models.ForeignKey(
        'profile_manager.UserInformation',
        on_delete=models.CASCADE,
        verbose_name='Информация о пользователе',
    )
    text = models.CharField(max_length=300, verbose_name='Текст интересного факта')

    class Meta:
        verbose_name = 'Интересный факт'
        verbose_name_plural = 'Интересные факты'
