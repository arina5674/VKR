import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from chat.models import Message, ChatSession


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        self.user = self.scope.get("user", AnonymousUser())

        if not self.user.is_authenticated:
            await self.close()
            return

        try:
            self.chat_session = await sync_to_async(ChatSession.objects.get)(uuid=self.room_name)

            first_user = await sync_to_async(lambda: self.chat_session.first_user)()
            second_user = await sync_to_async(lambda: self.chat_session.second_user)()

            if self.user not in [first_user, second_user]:
                await self.close()
                return

        except ChatSession.DoesNotExist:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        await self.mark_companion_messages_as_read()
        await self.accept()
        await self.send_history()

    async def mark_companion_messages_as_read(self):
        """Помечает все сообщения собеседника как прочитанные"""
        companion = await self.get_companion()
        if not companion:
            return

        # Находим все непрочитанные сообщения от собеседника
        unread_messages = await sync_to_async(list)(
            Message.objects.filter(
                chat_session=self.chat_session,
                sender=companion,
                is_checked=False
            )
        )

        for message in unread_messages:
            message.is_checked = True
            await sync_to_async(message.save)(update_fields=['is_checked'])

            # Уведомляем всех участников об обновлении статуса
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message.status.update',
                    'message_id': message.id,
                    'is_checked': True,
                    'is_received': True
                }
            )

    async def message_status_update(self, event):
        """Обработчик обновления статуса сообщения"""
        await self.send(text_data=json.dumps({
            'type': 'message_status_update',
            'message_id': event['message_id'],
            'is_checked': event['is_checked'],
            'is_received': event['is_received']
        }))

    async def send_history(self):
        messages = await sync_to_async(list)(
            Message.objects.filter(
                chat_session=self.chat_session
            ).select_related('sender').order_by('dt_send')[:50]
        )

        for message in messages:
            # Для старых сообщений получателя помечаем как прочитанные
            if await sync_to_async(lambda: message.sender != self.user)():
                if not message.is_checked:
                    message.is_checked = True
                    await sync_to_async(message.save)(update_fields=['is_checked'])

            await self.send_message_to_client(message, is_history=True)

    async def send_message_to_client(self, message, is_history=False):
        message_data = await sync_to_async(self.serialize_message)(message)
        message_data['is_history'] = is_history
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            **message_data
        }))

    def serialize_message(self, message):
        return {
            'message': message.text,
            'sender_id': message.sender.id if message.sender else None,
            'sender_name': message.sender.username if message.sender else None,
            'message_id': message.id,
            'timestamp': message.dt_send.isoformat(),
            'is_received': message.is_received,
            'is_checked': message.is_checked,
            'is_initial_load': True  # Флаг, что это загрузка истории
        }

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            # Помечаем все сообщения собеседника как полученные перед выходом
            await self.mark_companion_messages_as_received()

            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def mark_companion_messages_as_received(self):
        """Помечает все сообщения собеседника как полученные"""
        companion = await self.get_companion()
        if not companion:
            return

        unreceived_messages = await sync_to_async(list)(
            Message.objects.filter(
                chat_session=self.chat_session,
                sender=companion,
                is_received=False
            )
        )

        for message in unreceived_messages:
            message.is_received = True
            await sync_to_async(message.save)(update_fields=['is_received'])

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message.status.update',
                    'message_id': message.id,
                    'is_checked': message.is_checked,
                    'is_received': True
                }
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if not isinstance(data, dict):
                return

            message_type = data.get('type')

            if message_type == 'new_message':
                await self.handle_new_message(data)
            elif message_type == 'message_read':
                await self.handle_message_read(data)

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON format")
        except Exception as e:
            await self.send_error(str(e))

    async def handle_new_message(self, data):
        message_text = data.get('message', '').strip()
        if not message_text:
            return

        # Создаем сообщение с начальными статусами
        message = await sync_to_async(Message.objects.create)(
            chat_session=self.chat_session,
            text=message_text,
            sender=self.user,
            is_received=False,  # Получатель еще не получил
            is_checked=False  # Получатель еще не прочитал
        )

        # Отправляем сообщение в группу
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                **await sync_to_async(self.serialize_message)(message),
                'is_initial': False  # Это новое сообщение, не из истории
            }
        )

    async def handle_message_read(self, data):
        message_id = data.get('message_id')
        if not message_id:
            return

        try:
            message = await sync_to_async(Message.objects.get)(id=message_id)
            if message and await sync_to_async(lambda: message.sender.id)() != self.user.id:
                message.is_checked = True
                await sync_to_async(message.save)(update_fields=['is_checked'])

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'message.checked',
                        'message_id': message.id
                    }
                )
        except Message.DoesNotExist:
            pass

    async def chat_message(self, event):
        # Убедитесь, что тип события соответствует тому, что ожидает клиент
        await self.send(text_data=json.dumps({
            'type': 'chat_message',  # Должно совпадать с тем, что проверяется в onmessage
            'message': event.get('message'),
            'sender_id': event.get('sender_id'),
            'sender_name': event.get('sender_name'),
            'message_id': event.get('message_id'),
            'timestamp': event.get('timestamp'),
            'is_received': event.get('is_received', False),
            'is_checked': event.get('is_checked', False)
        }))

    async def message_checked(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_checked',  # Должно совпадать с проверкой в onmessage
            'message_id': event['message_id']
        }))

    async def send_error(self, error_msg):
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_msg
        }))

    async def mark_all_received_messages_as_read(self):
        """Помечает все полученные сообщения как прочитанные"""
        unread_messages = await sync_to_async(list)(
            Message.objects.filter(
                chat_session=self.chat_session,
                sender__id__ne=self.user.id,
                is_checked=False
            )
        )

        for message in unread_messages:
            message.is_checked = True
            await sync_to_async(message.save)(update_fields=['is_checked'])

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message.checked',
                    'message_id': message.id
                }
            )

    async def get_companion(self):
        """Возвращает объект собеседника"""
        first_user = await sync_to_async(lambda: self.chat_session.first_user)()
        second_user = await sync_to_async(lambda: self.chat_session.second_user)()

        if self.user == first_user:
            return second_user
        return first_user