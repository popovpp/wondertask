import base64

import django_filters
from django.db.models import Q
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from taggit.models import Tag
from django.contrib.auth import login

from journals.services import notify_service
from tasks.models import (Task, Group, Doc, Image, Audio, Comment, TaskTag, TaskSchedule, InvitationInGroup, Favorite,
                          Video)
from tasks.permissions import IsOwner, PermissionPost, IsExecutorOrObserver
from tasks.serializers import (TaskSerializer, ExecutorSerializer,
                               ObserverSerializer, TaskSystemTagsSerializer,
                               GroupSerializer,
                               TaskTreeSerializer, ExecutorListSerializer,
                               ObserverListSerializer, DocSerializer,
                               ImageSerializer, AudioSerializer, CommentSerializer,
                               CommentTreeSerializer, TagSerializer, GroupInviteSerializer,
                               ActionTagSerializer, TaskScheduleSerializer,
                               TaskListSerializer, GroupUserIdsSerializer, VideoSerializer, TaskIdsSerializer)
from tasks.services import tag_service, group_service
from tasks.signals import doc_file_delete, audio_file_delete, image_file_delete, video_file_delete
from accounts.models import User
from accounts.serializers import UserTaskSerializer

try:
    anonimous_user = User.objects.get(email='anonimous@anonimous.com')
except User.DoesNotExist:
    anonimous_user = User.objects.create_user(email='anonimous@anonimous.com', password='qwerty:)',
                                              full_name='Anonimous User')
    anonimous_user.save()


class ListCreateRetrieveDestroyViewSet(mixins.CreateModelMixin,
                                       mixins.RetrieveModelMixin,
                                       mixins.DestroyModelMixin,
                                       mixins.ListModelMixin,
                                       GenericViewSet):

    def get_task_queryset(self, serializer_type, model, model_related_name):
        if self.request.method == 'GET':
            self.serializer_class = serializer_type
        obj = get_object_or_404(model, pk=self.kwargs['task_id'])
        return getattr(obj, model_related_name).all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['task_id'] = self.kwargs.get('task_id')
        return context


class RetrieveListViewSet(mixins.RetrieveModelMixin,
                          mixins.ListModelMixin,
                          GenericViewSet):
    pass


class TaskFilters(django_filters.FilterSet):
    creation_date = django_filters.DateFromToRangeFilter(field_name="creation_date")
    deadline = django_filters.DateFromToRangeFilter(field_name="deadline")
    start_date = django_filters.DateFromToRangeFilter(field_name="start_date")
    finish_date = django_filters.DateFromToRangeFilter(field_name="finish_date")
    tags = django_filters.CharFilter(field_name="user_tags", method='filter_tags')
    keyword = django_filters.CharFilter(field_name="keyword", method='keyword_filter')

    class Meta:
        model = Task
        fields = ["status", "priority"]

    @staticmethod
    def filter_tags(queryset, name, value):
        tags = value.replace(' ', '').upper().split(',')
        return queryset.filter(Q(user_tags__name__in=tags) |
                               Q(system_tags__name__in=tags)).distinct()

    def keyword_filter(self, queryset, name, value):
        result = {
            "creator": queryset.filter(creator=self.request.user),
            "executor": queryset.filter(executors__executor=self.request.user).exclude(creator=self.request.user),
            "observers": queryset.filter(observers__observer=self.request.user),
            "favorite": queryset.filter(favorite__executor=self.request.user)
        }
        return result.get(value, queryset)

