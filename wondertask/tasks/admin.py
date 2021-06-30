from django.contrib import admin

from tasks.models import Task, Comment, Doc, Image, Audio, TaskSchedule, Group


class TaskModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'creation_date', 'creator', 'start_date',
                    'parent']
    list_display_links = ['id']
    search_fields = ['id']

    class Meta:
        model = Task


class CommentModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'author', 'task', 'text', 'parent', 'creation_date']
    list_display_links = ['id']

    class Meta:
        model = Doc


class DocModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'comment', 'doc_file']
    list_display_links = ['id']

    class Meta:
        model = Doc


class ImageModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'comment', 'image_file']
    list_display_links = ['id']

    class Meta:
        model = Doc


class AudioModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'comment', 'audio_file']
    list_display_links = ['id']

    class Meta:
        model = Doc


class GroupModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'group_name', 'creator']
    list_display_links = ['id']

    class Meta:
        model = Group


admin.site.register(Task, TaskModelAdmin)
admin.site.register(Comment, CommentModelAdmin)
admin.site.register(Doc, DocModelAdmin)
admin.site.register(Image, ImageModelAdmin)
admin.site.register(Audio, AudioModelAdmin)
admin.site.register(TaskSchedule)
admin.site.register(Group, GroupModelAdmin)
