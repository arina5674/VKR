from django.contrib.auth.models import User
from rest_framework import serializers

from profile_manager.models import UserInformation


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = '__all__'


class UserInformationSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = UserInformation
        fields = '__all__'
