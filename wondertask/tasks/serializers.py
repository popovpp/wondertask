from rest_framework import serializers

from tasks.models import Task, Executor, Observer


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class ExecutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Executor
        fields = '__all__'


class ObserverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observer
        fields = '__all__'
