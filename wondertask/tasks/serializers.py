from datetime import timedelta
from django.utils import timezone

from django.shortcuts import get_object_or_404
from django_celery_beat.models import CrontabSchedule
from django_celery_beat.models import PeriodicTask, ClockedSchedule
from rest_framework import serializers
from taggit.models import Tag
from taggit_serializer.serializers import (TagListSerializerField,
                                           TaggitSerializer, )
from django.conf import settings

from accounts.models import User
from accounts.serializers import UserTaskSerializer
from journals.services import notify_service
from tasks import tasks
from tasks.models import (Task, Executor, Observer,
                          Group, Doc, Image, Audio, Comment, TaskTag, TaskSchedule, Favorite, Video)
from tasks.validators import (check_file_extensions, VALID_DOC_FILES,
                              VALID_AUDIO_FILES, VALID_VIDEO_FILES, )


class GroupNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'group_name']


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
    creator = UserTaskSerializer(read_only=True)

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

        return output_data


class TaskSerializer(TaggitSerializer, serializers.ModelSerializer):
    user_tags = TagListSerializerField(required=False)
    system_tags = TagListSerializerField(required=False)
    title = serializers.CharField(required=True)
#    group = GroupNameSerializer()

    class Meta:
        model = Task
        fields = ['url', 'id', 'title', 'description', 'group', 'creation_date', 'deadline',
                  'start_date', 'finish_date',
                  'sum_elapsed_time', 'status', 'priority', 'creator',
                  'user_tags', 'system_tags', 'level', 'parent']
        read_only_fields = ['creation_date',
                            'start_date', 'finish_date',
                            'sum_elapsed_time', 'status', 'creator',
                             'system_tags', 'level']

    def validate_group(self, value):
        if value:
            group = get_object_or_404(Group, id=value.id)
            email = 'anonimous@anonimous.com'
            if group.creator != self.context['request'].user and (
               self.context['request'].user.email != email):
                raise serializers.ValidationError("The user is not owner this selected group")

        return value

    def validate_deadline(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("A deadline must be younger then a creation_date.")

        return value

    def create(self, validated_data):
        user_tags = None
        try:
            user_tags = validated_data['user_tags']
            del validated_data['user_tags']
        except KeyError:
            pass

        task = super(TaskSerializer, self).create(validated_data)
        task.creator = self.context['request'].user

        periodic_task_list = []
        clocked_list = []
        if not task.deadline:
            return task
        for hour in [1]:
            if (task.deadline - task.creation_date) > timedelta(hours=hour):
                time_start_task = task.deadline - timedelta(hours=hour)
                clocked_list.insert(0, ClockedSchedule.objects.create(clocked_time=time_start_task))
                periodic_task_list.append(PeriodicTask.objects.create(
                    name=f"Notification {hour} hours before the deadline for TaskID({task.id})",
                    task="deadline_notification",
                    clocked=clocked_list[0],
                    start_time=time_start_task,
                    args=[task.id, hour],
                    one_off=True,
                ))
        clocked_list.insert(0, ClockedSchedule.objects.create(clocked_time=task.deadline))
        periodic_task_list.append(PeriodicTask.objects.create(
            name=f"Notification task deadline overdue for TaskID({task.id})",
            task="deadline_notification",
            clocked=clocked_list[0],
            start_time=task.deadline,
            args=[task.id, 0],
            one_off=True,
        ))
        task.periodic_tasks.add(*periodic_task_list)
        task.clocked_shedule.add(*clocked_list)

        anonimous_user = User.objects.get(email='anonimous@anonimous.com')
        if task.creator == anonimous_user:
            try:
                email = 'anonimous_group_' + str(task.group.id) + '@anonimous.com'
                anonimous_group_user = User.objects.get(email=email)
            except User.DoesNotExist:
                full_name = 'Anonimous_' + task.group.group_name
                anonimous_group_user = User.objects.create_user(email=email,
                                                                password='qwerty:)',
                                                                full_name=full_name)
                anonimous_group_user.save()
            executor = Executor.objects.create(task=task,
                                         executor=anonimous_group_user)
            task.start_task()
            notify_service.send_notification(task=task, task_action="start_task")
        else:
            executor, created = Executor.objects.get_or_create(task=task,
                                         executor=task.creator)

        if user_tags:
            task.user_tags.add(*list(map(str, user_tags)), tag_kwargs={"user_id": task.creator.id})

        task.save()

        return task

    def update(self, instance, validated_data):
        try:
            if instance.group != validated_data['group']:
                validated_data['group'].group_members.add(instance.creator)
                for executor in instance.executors.all():
                    validated_data['group'].group_members.add(executor.executor)
        except KeyError:
            pass
        return super(TaskSerializer, self).update(instance, validated_data)

    def to_representation(self, instance):
        if instance.status in (instance.IN_PROGRESS, instance.IN_PROGRESS_OVERDUE):
            instance.stop_task()
            instance.start_task()

        output_data = super().to_representation(instance)

        if instance.group:
            output_data['group'] = GroupNameSerializer(instance.group,
                context={'request': self.context['request']}).data

        output_data['creator'] = UserTaskSerializer(instance.creator,
            context={'request': self.context['request']}).data

        executors = instance.executors.all()
        list_executors = [ExecutorListSerializer(el,
            context={'request': self.context['request']}).data for el in executors]
        output_data['executors'] = list_executors

        observers = instance.observers.all()
        list_observers = [ObserverListSerializer(el,
            context={'request': self.context['request']}).data for el in observers]
        output_data['observers'] = list_observers

        output_data['status'] = instance.STATUS_DICT[instance.status]

        user = self.context['request'].user
        if user == instance.creator:
            output_data['role'] = "creator"
        elif user.id in instance.executors.all().values_list("executor", flat=True):
            output_data['role'] = "executor"
        elif user.id in instance.observers.all().values_list("observer", flat=True):
            output_data['role'] = "observer"
        else:
            output_data['role'] = None

        output_data['is_favorite'] = Favorite.objects.filter(executor=user, task=instance).exists()
        return output_data


class TaskListSerializer(TaskSerializer):
    creator = UserTaskSerializer()


class TaskSystemTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class TaskIdsSerializer(serializers.Serializer):
    task_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class ExecutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Executor
        fields = ['id', 'executor']

    def create(self, validated_data):
        task = get_object_or_404(Task, id=self.context['task_id'])
        executor, created = Executor.objects.get_or_create(task=task,
                                                           executor=validated_data['executor'])
        notify_service.send_add_user_to_task_notifications(
            task=task, recipient=validated_data['executor'], role="executor"
        )
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
        notify_service.send_add_user_to_task_notifications(
            task=task, recipient=validated_data['observer'], role="observer"
        )
        return observer


class ObserverListSerializer(ObserverSerializer):
    observer = UserTaskSerializer()


class GroupSerializer(TaggitSerializer, serializers.ModelSerializer):
    creator = UserTaskSerializer(required=False)
    count_open_tasks = serializers.SerializerMethodField(method_name="get_count_open_tasks")

    class Meta:
        model = Group
        fields = '__all__'

    def create(self, validated_data):
        group = super(GroupSerializer, self).create(validated_data)
        group.group_members.add(group.creator)
        group.save()

        return group

    def get_count_open_tasks(self, instance):
        return instance.group_tasks.exclude(status=Task.DONE).count()


class CommentTreeSerializer(serializers.ModelSerializer):

    author = UserTaskSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'task', 'text', 'tree_id', 'level', 'parent', 'creation_date']

    def get_fields(self):
        fields = super(CommentTreeSerializer, self).get_fields()
        fields['children'] = CommentTreeSerializer(read_only=True, many=True)
        return fields


