from rest_framework import serializers
from taggit_serializer.serializers import (TagListSerializerField,
                                           TaggitSerializer)

from tasks.models import (Task, Executor, Observer, TaskSystemTags,
                          Group, TaskGroup, Comment, Doc, Image, Audio)
from tasks.validators import (check_file_extensions, VALID_DOC_FILES,
                              VALID_AUDIO_FILES)


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
                if ele['id'] == el['parent']:
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


class RecursiveSerializer(serializers.Serializer):
    """Вывод рекурсивно children"""
    def to_representation(self, value):
        serializer = CommentSerializer(value, context=self.context)
        return serializer.data


class CreateCommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field='id',
        read_only=True
    )
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )

    class Meta:
        model = Comment
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    super_comment = RecursiveSerializer(many=True)
    author = serializers.SlugRelatedField(
        slug_field='id',
        read_only=True
    )
    task = serializers.SlugRelatedField(
        read_only=True,
        slug_field='id',
    )

    class Meta:
        model = Comment
        fields = ('id', 'author', 'task', 'text', 'parent', 'super_comment')


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
