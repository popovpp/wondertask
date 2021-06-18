from rest_framework import serializers
from django.urls import resolve

from journals.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipients = serializers.SerializerMethodField(method_name="get_recipients")

    class Meta:
        model = Notification
        fields = ["id", "message", "type", "task", "group", "created", "recipients"]

    def get_recipients(self, instance):
        return [obj.user.id for obj in instance.recipients.all()]

    def to_representation(self, instance):
        output_data = super().to_representation(instance)
        if not (self.context['request'] and 'actions_journal' in 
                                             resolve(self.context['request'].path_info).url_name):
            if self.context['request'].user in [x.user for x in instance.recipients.all()]:
        	    output_data['message'] = output_data['message'].replace(
        		                         self.context['request'].user.full_name, 'Вы').replace(
        		                         'л(а)', 'ли').replace(
                                         'перенес', 'перенесли')
        return output_data


class ActionReadNotificationsSerializer(serializers.Serializer):
    notifications = serializers.ListField(child=serializers.IntegerField())
