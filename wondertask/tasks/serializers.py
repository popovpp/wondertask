from django_celery_beat.models import PeriodicTask, CrontabSchedule, ClockedSchedule
from rest_framework import serializers
from taggit.models import Tag
from taggit_serializer.serializers import (TagListSerializerField,
                                           TaggitSerializer, )
from django.shortcuts import get_object_or_404

from tasks import tasks
from tasks.models import (Task, Executor, Observer,
                          Group, Doc, Image, Audio, Comment, TaskTag, TaskSchedule)
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

    def get_fields(self):
        fields = super(TaskTreeSerializer, self).get_fields()
        fields['children'] = TaskTreeSerializer(read_only=True, many=True)
        return fields

    def to_representation(self, instance):
        if instance.status in (instance.IN_PROGRESS, instance.IN_PROGRESS_OVERDUE):
            instance.stop_task()
            instance.start_task()

        output_data = super().to_representation(instance)
        if instance.group:
            output_data['group'] = instance.group.group_name
        else:
            output_data['group'] = "null"

        return output_data


class TaskSerializer(TaggitSerializer, serializers.ModelSerializer):
    user_tags = TagListSerializerField(required=False)
    system_tags = TagListSerializerField(required=False)
    title = serializers.CharField(required=True)

    class Meta:
        model = Task
        fields = ['url', 'id', 'title', 'group', 'creation_date', 'deadline',
                  'start_date', 'finish_date', 
                  'sum_elapsed_time', 'status', 'priority', 'creator',
                  'user_tags', 'system_tags', 'level', 'parent']
        read_only_fields = ['creation_date',
                            'start_date', 'finish_date', 
                            'sum_elapsed_time', 'status', 'creator',
                            'user_tags', 'system_tags', 'level']


    def validate_group(self, value):
        if value:
            group = get_object_or_404(Group, id=value.id)
            if group.creator != self.context['request'].user:
                raise serializers.ValidationError("The user is not owner this selected group")

        return value

    def create(self, validated_data):
        task = super(TaskSerializer, self).create(validated_data)
        task.creator = self.context['request'].user
        if task.deadline < task.creation_date:
            raise serializers.ValidationError("A deadline must be younger then a creation_date.")
        task.save()

        return task

    def to_representation(self, instance):
        if instance.status in (instance.IN_PROGRESS, instance.IN_PROGRESS_OVERDUE):
            instance.stop_task()
            instance.start_task()

        output_data = super().to_representation(instance)
        if instance.group:
            output_data['group'] = instance.group.group_name
        else:
            output_data['group'] = "null"

        executors = instance.executors.all()
        list_executors = [ExecutorListSerializer(el).data for el in executors]
        output_data['executors'] = list_executors

        observers = instance.observers.all()
        list_observers = [ObserverListSerializer(el).data for el in observers]
        output_data['observers'] = list_observers

        output_data['status'] = instance.STATUS_DICT[instance.status]

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

    def get_fields(self):
        fields = super(CommentTreeSerializer, self).get_fields()
        fields['children'] = CommentTreeSerializer(read_only=True, many=True)
        return fields


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


class CrontabSerializer(serializers.ModelSerializer):
    timezone = serializers.CharField(write_only=True)

    class Meta:
        model = CrontabSchedule
        fields = ["minute", "hour", "day_of_week", "day_of_month", "month_of_year", "timezone"]


class TaskScheduleSerializer(serializers.ModelSerializer):
    crontab = CrontabSerializer()

    class Meta:
        model = TaskSchedule
        fields = ["id", "task", "number_of_times", "end_date", "crontab"]

    def create(self, validated_data):
        crontab = validated_data.pop("crontab")
        crontab_instance, _ = CrontabSchedule.objects.get_or_create(**crontab)
        tasks.create_repeats_tasks.delay(validated_data['task'].id)
        task_schedule, _ = TaskSchedule.objects.get_or_create(**validated_data, crontab=crontab_instance)
        return task_schedule

    def update(self, instance, validated_data):
        crontab = validated_data.pop("crontab")
        instance.crontab.minute = crontab.get('minute', instance.crontab.minute)
        instance.crontab.hour = crontab.get('hour', instance.crontab.hour)
        instance.crontab.day_of_week = crontab.get('day_of_week', instance.crontab.day_of_week)
        instance.crontab.day_of_month = crontab.get('day_of_month', instance.crontab.day_of_month)
        instance.crontab.month_of_year = crontab.get('month_of_year', instance.crontab.month_of_year)
        instance.crontab.timezone = crontab.get('timezone', instance.crontab.timezone)

        instance.task = validated_data.get('task', instance.task)
        instance.number_of_times = validated_data.get('number_of_times', instance.number_of_times)
        instance.end_date = validated_data.get('end_date', instance.end_date)

        instance.repeated_tasks.all().delete()
        tasks.create_repeats_tasks.delay(validated_data['task'].id)

        instance.save()
        return instance
