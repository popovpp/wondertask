from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.generics import get_object_or_404
from django.db.models import Q

from tasks.models import (Task, Executor, Observer, TaskSystemTags, 
	                      Group, TaskGroup)
from tasks.serializers import (TaskSerializer, ExecutorSerializer, 
                               ObserverSerializer, TaskSystemTagsSerializer,
                               GroupSerializer, TaskGroupSerializer,
                               TaskTreeSerializer)


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]


class TaskTreeViewSet(ModelViewSet):
    serializer_class = TaskTreeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Task.objects.filter(level=0)
        return queryset

    def list(self, request):

        self.serializer_class = TaskSerializer

        return super(TaskTreeViewSet, self).list(request)


class TaskSystemTagsViewSet(ModelViewSet):
    queryset = TaskSystemTags.objects.all()
    serializer_class = TaskSystemTagsSerializer
    permission_classes = [AllowAny]


class ExecutorViewSet(ModelViewSet):
    serializer_class = ExecutorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.executors.all()

 
class ObserverViewSet(ModelViewSet):
    queryset = Observer.objects.all()
    serializer_class = ObserverSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.observers.all()


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [AllowAny]


class TaskGroupViewSet(ModelViewSet):
    queryset = TaskGroup.objects.all()
    serializer_class = TaskGroupSerializer
    permission_classes = [AllowAny]


class GroupTasksViewSet(ModelViewSet):
    queryset = TaskGroup.objects.all()
    serializer_class = TaskGroupSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        group = get_object_or_404(Group, pk=self.kwargs['group_id'])
        return TaskGroup.objects.filter(group=group)
