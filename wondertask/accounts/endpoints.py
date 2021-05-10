from django.urls import path

from accounts.views import UserRegistrationView


registration_endpoint = [
    path('registration/', UserRegistrationView.as_view())
]