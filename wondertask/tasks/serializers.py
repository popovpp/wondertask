from rest_framework import serializers
from taggit_serializer.serializers import (TagListSerializerField,
                                           TaggitSerializer)

from tasks.models import (Task, Executor, Observer, TaskSystemTags, 
                          Group, TaskGroup)


class TaskTreeSerializer(TaggitSerializer, serializers.ModelSerializer):
    
    user_tags = TagListSerializerField()

    class Meta:
        model = Task
        fields = ['url', 'id', 'title', 'creation_date', 'deadline',
                  'start_date', 'finish_date', 'last_start_time',
                  'sum_elapsed_time', 'status', 'priority', 'creator',
                  'user_tags', 'tree_id', 'level', 'parent']

    def to_representation(self, instance):
        resp = super().to_representation(instance)
        descendants = instance.get_descendants(include_self=False)

        lst = []
        for el in descendants:
            lst.append(super().to_representation(el))
        for el in lst:
            for ele in lst:
                if ele['id']== el['parent']:
                    ele['children'] = el
                    lst.remove(el)
        resp['children'] = lst

        return resp


class TaskSerializer(TaggitSerializer, serializers.ModelSerializer):
    
    user_tags = TagListSerializerField()

    class Meta:
        model = Task
        fields = ['url', 'id', 'title', 'creation_date', 'deadline',
                  'start_date', 'finish_date', 'last_start_time',
                  'sum_elapsed_time', 'status', 'priority', 'creator',
                  'user_tags', 'tree_id', 'level', 'parent']


class TaskSystemTagsSerializer(TaggitSerializer, serializers.ModelSerializer):
    
    system_tags = TagListSerializerField()
    task = TaskSerializer(read_only=True)

    class Meta:
        model = TaskSystemTags
        fields = '__all__'           
       

class ExecutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Executor
        fields = '__all__'


class ObserverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observer
        fields = '__all__'


class GroupSerializer(TaggitSerializer, serializers.ModelSerializer):
    
    class Meta:
        model = Group
        fields = ['group_name']


class TaskGroupSerializer(TaggitSerializer, serializers.ModelSerializer):
    
    class Meta:
        model = TaskGroup
        fields = ['id', 'task', 'group']
