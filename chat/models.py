from django.db import models

# Create your models here.


class ChatSession(models.Model):
    uuid = models.UUIDField(verbose_name='Уникальный идентификатор сессии чата')
    first_user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Первый пользователь',
        related_name='chat_sessions_created',
    )
    second_user = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Второй пользователь',
        related_name='chat_sessions_invited',
    )
    dt_start = models.DateTimeField(auto_now_add=True, verbose_name='Дата и время создания чата')
    dt_last_message = models.DateTimeField(auto_now=True, verbose_name='Дата и время последнего сообщения')

    class Meta:
        verbose_name = 'Сессия чата'
        verbose_name_plural = 'Сессии чата'
        unique_together = ('first_user', 'second_user',)


class Message(models.Model):
    chat_session = models.ForeignKey('chat.ChatSession', on_delete=models.CASCADE, verbose_name='Сессия чата')
    text = models.CharField(max_length=500, verbose_name='Текст сообщения')
    sender = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Отправитель',
    )
    dt_send = models.DateTimeField(auto_now=True, verbose_name='Дата и время отправки')
    is_received = models.BooleanField(default=False, verbose_name='Получено')
    is_checked = models.BooleanField(default=False, verbose_name='Прочитано')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'

    def mark_as_received(self):
        self.is_received = True
        self.save()

    def mark_as_checked(self):
        self.is_checked = True
        self.save()

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'sender_id': self.sender.id if self.sender else None,
            'timestamp': self.dt_send.isoformat(),
            'is_received': self.is_received,
            'is_checked': self.is_checked
        }

    def save(self, *args, **kwargs):
        # При создании нового сообщения автоматически ставим is_received=False
        if not self.pk and not hasattr(self, 'is_received'):
            self.is_received = False
        super().save(*args, **kwargs)
