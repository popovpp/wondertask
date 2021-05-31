from django.urls import path

from accounts.views import UserRegistrationView, get_user_tags

registration_endpoint = [
    path('registration/', UserRegistrationView.as_view()),
    path('user/<int:user_id>/tags/', get_user_tags, name="user_tags")
]
