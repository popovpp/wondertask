from django.urls import include, path
from rest_framework.routers import DefaultRouter
from accounts.views import (UserRegistrationView, get_user_tags, UserViewSet,
	                        UserSendEmailView, RedirectUserView)
from . import views

user_router = DefaultRouter()
user_router.register('user', UserViewSet, 'user')

registration_endpoint = [
    path('registration/', UserRegistrationView.as_view()),
    path('user/<int:user_id>/tags/', get_user_tags, name="user_tags"),
    path('', include([path('', include(user_router.urls)), ]))
]

recover_password_endpoints = [
    path('sendemail/', UserSendEmailView.as_view()),
    path('newpassword/<str:secret>/', RedirectUserView.as_view()),
    path('password-reset/<str:secret>/', views.recover),
]
