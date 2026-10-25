import json
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import status, views, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Project, Task, Suggestion, ChatMessage
from .serializers import (
    ProjectSerializer,
    ProjectCreateSerializer,
    TaskSerializer,
    SuggestionSerializer,
    ChatMessageSerializer,
)
from .ai import generate_project_breakdown, generate_chat_reply
from .consumers import notify_project_update


class ProjectListCreateView(views.APIView):
    """
    GET /api/projects/ - List recent projects
    POST /api/projects/ - Submit raw_input to trigger AI breakdown and project initialization.
    """
    def get(self, request):
        projects = Project.objects.all()[:20]
        serializer = ProjectSerializer(projects, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ProjectCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_input = serializer.validated_data['raw_input']
        custom_title = serializer.validated_data.get('title', '').strip()

        # Step 1: Execute AI Breakdown (or rule-based fallback)
        breakdown = generate_project_breakdown(raw_input)
        title = custom_title or breakdown.get('title', 'Generated Project Plan')

        # Step 2: Persist Project
        project = Project.objects.create(
            title=title,
            raw_input=raw_input
        )

        # Step 3: CRUCIAL REQUIREMENT:
        # Save proposed tasks as Suggestions (kind='task', status='pending').
        # Never write directly to Tasks table without user accepting!
        for task_candidate in breakdown.get('tasks', []):
            Suggestion.objects.create(
                project=project,
                kind='task',
                content=json.dumps(task_candidate),
                status='pending'
            )

        # Step 4: Save risks and notes as Suggestions
        for sugg in breakdown.get('suggestions', []):
            Suggestion.objects.create(
                project=project,
                kind=sugg.get('kind', 'note'),
                content=sugg.get('content', ''),
                status='pending'
            )

        # Step 5: Create initial system chat greeting
        ChatMessage.objects.create(
            project=project,
            role='system',
            content=f"Welcome to '{project.title}'! Your breakdown is ready. Review suggestions on the right to accept tasks into your Kanban board, or ask any technical 'why' or 'risk' question below."
        )

        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)


class ProjectDetailView(views.APIView):
    """
    GET /api/projects/{id}/ - Retrieve full project with tasks, suggestions, and chat history.
    """
    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        serializer = ProjectSerializer(project)
        return Response(serializer.data)


