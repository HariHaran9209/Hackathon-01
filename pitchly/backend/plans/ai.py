"""
Pitchly AI Copilot Module (plans/ai.py)
---------------------------------------
Powered by NVIDIA and open-weights models served via Nebius Token Factory.

Model Selection Strategy:
- FAST_MODEL: Used for breakdown, rapid task decomposition, and general workflow queries.
- REASONING_MODEL: Used whenever user prompts ask "why", "risk", "compare", "tradeoff", or "explain",
  engaging deep architectural reasoning and comprehensive risk assessment.

NOTE: Confirm exact model IDs in the Nebius Token Factory catalog:
https://studio.nebius.ai/
"""

import json
import os
import re
from typing import Any, Dict, List, Optional
from openai import OpenAI

# Environment variables - never hardcode secrets
# Confirm exact model IDs in the Nebius Token Factory catalog:
NEBIUS_BASE_URL = os.getenv('NEBIUS_BASE_URL', 'https://api.studio.nebius.ai/v1').strip()
NEBIUS_API_KEY = os.getenv('NEBIUS_API_KEY', '').strip()

# Fast vs. Reasoning model split
# FAST_MODEL: Low latency, lightweight model (e.g., Meta-Llama-3.1-8B-Instruct)
FAST_MODEL = os.getenv('FAST_MODEL', 'meta-llama/Meta-Llama-3.1-8B-Instruct').strip()

# REASONING_MODEL: High capability model for deep analysis (e.g., DeepSeek-R1-Distill-Llama-70B or Llama-3.1-70B)
REASONING_MODEL = os.getenv('REASONING_MODEL', 'deepseek-ai/DeepSeek-R1-Distill-Llama-70B').strip()

REASONING_KEYWORDS = ['why', 'risk', 'compare', 'tradeoff', 'explain']


def is_reasoning_prompt(text: str) -> bool:
    """
    Determines if a prompt requires the REASONING_MODEL by scanning
    for analytical trigger words: why, risk, compare, tradeoff, explain.
    """
    lower = text.lower()
    for kw in REASONING_KEYWORDS:
        # Match whole word or keyword pattern
        if re.search(rf'\b{kw}\b', lower):
            return True
    return False


def get_client() -> Optional[OpenAI]:
    """
    Returns an authenticated OpenAI client configured for Nebius Token Factory,
    or None if the API key is absent.
    """
    api_key = os.getenv('NEBIUS_API_KEY', NEBIUS_API_KEY).strip()
    if not api_key:
        return None
    base_url = os.getenv('NEBIUS_BASE_URL', NEBIUS_BASE_URL).strip() or 'https://api.studio.nebius.ai/v1'
    return OpenAI(base_url=base_url, api_key=api_key)


def clean_json_response(raw_text: str) -> str:
    """
    Strips markdown code fencing (```json ... ```) or conversational fluff
    to isolate the raw JSON object string.
    """
    text = raw_text.strip()
    # Check for markdown code blocks
    match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if match:
        return match.group(1).strip()
    # Or find first '{' and last '}'
    first_brace = text.find('{')
    last_brace = text.rfind('}')
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return text[first_brace:last_brace + 1].strip()
    return text


def validate_breakdown_schema(data: Any) -> Dict[str, Any]:
    """
    Validates and standardizes the AI response into strict breakdown schema:
    {
        "title": str,
        "tasks": [{"title": str, "description": str, "column": "todo", "estimate_days": float}],
        "suggestions": [{"kind": "risk"|"note"|"task", "content": str}]
    }
    """
    if not isinstance(data, dict):
        raise ValueError("AI response root must be a dictionary")

    title = str(data.get('title', 'Generated Project Plan')).strip() or 'Generated Project Plan'

    validated_tasks: List[Dict[str, Any]] = []
    for item in data.get('tasks', []):
        if not isinstance(item, dict):
            continue
        t_title = str(item.get('title', '')).strip()
        if not t_title:
            continue
        t_desc = str(item.get('description', '')).strip()
        t_col = str(item.get('column', 'todo')).strip().lower()
        if t_col not in ['todo', 'doing', 'done']:
            t_col = 'todo'
        try:
            t_est = float(item.get('estimate_days', 1.0))
            if t_est <= 0:
                t_est = 1.0
        except (ValueError, TypeError):
            t_est = 1.0

        validated_tasks.append({
            'title': t_title,
            'description': t_desc,
            'column': t_col,
            'estimate_days': round(t_est, 1),
        })

    validated_suggestions: List[Dict[str, Any]] = []
    for item in data.get('suggestions', []):
        if not isinstance(item, dict):
            continue
        s_kind = str(item.get('kind', 'note')).strip().lower()
        if s_kind not in ['task', 'risk', 'note']:
            s_kind = 'note'
        s_content = str(item.get('content', '')).strip()
        if not s_content:
            continue
        validated_suggestions.append({
            'kind': s_kind,
            'content': s_content,
        })

    return {
        'title': title,
        'tasks': validated_tasks,
        'suggestions': validated_suggestions,
    }


