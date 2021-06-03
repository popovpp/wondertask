from rest_framework import serializers
from taggit.models import Tag
from taggit_serializer.serializers import (TagListSerializerField,
                                           TaggitSerializer, )
from django.shortcuts import get_object_or_404

from tasks.models import (Task, Executor, Observer,
                          Group, Doc, Image, Audio, Comment, TaskTag)
from tasks.validators import (check_file_extensions, VALID_DOC_FILES,
                              VALID_AUDIO_FILES, )
from accounts.serializers import UserTaskSerializer


class GroupNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['group_name']


class TaskTreeSerializer(TaggitSerializer, serializers.ModelSerializer):
    user_tags = TagListSerializerField(required=False, read_only=True)
    title = serializers.CharField(required=True)
    creation_date = serializers.CharField(read_only=True)
    start_date = serializers.CharField(read_only=True)
    last_start_time = serializers.CharField(read_only=True)
    finish_date = serializers.CharField(read_only=True)
    sum_elapsed_time = serializers.CharField(read_only=True)
    status = serializers.IntegerField(read_only=True)
    level = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = ['url', 'id', 'title', 'group', 'creation_date', 'deadline',
                  'start_date', 'finish_date', 'last_start_time',
                  'sum_elapsed_time', 'status', 'priority', 'creator',
                  'user_tags', 'level', 'parent']

    def to_representation(self, instance):

        output_data = TaskSerializer(instance, context={'request': self.context['request']}).data

        all_descendants = instance.get_descendants(include_self=False).order_by('-creation_date')
        lst = []
        for el in all_descendants:
            lst.append(TaskSerializer(el, context={'request': self.context['request']}).data)
        for el in lst:
            for ele in lst:
                if el['id'] == ele['parent']:
                    el['children'] = ele
                    lst.remove(ele)
        output_data['children'] = lst

        return output_data


class TaskSerializer(TaggitSerializer, serializers.ModelSerializer):
    user_tags = TagListSerializerField(required=False)
    system_tags = TagListSerializerField(required=False)

    class Meta:
        model = Task
        fields = ['url', 'id', 'title', 'group', 'creation_date', 'deadline',
                  'start_date', 'finish_date', 'last_start_time',
                  'sum_elapsed_time', 'status', 'priority', 'creator',
                  'user_tags', 'system_tags', 'level', 'parent']
        read_only_fields = ['title', 'creation_date',
                            'start_date', 'finish_date', 'last_start_time',
                            'sum_elapsed_time', 'status', 'creator',
                            'user_tags', 'system_tags', 'level']

    def create(self, validated_data):
        task = super(TaskSerializer, self).create(validated_data)
        task.creator = self.context['request'].user
        if not task.group:
            task.group, create = Group.objects.get_or_create(group_name='FREE_TASKS', creator=task.creator)
        task.save()

        return task

    def to_representation(self, instance):
        output_data = super().to_representation(instance)
        output_data['group'] = instance.group.group_name

        executors = instance.executors.all()
        list_executors = [ExecutorListSerializer(el).data for el in executors]
        output_data['executors'] = list_executors

        observers = instance.observers.all()
        list_observers = [ObserverListSerializer(el).data for el in observers]
        output_data['observers'] = list_observers

        return output_data


class TaskSystemTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class ExecutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Executor
        fields = ['id', 'executor']

    def create(self, validated_data):
        task = get_object_or_404(Task, id=self.context['task_id'])
        executor, created = Executor.objects.get_or_create(task=task,
                                                           executor=validated_data['executor'])

        return executor


class ExecutorListSerializer(ExecutorSerializer):
    executor = UserTaskSerializer()


class ObserverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observer
        fields = ['id', 'observer']

    def create(self, validated_data):
        task = get_object_or_404(Task, id=self.context['task_id'])
        observer, created = Observer.objects.get_or_create(task=task,
                                                           observer=validated_data['observer'])

        return observer


class ObserverListSerializer(ObserverSerializer):
    observer = UserTaskSerializer()


class GroupSerializer(TaggitSerializer, serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'

    def create(self, validated_data):
        group = super(GroupSerializer, self).create(validated_data)
        group.group_members.add(group.creator)
        group.save()

        return group


class CommentTreeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'author', 'task', 'text', 'tree_id', 'level', 'parent']

    def to_representation(self, instance):
        children_comments = instance.get_descendants(include_self=False)
        comments_list = []
        for comment in children_comments:
            comments_list.append(super().to_representation(comment))
        for child in comments_list:
            for parent in comments_list:
                if parent['id'] == child['parent']:
                    parent['children'] = child
                    comments_list.remove(child)
        comment = super().to_representation(instance)
        comment['children'] = comments_list
        return comment


class CommentSerializer(serializers.ModelSerializer):
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )

    class Meta:
        model = Comment
        fields = ['id', 'author', 'task', 'text', 'tree_id', 'level', 'parent']


class DocSerializer(serializers.ModelSerializer):
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    comment = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    doc_file = serializers.FileField(max_length=None,
                                     allow_empty_file=True,
                                     use_url=True,
                                     required=False)

    def validate(self, instance):
        check_file_extensions('doc_file', instance, VALID_DOC_FILES)
        return instance

    class Meta:
        model = Doc
        fields = '__all__'


class ImageSerializer(serializers.ModelSerializer):
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    comment = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    image_file = serializers.ImageField(max_length=None,
                                        allow_empty_file=True,
                                        use_url=True,
                                        required=False)

    class Meta:
        model = Image
        fields = '__all__'


class AudioSerializer(serializers.ModelSerializer):
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    comment = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    audio_file = serializers.FileField(max_length=None,
                                       allow_empty_file=True,
                                       use_url=True,
                                       required=False)

    def validate(self, instance):
        check_file_extensions('audio_file', instance, VALID_AUDIO_FILES)
        return instance

    class Meta:
        model = Audio
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTag
        fields = ['id', 'name', 'slug', 'user']
        read_only_fields = ['slug', 'user']


class GroupInviteSerializer(serializers.Serializer):
    users_emails = serializers.ListField(child=serializers.EmailField())


class ActionTagSerializer(serializers.Serializer):
    tags = serializers.ListField(child=serializers.CharField())