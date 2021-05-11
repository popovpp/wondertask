"""
Provide implementation of custom JWT serializers.

References:
    - https://stackoverflow.com/questions/34332074/django-rest-jwt-login-using-username-or-email/46191939#46191939
"""
from django.contrib.auth import (
    authenticate,
    get_user_model,
)
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework_jwt.serializers import JSONWebTokenSerializer
from rest_framework_jwt.settings import api_settings
from django.conf import settings

User = get_user_model()

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
jwt_decode_handler = api_settings.JWT_DECODE_HANDLER
jwt_get_username_from_payload = api_settings.JWT_PAYLOAD_GET_USERNAME_HANDLER


class CustomJWTSerializer(JSONWebTokenSerializer):
    """
    Obtain token with e-mail address or username implementation.

    References:
        - https://stackoverflow.com/questions/34332074/django-rest-jwt-login-using-username-or-email/46191939#46191939
    """
    username_field = 'email'

    def validate(self, attrs):
        """
        Validate incoming requests.
        """
        password = attrs.get('password')
        user = User.objects.filter(email=attrs.get('email')).first()

        if user is None:
            msg = _('Account with this email does not exists.')
            raise serializers.ValidationError(msg)

        credentials = {
            'email': user.email,
            'password': password,
        }

        if not all(credentials.values()):
            msg = _('Must include "{username_field}" and "password".')
            msg = msg.format(username_field=self.username_field)
            raise serializers.ValidationError(msg)

        user = authenticate(**credentials)

        if not user:
            msg = _('Unable to log in with provided credentials.')
            raise serializers.ValidationError(msg)

        if not user.is_active:
            msg = _('User account is disabled.')
            raise serializers.ValidationError(msg)

        payload = jwt_payload_handler(user)

        return {
            'token': jwt_encode_handler(payload),
            'user': user,
            'token_lifetime': int(settings.JWT_AUTH['JWT_EXPIRATION_DELTA'].total_seconds())  # seconds
        }
