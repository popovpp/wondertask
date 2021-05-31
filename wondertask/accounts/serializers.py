from rest_framework import serializers

from accounts.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name']

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserTaskSerializer(serializers.ModelSerializer):
    avatar_image = serializers.ImageField(max_length=None,
                                          allow_empty_file=True,
                                          use_url=True,
                                          required=False)
    full_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ['url', 'id', 'email', 'full_name', 'avatar_image']


class AvatarSerializer(serializers.ModelSerializer):
    
    avatar_image = serializers.ImageField(max_length=None,
                                          allow_empty_file=True,
                                          use_url=True,
                                          required=False)

    class Meta:
        model = User
        fields = ['id', 'avatar_image']
