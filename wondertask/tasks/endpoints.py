from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tasks.views import TaskViewSet, ExecutorViewSet, ObserverViewSet


task_router = DefaultRouter()
task_router.register('task', TaskViewSet, 'task')
task_router.register('executor', ExecutorViewSet, 'executor')
task_router.register('observer', ObserverViewSet, 'observer')

task_endpoints = [
     path('', include([path('', include(task_router.urls)),]))
]
