from django.contrib import admin

from tasks.models import Task, Comment, Doc, Image, Audio


class TaskModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'creation_date', 'creator', 'start_date',
                    'parent']
    list_display_links = ['id']
    search_fields = ['id']

    class Meta:
        model = Task


class DocModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'task', 'comment', 'doc_file']
    list_display_links = ['id']

    class Meta:
        model = Doc


admin.site.register(Task, TaskModelAdmin)
admin.site.register(Comment)
admin.site.register(Doc, DocModelAdmin)
admin.site.register(Image)
admin.site.register(Audio)
