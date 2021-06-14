from rest_framework import serializers

from journals.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipients = serializers.SerializerMethodField(method_name="get_recipients")

    class Meta:
        model = Notification
        fields = ["id", "message", "type", "task", "group", "created", "recipients"]

    def get_recipients(self, instance):
        return [obj.user.id for obj in instance.recipients.all()]


class ActionReadNotificationsSerializer(serializers.Serializer):
    notifications = serializers.ListField(child=serializers.IntegerField())
