from django.contrib import admin
from .models import Project, Task, Suggestion, ChatMessage

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at')
    search_fields = ('title', 'raw_input')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'project', 'column', 'estimate_days', 'order')
    list_filter = ('column', 'project')
    search_fields = ('title', 'description')

@admin.register(Suggestion)
class SuggestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'kind', 'status', 'project')
    list_filter = ('kind', 'status', 'project')
    search_fields = ('content',)

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'project', 'role', 'created_at')
    list_filter = ('role', 'project')
