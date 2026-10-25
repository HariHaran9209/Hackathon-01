import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from .models import Project, Task, Suggestion, ChatMessage
from .ai import (
    clean_json_response,
    validate_breakdown_schema,
    fallback_breakdown,
    is_reasoning_prompt,
)


class AIModuleTests(TestCase):
    """
    Unit tests for AI JSON parsing, validation, fallback logic, and reasoning routing.
    """

    def test_clean_json_response_with_markdown_fence(self):
        raw = "Here is your plan:\n```json\n{\"title\": \"Pitchly MVP\", \"tasks\": []}\n```\nEnjoy!"
        cleaned = clean_json_response(raw)
        self.assertEqual(cleaned, '{"title": "Pitchly MVP", "tasks": []}')

    def test_validate_breakdown_schema_valid(self):
        raw_dict = {
            "title": "Autonomous Drone Fleet",
            "tasks": [
                {
                    "title": "Flight Controller",
                    "description": "Implement PID control loops",
                    "column": "todo",
                    "estimate_days": 3.5
                }
            ],
            "suggestions": [
                {
                    "kind": "risk",
                    "content": "Battery degradation over long flights"
                },
                {
                    "kind": "note",
                    "content": "Use ROS2 for messaging"
                }
            ]
        }
        validated = validate_breakdown_schema(raw_dict)
        self.assertEqual(validated["title"], "Autonomous Drone Fleet")
        self.assertEqual(len(validated["tasks"]), 1)
        self.assertEqual(validated["tasks"][0]["title"], "Flight Controller")
        self.assertEqual(validated["tasks"][0]["estimate_days"], 3.5)
        self.assertEqual(len(validated["suggestions"]), 2)

    def test_validate_breakdown_schema_normalizes_invalid_data(self):
        # Empty titles, invalid columns, negative days
        raw_dict = {
            "title": "",
            "tasks": [
                {"title": "", "description": "no title"},  # Should be skipped
                {"title": "Valid Task", "column": "invalid_col", "estimate_days": -5}
            ],
            "suggestions": [
                {"kind": "unknown_kind", "content": "Something"},
                {"kind": "risk", "content": ""}  # Should be skipped
            ]
        }
        validated = validate_breakdown_schema(raw_dict)
        self.assertEqual(validated["title"], "Generated Project Plan")
        self.assertEqual(len(validated["tasks"]), 1)
        self.assertEqual(validated["tasks"][0]["column"], "todo")
        self.assertEqual(validated["tasks"][0]["estimate_days"], 1.0)
        self.assertEqual(len(validated["suggestions"]), 1)
        self.assertEqual(validated["suggestions"][0]["kind"], "note")

    def test_fallback_breakdown_generates_tasks_and_suggestions(self):
        input_text = "Build a real-time collaborative code editor with WebSockets and syntax highlighting."
        result = fallback_breakdown(input_text)

        self.assertIn("title", result)
        self.assertTrue(len(result["tasks"]) >= 3)
        self.assertTrue(len(result["suggestions"]) >= 2)
        # Verify suggestions contain risks and notes
        kinds = [s["kind"] for s in result["suggestions"]]
        self.assertIn("risk", kinds)
        self.assertIn("note", kinds)

    def test_fallback_breakdown_bullet_parsing(self):
        bullet_input = (
            "Smart Garden Watering System\n"
            "- Setup ESP32 soil moisture sensor\n"
            "- Connect MQTT telemetry to backend\n"
            "- Build automated pump relay trigger\n"
            "- Design mobile dashboard"
        )
        result = fallback_breakdown(bullet_input)
        self.assertEqual(result["title"], "Smart Garden Watering System")
        self.assertEqual(len(result["tasks"]), 4)
        self.assertEqual(result["tasks"][0]["title"], "Setup ESP32 soil moisture sensor")

    def test_is_reasoning_prompt_keywords(self):
        # Check all trigger keywords
        self.assertTrue(is_reasoning_prompt("Why should we use PostgreSQL instead of MongoDB?"))
        self.assertTrue(is_reasoning_prompt("What is the biggest technical risk in this architecture?"))
        self.assertTrue(is_reasoning_prompt("Compare Daphne ASGI with Uvicorn."))
        self.assertTrue(is_reasoning_prompt("Explain the tradeoff between in-memory and Redis channels."))
        # Normal query should not trigger reasoning mode
        self.assertFalse(is_reasoning_prompt("Add a new task for writing unit tests."))