def fallback_breakdown(raw_input: str) -> Dict[str, Any]:
    """
    Deterministic rule-based breakdown fallback when NEBIUS_API_KEY is missing or offline.
    Ensures demos never crash without credentials.
    Splits input into bullet points or sentences, extracts a title, and derives tasks,
    risks, and notes.
    """
    clean_input = raw_input.strip()
    if not clean_input:
        clean_input = "New Project Idea"

    # Extract title from first line or sentence
    lines = [line.strip() for line in clean_input.splitlines() if line.strip()]
    first_line = lines[0] if lines else "New Project"
    # Remove leading markdown bullet marks if any
    first_line_clean = re.sub(r'^[-*#\d\.\s]+', '', first_line).strip()
    title = (first_line_clean[:60] + '...') if len(first_line_clean) > 60 else (first_line_clean or "Project MVP Plan")

    # Extract bullet points or tasks
    bullet_items: List[str] = []
    # If the first line was used as the title and is not a bullet item itself, process remaining lines
    first_line_is_bullet = bool(re.match(r'^[-*•\d+\.]', lines[0]))
    content_lines = lines if first_line_is_bullet else lines[1:]

    for line in content_lines:
        cleaned = re.sub(r'^[-*•\d+\.\s]+', '', line).strip()
        if cleaned:
            bullet_items.append(cleaned)

    # If no remaining lines were found and we only had 1 line total, split by sentences
    if not bullet_items and len(lines) == 1:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', first_line_clean) if s.strip()]
        if len(sentences) > 1:
            title = sentences[0][:60]
            bullet_items = sentences[1:]
        else:
            bullet_items = [first_line_clean]

    tasks: List[Dict[str, Any]] = []
    # If we have bullet points, convert them into tasks
    if len(bullet_items) > 1:
        # First item was title if not a bullet list
        task_candidates = bullet_items
        for idx, item in enumerate(task_candidates):
            tasks.append({
                'title': item[:80],
                'description': f"Execution step derived from specification: {item}",
                'column': 'todo',
                'estimate_days': 1.0 + (idx % 3),
            })
    else:
        # Standard boilerplate breakdown for simple 1-line inputs
        tasks = [
            {
                'title': 'Project Scaffolding & Architecture Setup',
                'description': f'Initialize workspace and core boilerplate based on: {clean_input[:100]}',
                'column': 'todo',
                'estimate_days': 1.0,
            },
            {
                'title': 'Core API & Data Models Implementation',
                'description': 'Define schema, database migrations, and REST endpoints.',
                'column': 'todo',
                'estimate_days': 2.0,
            },
            {
                'title': 'Frontend Interface & State Management',
                'description': 'Build responsive views and integrate with backend endpoints.',
                'column': 'todo',
                'estimate_days': 2.0,
            },
            {
                'title': 'Testing, Verification & Deployment',
                'description': 'Write unit tests, configure containerization, and verify user flows.',
                'column': 'todo',
                'estimate_days': 1.5,
            },
        ]

    suggestions = [
        {
            'kind': 'risk',
            'content': 'Tight hackathon timeline: prioritize core MVP flow before adding secondary options.',
        },
        {
            'kind': 'risk',
            'content': 'External API latency and rate limiting: ensure asynchronous handling and fallback defaults.',
        },
        {
            'kind': 'note',
            'content': 'Consider Docker Compose for deterministic multi-service deployment (PostgreSQL, Daphne, Vite).',
        },
        {
            'kind': 'note',
            'content': 'Use WebSockets for real-time board updates to provide interactive collaboration.',
        },
    ]

    return {
        'title': title,
        'tasks': tasks,
        'suggestions': suggestions,
    }


