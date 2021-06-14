from django.urls import path, include
from rest_framework.routers import DefaultRouter

from journals.views import NotificationViewSet

journal_router = DefaultRouter()

journal_router.register('notifications', NotificationViewSet, 'notifications')

journal_endpoints = [
    path('', include([path('', include(journal_router.urls)), ]))
]