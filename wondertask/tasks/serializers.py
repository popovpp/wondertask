from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from tasks.models import (Task, Executor, Observer, Comment,
                          Doc, Image, Audio)
from tasks.validators import (check_file_extensions, VALID_DOC_FILES,
                              VALID_AUDIO_FILES)


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class ExecutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Executor
        fields = '__all__'


class ObserverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Observer
        fields = '__all__'


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