class CommentSerializer(serializers.ModelSerializer):
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    likes = serializers.IntegerField(source="likes.count", read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'task', 'text', 'tree_id', 'level', 'parent', 'creation_date', 'likes']

    def to_representation(self, instance):

        output_data = super().to_representation(instance)
        output_data['author'] = UserTaskSerializer(instance.author,
            context={'request': self.context['request']}).data

        return output_data


class CommentListSerializer(CommentSerializer):
    author = UserTaskSerializer()


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


class VideoSerializer(serializers.ModelSerializer):
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    comment = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )
    video_file = serializers.FileField(max_length=None,
                                       allow_empty_file=True,
                                       use_url=True,
                                       required=False)

    def validate(self, instance):
        check_file_extensions('video_file', instance, VALID_VIDEO_FILES)
        return instance

    class Meta:
        model = Video
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTag
        fields = ['id', 'name', 'user']
        read_only_fields = ['user']


class GroupInviteSerializer(serializers.Serializer):
    users_emails = serializers.ListField(child=serializers.EmailField(), allow_empty=False)


class GroupUserIdsSerializer(serializers.Serializer):
    users_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)


class ActionTagSerializer(serializers.Serializer):
    tags = serializers.ListField(child=serializers.CharField())


class CrontabSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrontabSchedule
        fields = ["minute", "hour", "day_of_week", "day_of_month", "month_of_year", "timezone"]


class TaskScheduleSerializer(serializers.ModelSerializer):
    crontab = CrontabSerializer()

    class Meta:
        model = TaskSchedule
        fields = ["id", "task", "number_of_times", "end_date", "crontab", "repeated_tasks"]
        read_only_fields = ["repeated_tasks"]

    def validate_end_date(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("A end_date must be older then a current moment.")

        return value

    def create(self, validated_data):
        crontab = validated_data.pop("crontab")
        crontab_instance, _ = CrontabSchedule.objects.get_or_create(**crontab)
        task_schedule = TaskSchedule.objects.create(**validated_data,
                                                    crontab=crontab_instance)
        tasks.create_repeats_tasks.delay(validated_data['task'].id)

        return task_schedule

    def update(self, instance, validated_data):
        instance.task = validated_data.get('task', instance.task)
        instance.number_of_times = validated_data.get('number_of_times', instance.number_of_times)
        instance.end_date = validated_data.get('end_date', instance.end_date)

        crontab = validated_data.pop("crontab")
        instance.crontab.minute = crontab.get('minute', instance.crontab.minute)
        instance.crontab.hour = crontab.get('hour', instance.crontab.hour)
        instance.crontab.day_of_week = crontab.get('day_of_week', instance.crontab.day_of_week)
        instance.crontab.day_of_month = crontab.get('day_of_month', instance.crontab.day_of_month)
        instance.crontab.month_of_year = crontab.get('month_of_year',
                                                     instance.crontab.month_of_year)
        instance.crontab.timezone = crontab.get('timezone', instance.crontab.timezone)

        # delete all repeated_tasks and create new repeated tasks
        instance.repeated_tasks.all().delete()
        instance.periodic_tasks.all().delete()
        tasks.create_repeats_tasks.delay(instance.task.id)
        instance.save()
        return instance

    def to_representation(self, instance):
        output = super(TaskScheduleSerializer, self).to_representation(instance)
        output['crontab']['timezone'] = str(instance.crontab.timezone)
        return output
