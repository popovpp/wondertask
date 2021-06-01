#from django.urls import path
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts.views import UserRegistrationView, get_user_tags, UserViewSet


user_router = DefaultRouter()
user_router.register('user', UserViewSet, 'user')

registration_endpoint = [
    path('registration/', UserRegistrationView.as_view()),
    path('user/<int:user_id>/tags/', get_user_tags, name="user_tags"),
    path('', include([path('', include(user_router.urls)), ]))
]



#registration_endpoint = [
#    path('registration/', UserRegistrationView.as_view()),
#    path('', include([path('', include(user_router.urls)), ]))
#]