def generate_project_breakdown(raw_input: str) -> Dict[str, Any]:
    """
    Generates a structured project breakdown using FAST_MODEL (Nebius Token Factory)
    with strict JSON parsing and schema validation.
    Falls back to rule-based generation if no API key is provided or on network error.
    """
    client = get_client()
    if not client:
        return fallback_breakdown(raw_input)

    fast_model = os.getenv('FAST_MODEL', FAST_MODEL).strip()

    system_prompt = (
        "You are an expert technical product manager and architect.\n"
        "Analyze the user's project idea and return a STRICT JSON object with this exact structure:\n"
        "{\n"
        '  "title": "Short descriptive project title (max 60 chars)",\n'
        '  "tasks": [\n'
        '    {\n'
        '      "title": "Concise task title",\n'
        '      "description": "Clear technical description and acceptance criteria",\n'
        '      "column": "todo",\n'
        '      "estimate_days": 1.5\n'
        '    }\n'
        "  ],\n"
        '  "suggestions": [\n'
        '    {\n'
        '      "kind": "risk",\n'
        '      "content": "Description of critical technical or operational risk"\n'
        '    },\n'
        '    {\n'
        '      "kind": "note",\n'
        '      "content": "Architectural or performance recommendation"\n'
        '    }\n'
        "  ]\n"
        "}\n"
        "RULES:\n"
        "1. Return ONLY valid JSON. No conversational preamble or trailing text.\n"
        "2. Generate 4 to 7 realistic engineering tasks for an MVP.\n"
        "3. Provide 2 to 4 actionable risks and architectural notes."
    )

    try:
        response = client.chat.completions.create(
            model=fast_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Project idea:\n{raw_input}"},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content or "{}"
        cleaned = clean_json_response(content)
        parsed = json.loads(cleaned)
        return validate_breakdown_schema(parsed)
    except Exception as e:
        # Fall back gracefully so hackathon demos never crash
        print(f"[Pitchly AI] Nebius API request failed or JSON invalid: {e}. Using fallback.")
        return fallback_breakdown(raw_input)


def generate_chat_reply(project: Any, chat_history: List[Dict[str, str]], user_message: str) -> Dict[str, Any]:
    """
    Answers follow-up queries regarding the project.
    Routes to REASONING_MODEL when 'why', 'risk', 'compare', 'tradeoff', or 'explain' is detected.
    Otherwise uses FAST_MODEL.
    """
    requires_reasoning = is_reasoning_prompt(user_message)
    selected_model = os.getenv('REASONING_MODEL', REASONING_MODEL) if requires_reasoning else os.getenv('FAST_MODEL', FAST_MODEL)

    client = get_client()
    if not client:
        # Fallback offline reply
        model_name = "Rule-based Fallback (No NEBIUS_API_KEY set)"
        if requires_reasoning:
            reply = (
                f"### [Reasoning Mode] Architectural Analysis for '{project.title}'\n\n"
                f"Regarding your inquiry ('{user_message}'):\n"
                f"- **Tradeoff Assessment**: In high-velocity MVPs, optimizing for simplicity and developer ergonomic speed "
                f"outweighs distributed complexity. Decouple frontend state via WebSockets while maintaining a relational single source of truth.\n"
                f"- **Risk Factor**: Watch for latency in external AI pipelines; implement asynchronous background queues or optimistic UI updates.\n"
                f"- **Recommendation**: Keep initial scope contained to essential CRUD and WebSocket broadcasting before introducing distributed microservices."
            )
        else:
            reply = (
                f"### [Fast Mode] Planning Copilot for '{project.title}'\n\n"
                f"I reviewed your request: '{user_message}'.\n"
                f"The current project plan has tasks organized across your Kanban columns. "
                f"You can drag tasks between columns, convert pending suggestions to active tasks, "
                f"or request further architectural breakdown anytime."
            )
        return {
            'content': reply,
            'model_used': model_name,
            'reasoning_mode': requires_reasoning,
        }

    # Prepare context
    tasks_summary = "\n".join([f"- [{t.column}] {t.title}: {t.description} ({t.estimate_days}d)" for t in project.tasks.all()])
    suggestions_summary = "\n".join([f"- [{s.kind}] {s.content}" for s in project.suggestions.filter(status='pending')])

    system_prompt = (
        f"You are Pitchly Copilot, an AI technical planning assistant.\n"
        f"You are collaborating with a developer on the project '{project.title}'.\n"
        f"Original raw idea: {project.raw_input}\n\n"
        f"CURRENT BOARD TASKS:\n{tasks_summary or 'No active tasks yet.'}\n\n"
        f"PENDING SUGGESTIONS:\n{suggestions_summary or 'No pending suggestions.'}\n\n"
        f"GUIDELINES:\n"
        f"- Provide direct, concrete, actionable technical guidance.\n"
        f"- If the user asks why, risks, tradeoffs, or comparisons, dive into deep engineering nuances and architectural justifications."
    )

    messages = [{"role": "system", "content": system_prompt}]
    for msg in chat_history[-6:]:  # Keep recent history
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=messages,
            temperature=0.3 if requires_reasoning else 0.5,
        )
        content = response.choices[0].message.content or "No response generated."
        return {
            'content': content,
            'model_used': selected_model,
            'reasoning_mode': requires_reasoning,
        }
    except Exception as e:
        return {
            'content': f"AI service temporarily unavailable: {e}. Check NEBIUS_API_KEY and network connection.",
            'model_used': selected_model,
            'reasoning_mode': requires_reasoning,
        }