class ProjectAPITests(TestCase):
    """
    Integration tests for Router, CRUD endpoints, and the Accept/Reject flow.
    """

    def setUp(self):
        self.client = APIClient()

    def test_create_project_breakdown_never_writes_to_tasks(self):
        """
        Critical Rule Verification:
        POST /api/projects/ must save candidates as Suggestions (kind='task', status='pending')
        and must NEVER write directly to Tasks table!
        """
        payload = {
            "raw_input": "AI voice agent for customer support that connects to Twilio and CRM."
        }
        response = self.client.post(reverse('project-list-create'), data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        project_id = response.data['id']
        project = Project.objects.get(id=project_id)

        # Ensure Tasks table is EMPTY for this project
        self.assertEqual(project.tasks.count(), 0)

        # Ensure Suggestions table HAS task candidates pending
        task_suggestions = project.suggestions.filter(kind='task')
        self.assertTrue(task_suggestions.count() > 0)
        for s in task_suggestions:
            self.assertEqual(s.status, 'pending')

        # Ensure Suggestions has risks and notes
        self.assertTrue(project.suggestions.filter(kind='risk').exists())

    def test_get_project_detail(self):
        project = Project.objects.create(title="Test Board", raw_input="Sample raw idea")
        Task.objects.create(project=project, title="Task 1", column="todo", estimate_days=2.0)
        Suggestion.objects.create(project=project, kind="note", content="A helpful note")

        response = self.client.get(reverse('project-detail', kwargs={'pk': project.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Board")
        self.assertEqual(len(response.data['tasks']), 1)
        self.assertEqual(len(response.data['suggestions']), 1)
        self.assertEqual(response.data['total_days'], 2.0)

    def test_patch_task_moving_and_editing(self):
        project = Project.objects.create(title="Move Task Test", raw_input="Idea")
        task = Task.objects.create(project=project, title="Initial Task", column="todo", estimate_days=1.0)

        # Move to 'doing' and update estimate
        url = reverse('task-detail', kwargs={'pk': task.id})
        patch_payload = {
            "column": "doing",
            "estimate_days": 3.0,
            "order": 1
        }
        response = self.client.patch(url, data=patch_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        task.refresh_from_db()
        self.assertEqual(task.column, "doing")
        self.assertEqual(task.estimate_days, 3.0)
        self.assertEqual(task.order, 1)

    def test_accept_task_suggestion_converts_to_task(self):
        """
        Verify that POST /api/suggestions/{id}/accept/ converts a task suggestion
        into a concrete Task and marks the suggestion accepted.
        """
        project = Project.objects.create(title="Accept Flow Test", raw_input="Testing accept")
        task_payload = {
            "title": "Set up CI/CD pipeline",
            "description": "Configure GitHub Actions workflow for test runs",
            "column": "todo",
            "estimate_days": 2.5
        }
        suggestion = Suggestion.objects.create(
            project=project,
            kind="task",
            content=json.dumps(task_payload),
            status="pending"
        )

        self.assertEqual(project.tasks.count(), 0)

        # Call accept endpoint
        accept_url = reverse('suggestion-accept', kwargs={'pk': suggestion.id})
        response = self.client.post(accept_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, "accepted")

        # Verify task was created on the board
        self.assertEqual(project.tasks.count(), 1)
        created_task = project.tasks.first()
        self.assertEqual(created_task.title, "Set up CI/CD pipeline")
        self.assertEqual(created_task.description, "Configure GitHub Actions workflow for test runs")
        self.assertEqual(created_task.estimate_days, 2.5)
        self.assertEqual(created_task.column, "todo")

    def test_reject_suggestion(self):
        """
        Verify that POST /api/suggestions/{id}/reject/ updates status and does NOT create a task.
        """
        project = Project.objects.create(title="Reject Flow Test", raw_input="Idea")
        suggestion = Suggestion.objects.create(
            project=project,
            kind="task",
            content=json.dumps({"title": "Unwanted task"}),
            status="pending"
        )

        reject_url = reverse('suggestion-reject', kwargs={'pk': suggestion.id})
        response = self.client.post(reject_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        suggestion.refresh_from_db()
        self.assertEqual(suggestion.status, "rejected")
        self.assertEqual(project.tasks.count(), 0)

    def test_chat_endpoint_and_reasoning_mode(self):
        project = Project.objects.create(title="Chat Test Project", raw_input="A high performance cache")

        # Chat with reasoning keyword "why"
        chat_url = reverse('project-chat', kwargs={'pk': project.id})
        response = self.client.post(chat_url, data={"content": "Why choose Redis over Memcached for this?"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['reasoning_mode'])
        self.assertIn("user_message", response.data)
        self.assertIn("assistant_message", response.data)

        # Chat without reasoning keyword
        response2 = self.client.post(chat_url, data={"content": "Give me a quick update on current status."}, format='json')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertFalse(response2.data['reasoning_mode'])

    def test_readme_generation_endpoint(self):
        project = Project.objects.create(title="Pitchly Core", raw_input="An AI copilot for project breakdown.")
        Task.objects.create(project=project, title="Configure Docker", column="done", estimate_days=1.0)
        Task.objects.create(project=project, title="Build Kanban UI", column="doing", estimate_days=2.0)
        Suggestion.objects.create(project=project, kind="risk", content="LLM rate limits")

        readme_url = reverse('project-readme', kwargs={'pk': project.id})
        response = self.client.get(readme_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("readme", response.data)
        readme_md = response.data['readme']
        self.assertIn("# Pitchly Core", readme_md)
        self.assertIn("Configure Docker", readme_md)
        self.assertIn("LLM rate limits", readme_md)
