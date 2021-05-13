from django.contrib import admin

from tasks.models import Task


class TaskModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'creation_date', 'creator', 'start_date', 
                    'parent']
    list_display_links = ['id']
    search_fields = ['id']

    class Meta:
        model = Task


admin.site.register(Task, TaskModelAdmin)
