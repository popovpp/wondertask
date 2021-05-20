from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import get_object_or_404
from http import HTTPStatus

from tasks.models import (Task, TaskSystemTags,
                          Group, TaskGroup, Doc, Image, Audio, Comment)
from tasks.serializers import (TaskSerializer, ExecutorSerializer,
                               ObserverSerializer, TaskSystemTagsSerializer,
                               GroupSerializer, TaskGroupSerializer,
                               TaskTreeSerializer, ExecutorListSerializer,
                               ObserverListSerializer, DocSerializer,
                               ImageSerializer, AudioSerializer, CommentSerializer,
                               CommentTreeSerializer)
from tasks.signals import doc_file_delete, audio_file_delete, image_file_delete


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all().order_by('-creation_date')
    serializer_class = TaskSerializer
    permission_classes = [AllowAny]


class TaskTreeViewSet(ModelViewSet):
    serializer_class = TaskTreeSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = Task.objects.filter(level=0).order_by('-creation_date')
        return queryset

    def get_serializer_context(self):
        context = super(TaskTreeViewSet, self).get_serializer_context()
        context['request'] = self.request
        return context

    def list(self, request):
        self.serializer_class = TaskSerializer
        return super(TaskTreeViewSet, self).list(request)

    def create(self, request):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)

    def destroy(self, request, pk):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)

    def update(self, request, pk=None):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)


class TaskSystemTagsViewSet(ModelViewSet):
    queryset = TaskSystemTags.objects.all()
    serializer_class = TaskSystemTagsSerializer
    permission_classes = [AllowAny]


class ExecutorViewSet(ModelViewSet):
    serializer_class = ExecutorSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.method == 'GET':
            self.serializer_class = ExecutorListSerializer
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.executors.all()

    def get_serializer_context(self):
        context = super(ExecutorViewSet, self).get_serializer_context()
        context['task_id'] = self.kwargs.get('task_id')
        return context

    def update(self, request, pk=None, **kwargs):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)

    def partial_update(self, request, pk=None, **kwargs):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)


class ObserverViewSet(ModelViewSet):
    serializer_class = ObserverSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        if self.request.method == 'GET':
            self.serializer_class = ObserverListSerializer
        task = get_object_or_404(Task, pk=self.kwargs['task_id'])
        return task.observers.all()

    def get_serializer_context(self):
        context = super(ObserverViewSet, self).get_serializer_context()
        context['task_id'] = self.kwargs.get('task_id')
        return context

    def update(self, request, pk=None, **kwargs):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)

    def partial_update(self, request, pk=None, **kwargs):
        return Response({'result': 'Method is not allowly.'},
                        status=HTTPStatus.BAD_REQUEST)


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
