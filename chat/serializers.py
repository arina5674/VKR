from rest_framework import serializers

from chat.models import Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'text', 'sender', 'dt_send', 'is_received', 'is_checked']