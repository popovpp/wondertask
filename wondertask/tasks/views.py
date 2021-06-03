import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework import mixins
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import get_object_or_404

from accounts.models import User
from tasks import tasks
from tasks.models import (Task, TaskSystemTags,
                          Group, Doc, Image, Audio, Comment, TaskTag)
from tasks.serializers import (TaskSerializer, ExecutorSerializer,
                               ObserverSerializer, TaskSystemTagsSerializer,
                               GroupSerializer,
                               TaskTreeSerializer, ExecutorListSerializer,
                               ObserverListSerializer, DocSerializer,
                               ImageSerializer, AudioSerializer, CommentSerializer,
                               CommentTreeSerializer, TagSerializer, GroupInviteSerializer)
from tasks.signals import doc_file_delete, audio_file_delete, image_file_delete


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

    class Meta:
        model = Task
        fields = ["status", "priority"]

    @staticmethod
    def filter_tags(queryset, name, value):
        return queryset.filter(user_tags__name__in=value.split(',')).distinct()


class TaskViewSet(ModelViewSet):
    
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TaskFilters
    search_fields = ['$title']
    ordering_fields = ["status", "priority", "creation_date",
                       "deadline", "start_date", "finish_date"]

    def get_queryset(self):
        return Task.objects.all().filter(creator=self.request.user).order_by('-creation_date')

    @action(methods=['GET'], detail=False, url_path="my", url_name="my_tasks",
            permission_classes=[IsAuthenticated])
    def my_tasks(self, request):
        filter_queryset = self.filter_queryset(self.get_queryset())
        queryset = filter_queryset.filter(creator=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(methods=['POST'], detail=True, url_path="add-tags", url_name="add_tags",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def add_tags(self, request, pk=None):
        try:
            tags = request.data['tags']
        except KeyError:
            return Response(data={"detail": "Request has no 'tags' attached"},
                            status=status.HTTP_400_BAD_REQUEST)
        task = get_object_or_404(Task, pk=pk)
        task.user_tags.add(*tags, tag_kwargs={"user": request.user})
        return Response(status=status.HTTP_200_OK)

    @action(methods=['DELETE'], detail=True, url_path="del-tags", url_name="del_tags",
            permission_classes=[IsAuthenticatedOrReadOnly])
    def del_tags(self, request, pk=None):
        try:
            tags = request.data['tags']
        except KeyError:
            return Response(data={"detail": 'Request has no "tags" attached'},
                            status=status.HTTP_400_BAD_REQUEST)
        task = get_object_or_404(Task, pk=pk)
        task.user_tags.remove(*tags)
        return Response(status=status.HTTP_200_OK)


class TaskTreeViewSet(RetrieveListViewSet):
    serializer_class = TaskTreeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Task.objects.filter(creator=self.request.user, level=0).order_by('-creation_date')
        return queryset

    def list(self, request):
        self.serializer_class = TaskSerializer
        return super(TaskTreeViewSet, self).list(request)


class TaskSystemTagsViewSet(ModelViewSet):
    queryset = TaskSystemTags.objects.all()
    serializer_class = TaskSystemTagsSerializer
    permission_classes = [AllowAny]


class ExecutorViewSet(ListCreateRetrieveDestroyViewSet):
    serializer_class = ExecutorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.get_task_queryset(ExecutorListSerializer,
                                      model=Task,
                                      model_related_name="executors")


class ObserverViewSet(ListCreateRetrieveDestroyViewSet):
    serializer_class = ObserverSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return self.get_task_queryset(ObserverListSerializer,
                                      model=Task,
                                      model_related_name="observers")


class GroupViewSet(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(methods=["POST"], detail=True, url_path="invite", url_name="invite_users_in_group",
            serializer_class=GroupInviteSerializer, permission_classes=[IsAuthenticated])
    def invite_users_in_group(self, request, pk=None):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = get_object_or_404(Group, pk=pk)

        if group.creator != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        users = User.objects.filter(email__in=serializer.data['users_emails'])
        if not users:
            return Response(data={"detail": "No users found for these emails"},
                            status=status.HTTP_400_BAD_REQUEST)

        url = request.build_absolute_uri().replace("invite", "accept-invite")
        for user in users:
            tasks.send_invite_in_group.delay(group_name=group.group_name,
                                             url=f'{url}?email={user.email}',
                                             email=user.email)
        return Response(data={"detail": "Invitations will be mailed"}, status=status.HTTP_200_OK)

    @action(methods=["GET"], detail=True, url_path="accept-invite", url_name="accept_invite")
    def accept_invite(self, request, pk=None):
        if 'email' not in request.query_params:
            return Response(data={"detail": "email query param is required"},
                            status=status.HTTP_400_BAD_REQUEST)
        email = request.query_params['email']
        user = get_object_or_404(User, email=email)
        group = Group.objects.get(pk=pk)
        group.group_members.add(user)

        return Response(status=status.HTTP_200_OK)


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.comments.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CommentTreeSerializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(task=task)


class TaskDocViewSet(ModelViewSet):
    serializer_class = DocSerializer
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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
    permission_classes = [AllowAny]

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


class TagViewSet(ModelViewSet):
    queryset = TaskTag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
