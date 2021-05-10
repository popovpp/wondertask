from django.conf import settings


def jwt_response_payload_handler(token, user=None, request=None):
    return {
        'token': token,
        'token_lifetime': int(settings.JWT_AUTH['JWT_EXPIRATION_DELTA'].total_seconds())  # seconds
    }
