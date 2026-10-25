import json
from rest_framework import serializers
from .models import Project, Task, Suggestion, ChatMessage


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'project', 'title', 'description', 'column', 'estimate_days', 'order']
        read_only_fields = ['id', 'project']


class SuggestionSerializer(serializers.ModelSerializer):
    payload = serializers.SerializerMethodField()

    class Meta:
        model = Suggestion
        fields = ['id', 'project', 'kind', 'content', 'status', 'payload']
        read_only_fields = ['id', 'project']

    def get_payload(self, obj):
        return obj.parse_payload()


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'project', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'project', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)
    suggestions = SuggestionSerializer(many=True, read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)
    total_days = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'title', 'raw_input', 'created_at', 'tasks', 'suggestions', 'messages', 'total_days']
        read_only_fields = ['id', 'title', 'created_at', 'tasks', 'suggestions', 'messages', 'total_days']

    def get_total_days(self, obj):
        return round(sum(t.estimate_days for t in obj.tasks.all()), 1)


class ProjectCreateSerializer(serializers.Serializer):
    raw_input = serializers.CharField(required=True, allow_blank=False)
    title = serializers.CharField(required=False, allow_blank=True)
