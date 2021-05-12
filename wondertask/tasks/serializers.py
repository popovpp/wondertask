from rest_framework import serializers
from taggit_serializer.serializers import (TagListSerializerField,
                                           TaggitSerializer)

from tasks.models import Task, Executor, Observer


class TaskSerializer(TaggitSerializer, serializers.ModelSerializer):
    
    tags = TagListSerializerField()

    class Meta:
        model = Task
        fields = '__all__'
        fields = [
            'title', 'tags']
#    start_date 
#    finish_date 
#    last_start_time 
#    sum_elapsed_time 
#    status 
# s   priority 
#    creator
           
       

class ExecutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Executor
        fields = '__all__'


class ObserverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observer
        fields = '__all__'