class TaskViewSet(ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [PermissionPost|IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TaskFilters
    search_fields = ['$title']
    ordering_fields = ["status", "priority", "creation_date",
                       "deadline", "start_date", "finish_date"]

    def get_queryset(self):
        if self.request.user.is_authenticated == False:
            login(self.request, anonimous_user)
            return Task.objects.all().filter(creator=anonimous_user).order_by('-creation_date')
        else:
            queryset = Task.objects.filter(
                Q(creator=self.request.user) |
                Q(executors__executor=self.request.user) |
                Q(observers__observer=self.request.user)
            )
            groups = Group.objects.all()
            for group in groups:
                if self.request.user in group.group_members.all():
                    queryset = queryset | Task.objects.all().filter(group=group).order_by('-creation_date')
            return queryset.order_by('-creation_date').distinct()

    @action(methods=['GET'], detail=False, url_path="my", url_name="my_tasks",
            permission_classes=[IsAuthenticated])
    def my_tasks(self, request):
        queryset = self.filter_queryset(Task.objects.filter(
                Q(creator=self.request.user) |
                Q(executors__executor=self.request.user) |
                Q(observers__observer=self.request.user)
            ).order_by('-creation_date')).distinct()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path="add-tags", url_name="add_tags",
            permission_classes=[IsAuthenticatedOrReadOnly], serializer_class=ActionTagSerializer)
    def add_tags(self, request, pk=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_tags, system_tags = tag_service.filtering_tags(serializer.data['tags'])
        non_existent_system_tags = tag_service.get_non_existent_system_tags(system_tags)
        if non_existent_system_tags:
            return Response({"detail": f"This system tags: {non_existent_system_tags} not existing"})

        task = tag_service.add_tags_to_task(task_id=pk, user_id=request.user.id,
                                            user_tags=user_tags, system_tags=system_tags)
        serializer_task = TaskSerializer(instance=task, context=self.get_serializer_context())
        return Response(data=serializer_task.data, status=status.HTTP_200_OK)

    @action(methods=['DELETE'], detail=True, url_path="del-tags", url_name="del_tags",
            permission_classes=[IsAuthenticatedOrReadOnly], serializer_class=ActionTagSerializer)
    def del_tags(self, request, pk=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_tags, system_tags = tag_service.filtering_tags(serializer.data['tags'])
        task = tag_service.remove_tags_from_task(task_id=pk, user_tags=user_tags,
                                                 system_tags=system_tags)
        serializer_task = TaskSerializer(instance=task, context=self.get_serializer_context())
        return Response(data=serializer_task.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path="start-task", url_name="start_task",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def start_task(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        task.start_task()
        task.save()
        serializer = TaskSerializer(task, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path="stop-task", url_name="stop_task",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def stop_task(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        task.stop_task()
        task.save()
        serializer = TaskSerializer(task, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path="finish-task", url_name="finish_task",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def finish_task(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        task.finish_task()
        task.save()
        notify_service.send_notification(task=task, task_action="finish_task")
        serializer = TaskSerializer(task, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['GET'], detail=True, url_path="doubling-task", url_name="doubling_task",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def doubling_task(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        duplicated_task = Task.objects.create(creator=task.creator,
                                              title=task.title,
                                              deadline=(timezone.now()+(task.deadline-task.creation_date)),
                                              priority=task.priority,
                                              user_tags=task.user_tags,
                                              system_tags=task.system_tags,
                                              group=task.group,
                                              parent=task.parent)
        duplicated_task.save()
        serializer = TaskSerializer(duplicated_task, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path="add-parent", url_name="add_parent",
            permission_classes=[IsAuthenticatedOrReadOnly], serializer_class=TaskSerializer)
    def add_parent(self, request, pk=None):
        parent_task = Task.objects.create(**request.data)
        child_task = get_object_or_404(Task, pk=pk)
        parent_task.group = child_task.group
        parent_task.creator = request.user
        child_task.parent = parent_task
        parent_task.save()
        child_task.save()
        serializer_task = TaskTreeSerializer(instance=parent_task, context=self.get_serializer_context())
        return Response(data=serializer_task.data, status=status.HTTP_200_OK)

    @action(
        methods=['POST'], detail=True,
        url_path="favorite", url_name="favorite",
        permission_classes=[IsAuthenticated, IsExecutorOrObserver],
    )
    def favorite(self, request, pk=None):
        task = get_object_or_404(Task, pk=pk)
        self.check_object_permissions(self.request, task)
        favorite, is_created = Favorite.objects.get_or_create(task=task, executor=request.user)
        if not is_created:
            favorite.delete()
        return Response(data=self.serializer_class(task, context={'request': request}).data, status=status.HTTP_200_OK)

    def create(self, request):
        if self.request.user.is_authenticated == False:
            login(self.request, anonimous_user)
        return super(TaskViewSet, self).create(request, permission_classes=[IsAuthenticatedOrReadOnly])

    @action(
        methods=['DELETE'], detail=False, url_path="delete/bulk", url_name="bulk_delete",
        permission_classes=[IsAuthenticated, IsOwner],
        serializer_class=TaskIdsSerializer
    )
    def bulk_delete(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        Task.objects.filter(pk__in=serializer.data['task_ids']).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskTreeViewSet(RetrieveListViewSet):
    serializer_class = TaskTreeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Task.objects.filter(creator=self.request.user, level=0).order_by('-creation_date')
        groups = Group.objects.all()
        for group in groups:
            if self.request.user in group.group_members.all():
                queryset = queryset | Task.objects.all().filter(group=group, level=0).order_by('-creation_date')
        return queryset.order_by('-creation_date')

    def list(self, request):
        self.serializer_class = TaskListSerializer
        return super(TaskTreeViewSet, self).list(request)


class TaskSystemTagsViewSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TaskSystemTagsSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ExecutorViewSet(ListCreateRetrieveDestroyViewSet):
    serializer_class = ExecutorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return self.get_task_queryset(ExecutorListSerializer,
                                      model=Task,
                                      model_related_name="executors")


class ObserverViewSet(ListCreateRetrieveDestroyViewSet):
    serializer_class = ObserverSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return self.get_task_queryset(ObserverListSerializer,
                                      model=Task,
                                      model_related_name="observers")


class GroupViewSet(ModelViewSet):
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        groups = Group.objects.all()
        queryset = groups.filter(creator=self.request.user)
        for group in groups:
            if self.request.user in group.group_members.all():
                queryset = queryset | groups.filter(id=group.id)
        return queryset.order_by('id')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(methods=["POST"], detail=True, url_path="invite", url_name="invite_users_in_group",
            serializer_class=GroupInviteSerializer, permission_classes=[IsAuthenticated, IsOwner])
    def invite_users_in_group(self, request, pk=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        emails = serializer.data['users_emails']

        non_existent_emails = group_service.get_non_existent_user_emails(emails=emails)
        if non_existent_emails:
            return Response(
                data={"detail": f"No users found for these emails: {non_existent_emails}"},
                status=status.HTTP_400_BAD_REQUEST)

        group = get_object_or_404(Group, pk=pk)
        group_service.invite_users_in_group(
            group=group,
            url=request.build_absolute_uri("/v1/tasks/groups/accept-invite/"),
            emails=emails,
        )
        return Response(data={"msg": "Invitations will be mailed"}, status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=True, url_path="invite-link", url_name="create_invite_link",
            serializer_class=GroupInviteSerializer, permission_classes=[IsAuthenticated, IsOwner])
    def create_invite_link(self, request, pk=None):
        invitation_token = InvitationInGroup.objects.create(group_id=pk, is_multiple=True)
        token = base64.urlsafe_b64encode(str(invitation_token.id).encode()).decode()
        link = request.build_absolute_uri("/v1/tasks/groups/accept-invite/?secret=" + token)
        return Response(data={"link": link}, status=status.HTTP_201_CREATED)


    @action(methods=["GET"], detail=False, url_path="accept-invite", url_name="accept_invite")
    def accept_invite(self, request):
        group_service.accept_invite_in_group(request=request)
        return Response(status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True, url_path="tasks-list", url_name="tasks_list")
    def tasks_list(self, request, pk=None):

        self.serializer_class = TaskSerializer
        queryset = Task.objects.filter(group=pk).order_by('-creation_date')

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True, url_path="members-list", url_name="members_list")
    def members_list(self, request, pk=None):
        self.serializer_class = UserTaskSerializer
        group = get_object_or_404(Group, pk=pk)
        group_members = group.group_members.all()

        if 'search' in request.query_params:
            search = request.query_params.get('search')
            group_members = group.group_members.filter(Q(email__icontains=search) | Q(full_name__icontains=search))

        group_members_ids = [user.id for user in group_members]
        queryset = User.objects.filter(pk__in=group_members_ids)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=["POST"], detail=True, url_path="remove-members", url_name="remove_members",
            serializer_class=GroupUserIdsSerializer, permission_classes=[IsAuthenticated, IsOwner])
    def remove_members(self, request, pk=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = get_object_or_404(Group, pk=pk)
        group.group_members.remove(*User.objects.filter(id__in=serializer.data['users_ids']))
        return Response(data={"msg": "Users removed from group!"}, status=status.HTTP_200_OK)

    @action(
        methods=['POST'], detail=True, url_path="add-task/(?P<task_id>\d+)", url_name="add_task",
        permission_classes=[IsAuthenticated, IsOwner],
    )
    def add_task(self, request, pk=None, task_id=None):
        group = get_object_or_404(Group, pk=pk)
        task = get_object_or_404(Task, pk=task_id)
        task.group = group
        task.save()
        return Response(status=status.HTTP_200_OK)

    @action(
        methods=['POST'], detail=True, url_path="add-task/bulk", url_name="add_task_bulk",
        permission_classes=[IsAuthenticated, IsOwner], serializer_class=TaskIdsSerializer
    )
    def add_task_bulk(self, request, pk=None):
        group = get_object_or_404(Group, pk=pk)
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        tasks = Task.objects.filter(pk__in=serializer.data['task_ids'])
        for task in tasks:
            task.group = group
        Task.objects.bulk_update(tasks, ['group'])
        return Response(status=status.HTTP_200_OK)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.comments.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CommentTreeSerializer(instance, context={'request': request})
        return Response(serializer.data)

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(task=task)


class TaskDocViewSet(ModelViewSet):
    serializer_class = DocSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.docs.all()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(task=task, comment=None)

    def perform_destroy(self, instance):
        doc_file_delete(Doc, instance=instance)
        instance.delete()


class CommentDocViewSet(ModelViewSet):
    serializer_class = DocSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'],
                                    task__id=self.kwargs['task_id'])
        return comment.docs.all()

    def perform_create(self, serializer):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'],
                                    task__id=self.kwargs['task_id'])
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        serializer.save(task=task, comment=comment)

    def perform_destroy(self, instance):
        doc_file_delete(Doc, instance=instance)
        instance.delete()


class TaskImageViewSet(ModelViewSet):
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.images.all()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(task=task)

    def perform_destroy(self, instance):
        image_file_delete(Image, instance=instance)
        instance.delete()


class CommentImageViewSet(ModelViewSet):
    serializer_class = ImageSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'])
        return comment.images.all()

    def perform_create(self, serializer):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'],
                                    task__id=self.kwargs['task_id'])
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        serializer.save(task=task, comment=comment)

    def perform_destroy(self, instance):
        image_file_delete(Image, instance=instance)
        instance.delete()


class TaskAudioViewSet(ModelViewSet):
    serializer_class = AudioSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.audios.all()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(task=task)

    def perform_destroy(self, instance):
        audio_file_delete(Audio, instance=instance)
        instance.delete()


class CommentAudioViewSet(ModelViewSet):
    serializer_class = AudioSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'],
                                    task__id=self.kwargs['task_id'])
        return comment.audios.all()

    def perform_create(self, serializer):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'],
                                    task__id=self.kwargs['task_id'])
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        serializer.save(task=task, comment=comment)

    def perform_destroy(self, instance):
        audio_file_delete(Audio, instance=instance)
        instance.delete()


class TaskVideoViewSet(ModelViewSet):
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.videos.all()

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(task=task)

    def perform_destroy(self, instance):
        video_file_delete(Video, instance=instance)
        instance.delete()


class CommentVideoViewSet(ModelViewSet):
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'],
                                    task__id=self.kwargs['task_id'])
        return comment.videos.all()

    def perform_create(self, serializer):
        comment = get_object_or_404(Comment, id=self.kwargs['comment_id'],
                                    task__id=self.kwargs['task_id'])
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        serializer.save(task=task, comment=comment)

    def perform_destroy(self, instance):
        video_file_delete(Video, instance=instance)
        instance.delete()


class TagViewSet(ModelViewSet):
    queryset = TaskTag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TaskScheduleViewSet(ModelViewSet):
    queryset = TaskSchedule.objects.all().order_by('-id')
    serializer_class = TaskScheduleSerializer
    permission_classes = [AllowAny]
