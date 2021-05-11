from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework import generics
from rest_framework.views import APIView

from tasks.models import Task, Executor, Observer
from tasks.serializers import TaskSerializer, ExecutorSerializer, ObserverSerializer


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]


class ExecutorViewSet(ModelViewSet):
    queryset = Executor.objects.all()
    serializer_class = ExecutorSerializer
    permission_classes = [AllowAny]


class ObserverViewSet(ModelViewSet):
    queryset = Observer.objects.all()
    serializer_class = ObserverSerializer
    permission_classes = [AllowAny]