class TaskDetailView(views.APIView):
    """
    PATCH /api/tasks/{id}/ - Move columns, reorder, or update task attributes.
    DELETE /api/tasks/{id}/ - Remove task from board.
    """
    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        serializer = TaskSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated_task = serializer.save()

        # Broadcast live update across WebSocket
        notify_project_update(
            project_id=task.project_id,
            event_type='task_updated',
            data=TaskSerializer(updated_task).data
        )

        return Response(TaskSerializer(updated_task).data)

    def delete(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        project_id = task.project_id
        task_id = task.id
        task.delete()

        notify_project_update(
            project_id=project_id,
            event_type='task_deleted',
            data={'id': task_id}
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskCreateView(views.APIView):
    """
    POST /api/projects/{id}/tasks/ - Directly add a manual task to project.
    """
    def post(self, request, project_id):
        project = get_object_or_404(Project, pk=project_id)
        serializer = TaskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(project=project)

        notify_project_update(
            project_id=project.id,
            event_type='task_created',
            data=TaskSerializer(task).data
        )

        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def accept_suggestion(request, pk):
    """
    POST /api/suggestions/{id}/accept/
    Converts a task suggestion into a live Kanban Task.
    Sets suggestion status to 'accepted'.
    """
    suggestion = get_object_or_404(Suggestion, pk=pk)
    suggestion.status = 'accepted'
    suggestion.save()

    created_task = None
    if suggestion.kind == 'task':
        payload = suggestion.parse_payload()
        existing_count = Task.objects.filter(project=suggestion.project, column=payload.get('column', 'todo')).count()
        created_task = Task.objects.create(
            project=suggestion.project,
            title=payload.get('title', 'New Task'),
            description=payload.get('description', ''),
            column=payload.get('column', 'todo'),
            estimate_days=payload.get('estimate_days', 1.0),
            order=existing_count
        )

    # Broadcast update
    broadcast_data = {
        'suggestion': SuggestionSerializer(suggestion).data,
    }
    if created_task:
        broadcast_data['task'] = TaskSerializer(created_task).data

    notify_project_update(
        project_id=suggestion.project_id,
        event_type='suggestion_accepted',
        data=broadcast_data
    )

    return Response({
        'status': 'accepted',
        'suggestion': SuggestionSerializer(suggestion).data,
        'task': TaskSerializer(created_task).data if created_task else None
    })


@api_view(['POST'])
def reject_suggestion(request, pk):
    """
    POST /api/suggestions/{id}/reject/
    Marks a suggestion as 'rejected'.
    """
    suggestion = get_object_or_404(Suggestion, pk=pk)
    suggestion.status = 'rejected'
    suggestion.save()

    broadcast_data = {
        'suggestion': SuggestionSerializer(suggestion).data
    }
    notify_project_update(
        project_id=suggestion.project_id,
        event_type='suggestion_rejected',
        data=broadcast_data
    )

    return Response({
        'status': 'rejected',
        'suggestion': SuggestionSerializer(suggestion).data
    })


@api_view(['POST'])
def project_chat(request, pk):
    """
    POST /api/projects/{id}/chat/
    Submit a follow-up query to the AI copilot.
    Routes to REASONING_MODEL for 'why', 'risk', 'compare', 'tradeoff', 'explain',
    otherwise uses FAST_MODEL.
    """
    project = get_object_or_404(Project, pk=pk)
    user_text = request.data.get('content') or request.data.get('message', '').strip()
    if not user_text:
        return Response({'error': 'Message content cannot be blank.'}, status=status.HTTP_400_BAD_REQUEST)

    # 1. Save user message
    user_msg = ChatMessage.objects.create(
        project=project,
        role='user',
        content=user_text
    )

    # 2. Gather history
    history = [
        {'role': m.role, 'content': m.content}
        for m in project.messages.all().order_by('created_at')
    ]

    # 3. Call AI
    ai_result = generate_chat_reply(project, history, user_text)

    # 4. Save assistant response
    assistant_msg = ChatMessage.objects.create(
        project=project,
        role='assistant',
        content=ai_result['content']
    )

    # 5. Broadcast to WebSocket
    notify_project_update(
        project_id=project.id,
        event_type='chat_message_created',
        data={
            'user_message': ChatMessageSerializer(user_msg).data,
            'assistant_message': ChatMessageSerializer(assistant_msg).data,
            'model_used': ai_result.get('model_used'),
            'reasoning_mode': ai_result.get('reasoning_mode', False)
        }
    )

    return Response({
        'user_message': ChatMessageSerializer(user_msg).data,
        'assistant_message': ChatMessageSerializer(assistant_msg).data,
        'model_used': ai_result.get('model_used'),
        'reasoning_mode': ai_result.get('reasoning_mode', False)
    })


@api_view(['GET'])
def project_readme(request, pk):
    """
    GET /api/projects/{id}/readme/
    Returns a beautifully structured, comprehensive README in Markdown format.
    """
    project = get_object_or_404(Project, pk=pk)

    tasks_todo = project.tasks.filter(column='todo')
    tasks_doing = project.tasks.filter(column='doing')
    tasks_done = project.tasks.filter(column='done')

    risks = project.suggestions.filter(kind='risk')
    notes = project.suggestions.filter(kind='note')

    total_days = sum(t.estimate_days for t in project.tasks.all())

    lines = [
        f"# {project.title}",
        "",
        "> Generated automatically by [Pitchly](https://github.com/your-username/pitchly) — AI Project Copilot.",
        "",
        "## 💡 Project Concept",
        "",
        project.raw_input.strip(),
        "",
        "---",
        "",
        "## 📊 Roadmap & Execution Board",
        "",
        f"**Total Estimated Effort:** `{total_days:.1f} engineer-days`",
        "",
    ]

    # In Progress
    lines.append("### ⏳ In Progress (`doing`)")
    if tasks_doing.exists():
        for t in tasks_doing:
            desc = f" - {t.description}" if t.description else ""
            lines.append(f"- [ ] **{t.title}** (`{t.estimate_days}d`){desc}")
    else:
        lines.append("_No tasks currently in progress._")
    lines.append("")

    # Backlog / Todo
    lines.append("### 📋 Backlog (`todo`)")
    if tasks_todo.exists():
        for t in tasks_todo:
            desc = f" - {t.description}" if t.description else ""
            lines.append(f"- [ ] **{t.title}** (`{t.estimate_days}d`){desc}")
    else:
        lines.append("_No pending tasks in backlog._")
    lines.append("")

    # Completed
    lines.append("### ✅ Completed (`done`)")
    if tasks_done.exists():
        for t in tasks_done:
            desc = f" - {t.description}" if t.description else ""
            lines.append(f"- [x] **{t.title}** (`{t.estimate_days}d`){desc}")
    else:
        lines.append("_No completed tasks yet._")
    lines.append("")

    # Risks & Mitigations
    lines.append("---")
    lines.append("## ⚠️ Critical Risks & Mitigations")
    lines.append("")
    if risks.exists():
        for r in risks:
            status_icon = "🟢 [Accepted]" if r.status == 'accepted' else ("🔴 [Rejected]" if r.status == 'rejected' else "🟡 [Pending]")
            lines.append(f"- {status_icon} {r.content}")
    else:
        lines.append("- _No specific risks flagged._")
    lines.append("")

    # Architectural Notes
    lines.append("## 🛠️ Architectural Recommendations")
    lines.append("")
    if notes.exists():
        for n in notes:
            lines.append(f"- {n.content}")
    else:
        lines.append("- _Standard modern full-stack web architecture recommended._")
    lines.append("")

    # Run section
    lines.extend([
        "---",
        "## 🚀 Getting Started",
        "",
        "### Prerequisites",
        "- Python 3.11+",
        "- Node.js 18+",
        "- (Optional) Docker & Docker Compose",
        "",
        "### Local Run Instructions",
        "```bash",
        "# 1. Clone repository",
        "git clone <repository-url>",
        "cd pitchly",
        "",
        "# 2. Launch with Docker Compose",
        "docker compose up --build",
        "```",
        "",
        "Visit `http://localhost:5173` to explore the project board.",
        "",
        "---",
        "*Created with Pitchly Copilot powered by NVIDIA & Nebius Token Factory.*"
    ])

    markdown_text = "\n".join(lines)

    if request.query_params.get('format') == 'raw':
        return HttpResponse(markdown_text, content_type='text/markdown; charset=utf-8')

    return Response({
        'project_id': project.id,
        'title': project.title,
        'readme': markdown_text
    })
