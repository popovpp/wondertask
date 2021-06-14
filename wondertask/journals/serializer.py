from rest_framework import serializers

from journals.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "message", "type", "task", "group", "created", "recipients"]


class ActionReadNotificationsSerializer(serializers.Serializer):
    notifications = serializers.ListField(child=serializers.IntegerField())
