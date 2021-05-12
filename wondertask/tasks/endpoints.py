from django.urls import include, path
from rest_framework.routers import DefaultRouter

from tasks.views import (TaskViewSet, ExecutorViewSet, ObserverViewSet,
                         CommentViewSet, TaskDocViewSet, CommentDocViewSet,
                         TaskImageViewSet, CommentImageViewSet, TaskAudioViewSet,
                         CommentAudioViewSet)

task_router = DefaultRouter()
task_router.register('task', TaskViewSet, 'task')
task_router.register('executor', ExecutorViewSet, 'executor')
task_router.register('observer', ObserverViewSet, 'observer')

task_router.register(r'task/(?P<task_id>\d+)/comment', CommentViewSet, 'comment')

task_router.register(r'task/(?P<task_id>\d+)/doc', TaskDocViewSet, 'task_doc')
task_router.register(r'task/(?P<task_id>\d+)/comment/(?P<comment_id>\d+)/doc',
                     CommentDocViewSet, 'comment_doc')

task_router.register(r'task/(?P<task_id>\d+)/image', TaskImageViewSet, 'task_image')
task_router.register(r'task/(?P<task_id>\d+)/comment/(?P<comment_id>\d+)/image',
                     CommentImageViewSet, 'comment_image')

task_router.register(r'task/(?P<task_id>\d+)/audio', TaskAudioViewSet, 'task_audio')
task_router.register(r'task/(?P<task_id>\d+)/comment/(?P<comment_id>\d+)/audio',
                     CommentAudioViewSet, 'comment_audio')

task_endpoints = [
    path('', include([path('', include(task_router.urls)), ]))
]
