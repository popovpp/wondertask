from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework.generics import get_object_or_404

from tasks.models import (Task, TaskSystemTags,
                          Group, TaskGroup, Doc, Image, Audio, Comment, TaskTag)
from tasks.serializers import (TaskSerializer, ExecutorSerializer,
                               ObserverSerializer, TaskSystemTagsSerializer,
                               GroupSerializer, TaskGroupSerializer,
                               TaskTreeSerializer, ExecutorListSerializer,
                               ObserverListSerializer, DocSerializer,
                               ImageSerializer, AudioSerializer, CommentSerializer,
                               CommentTreeSerializer, TagSerializer)
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


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all().order_by('-creation_date')
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]

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
        queryset = Task.objects.filter(level=0).order_by('-creation_date')
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


class CommentViewSet(ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.comments.filter(level=0)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = CommentTreeSerializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        task = get_object_or_404(Task, pk=self.kwargs.get('task_id'))
        serializer.save(author=self.request.user, task=task)


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
