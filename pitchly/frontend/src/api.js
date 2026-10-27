/**
 * Pitchly REST API Client
 */

function resolveApiBase() {
  const envUrl = import.meta.env.VITE_API_URL;
  if (!envUrl) return '/api';
  let formatted = envUrl.trim();
  if (!/^https?:\/\//i.test(formatted)) {
    formatted = formatted.startsWith('localhost') || formatted.startsWith('127.0.0.1')
      ? `http://${formatted}`
      : `https://${formatted}`;
  }
  return `${formatted.replace(/\/+$/, '')}/api`;
}

const API_BASE = resolveApiBase();

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  const response = await fetch(url, config);
  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    try {
      const data = await response.json();
      errorDetail = data.error || data.detail || JSON.stringify(data);
    } catch (_) {}
    throw new Error(errorDetail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  // Projects
  getProjects() {
    return request('/projects/');
  },
  getProject(id) {
    return request(`/projects/${id}/`);
  },
  createProject(rawInput, title = '') {
    return request('/projects/', {
      method: 'POST',
      body: JSON.stringify({ raw_input: rawInput, title }),
    });
  },

  // Tasks
  updateTask(id, data) {
    return request(`/tasks/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },
  deleteTask(id) {
    return request(`/tasks/${id}/`, {
      method: 'DELETE',
    });
  },
  createTask(projectId, taskData) {
    return request(`/projects/${projectId}/tasks/`, {
      method: 'POST',
      body: JSON.stringify(taskData),
    });
  },

  // Suggestions
  acceptSuggestion(id) {
    return request(`/suggestions/${id}/accept/`, {
      method: 'POST',
    });
  },
  rejectSuggestion(id) {
    return request(`/suggestions/${id}/reject/`, {
      method: 'POST',
    });
  },

  // AI Chat & Readme
  sendChatMessage(projectId, content) {
    return request(`/projects/${projectId}/chat/`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  },
  getProjectReadme(projectId) {
    return request(`/projects/${projectId}/readme/`);
  },
};
