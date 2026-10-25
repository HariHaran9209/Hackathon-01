import json
from django.db import models


class Project(models.Model):
    """
    Project model storing the user's raw idea input, generated title, and timestamp.
    """
    title = models.CharField(max_length=255)
    raw_input = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Task(models.Model):
    """
    Task on the Kanban board.
    Only created when explicitly accepted from suggestions or manually added.
    """
    COLUMN_CHOICES = [
        ('todo', 'To Do'),
        ('doing', 'In Progress'),
        ('done', 'Done'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    column = models.CharField(max_length=20, choices=COLUMN_CHOICES, default='todo')
    estimate_days = models.FloatField(default=1.0)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"[{self.column}] {self.title}"


class Suggestion(models.Model):
    """
    AI-generated suggestions (task, risk, note).
    Stored with status='pending'. Tasks are NOT placed on the board until accepted.
    """
    KIND_CHOICES = [
        ('task', 'Task'),
        ('risk', 'Risk'),
        ('note', 'Note'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='suggestions')
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.kind.upper()} ({self.status}): {self.content[:40]}"

    def parse_payload(self):
        """
        Extract structured dictionary from content if stored as JSON,
        or fall back to parsing plain string.
        """
        try:
            data = json.loads(self.content)
            if isinstance(data, dict):
                return {
                    'title': data.get('title', self.content.strip()),
                    'description': data.get('description', ''),
                    'column': data.get('column', 'todo'),
                    'estimate_days': float(data.get('estimate_days', 1.0)),
                }
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

        return {
            'title': self.content.strip(),
            'description': '',
            'column': 'todo',
            'estimate_days': 1.0,
        }


class ChatMessage(models.Model):
    """
    Follow-up chat messages and reasoning exchanges attached to the project.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:30]}"
