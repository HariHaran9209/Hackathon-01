import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header.jsx';
import Board from './components/Board.jsx';
import SuggestionPanel from './components/SuggestionPanel.jsx';
import ChatDrawer from './components/ChatDrawer.jsx';
import ReadmeModal from './components/ReadmeModal.jsx';
import { api } from './api.js';
import { createProjectSocket } from './websocket.js';
import styles from './App.module.css';

const SAMPLE_IDEAS = [
  {
    title: 'AI Voice Support Agent',
    text: 'Build an AI voice agent for customer support. It connects incoming phone calls via Twilio Voice API, streams audio to an LLM speech-to-text and reasoning engine, queries internal CRM customer records, and provides automated issue resolution with human escalation.',
  },
  {
    title: 'Realtime Collaborative Whiteboard',
    text: 'Create a high-performance browser collaborative whiteboard. Supports sticky notes, freehand drawing with bezier smoothing, multi-cursor presence, CRDT synchronization, and export to SVG/PDF.',
  },
  {
    title: 'IoT Predictive Maintenance Platform',
    text: 'Edge IoT predictive maintenance gateway for manufacturing facilities. Gathers vibration and temperature telemetry over MQTT, analyzes anomalies using lightweight models, alerts operators on threshold breaches, and schedules work orders.',
  },
];

export default function App() {
  const [currentProject, setCurrentProject] = useState(null);
  const [recentProjects, setRecentProjects] = useState([]);
  const [ideaInput, setIdeaInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isReadmeOpen, setIsReadmeOpen] = useState(false);
  const [isSendingChat, setIsSendingChat] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  const socketRef = useRef(null);

  // Load recent projects on initial mount
  useEffect(() => {
    loadRecentProjects();
  }, []);

  // Manage WebSocket connection when current project changes
  useEffect(() => {
    if (!currentProject?.id) {
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
      setWsStatus('disconnected');
      return;
    }

    const socket = createProjectSocket(
      currentProject.id,
      handleSocketMessage,
      (status) => setWsStatus(status)
    );
    socketRef.current = socket;

    return () => {
      socket.close();
    };
  }, [currentProject?.id]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(''), 3000);
  };

  const loadRecentProjects = async () => {
    try {
      const data = await api.getProjects();
      setRecentProjects(data);
    } catch (e) {
      console.warn('Failed to fetch recent projects:', e);
    }
  };

  const handleSocketMessage = (payload) => {
    if (!payload || !payload.event) return;

    const { event, data } = payload;

    setCurrentProject((prev) => {
      if (!prev) return prev;

      switch (event) {
        case 'task_updated': {
          const updatedTasks = prev.tasks.map((t) =>
            t.id === data.id ? { ...t, ...data } : t
          );
          return { ...prev, tasks: updatedTasks };
        }
        case 'task_created': {
          const exists = prev.tasks.some((t) => t.id === data.id);
          if (exists) return prev;
          return { ...prev, tasks: [...prev.tasks, data] };
        }
        case 'task_deleted': {
          return {
            ...prev,
            tasks: prev.tasks.filter((t) => t.id !== data.id),
          };
        }
        case 'suggestion_accepted': {
          const updatedSuggestions = prev.suggestions.map((s) =>
            s.id === data.suggestion?.id ? { ...s, status: 'accepted' } : s
          );
          let newTasks = prev.tasks;
          if (data.task && !prev.tasks.some((t) => t.id === data.task.id)) {
            newTasks = [...prev.tasks, data.task];
          }
          return { ...prev, suggestions: updatedSuggestions, tasks: newTasks };
        }
        case 'suggestion_rejected': {
          const updatedSuggestions = prev.suggestions.map((s) =>
            s.id === data.suggestion?.id ? { ...s, status: 'rejected' } : s
          );
          return { ...prev, suggestions: updatedSuggestions };
        }
        case 'chat_message_created': {
          const msgs = [...(prev.messages || [])];
          if (data.user_message && !msgs.some((m) => m.id === data.user_message.id)) {
            msgs.push(data.user_message);
          }
          if (data.assistant_message && !msgs.some((m) => m.id === data.assistant_message.id)) {
            msgs.push({
              ...data.assistant_message,
              reasoning_mode: data.reasoning_mode,
            });
          }
          return { ...prev, messages: msgs };
        }
        default:
          return prev;
      }
    });
  };

  const handleCreateProject = async (e) => {
    if (e) e.preventDefault();
    if (!ideaInput.trim() || isGenerating) return;

    setIsGenerating(true);
    try {
      const newProj = await api.createProject(ideaInput.trim());
      setCurrentProject(newProj);
      setIdeaInput('');
      loadRecentProjects();
      showToast('Project breakdown generated successfully!');
    } catch (err) {
      alert(`Error generating project: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectRecent = async (proj) => {
    try {
      const fullProj = await api.getProject(proj.id);
      setCurrentProject(fullProj);
    } catch (e) {
      alert(`Could not load project: ${e.message}`);
    }
  };

  const handleUpdateTask = async (taskId, updates) => {
    // Optimistic UI update
    setCurrentProject((prev) => {
      if (!prev) return prev;
      const newTasks = prev.tasks.map((t) =>
        t.id === taskId ? { ...t, ...updates } : t
      );
      return { ...prev, tasks: newTasks };
    });

    try {
      await api.updateTask(taskId, updates);
    } catch (err) {
      showToast(`Failed to update task: ${err.message}`);
      // Revert on error
      if (currentProject?.id) {
        const fresh = await api.getProject(currentProject.id);
        setCurrentProject(fresh);
      }
    }
  };

  const handleDeleteTask = async (taskId) => {
    setCurrentProject((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        tasks: prev.tasks.filter((t) => t.id !== taskId),
      };
    });

    try {
      await api.deleteTask(taskId);
      showToast('Task removed.');
    } catch (err) {
      showToast(`Failed to delete task: ${err.message}`);
    }
  };

  const handleAcceptSuggestion = async (id) => {
    try {
      const res = await api.acceptSuggestion(id);
      setCurrentProject((prev) => {
        if (!prev) return prev;
        const newSuggestions = prev.suggestions.map((s) =>
          s.id === id ? { ...s, status: 'accepted' } : s
        );
        let newTasks = prev.tasks;
        if (res.task && !prev.tasks.some((t) => t.id === res.task.id)) {
          newTasks = [...prev.tasks, res.task];
        }
        return { ...prev, suggestions: newSuggestions, tasks: newTasks };
      });
      showToast('Suggestion accepted to board!');
    } catch (err) {
      showToast(`Accept failed: ${err.message}`);
    }
  };

  const handleRejectSuggestion = async (id) => {
    try {
      await api.rejectSuggestion(id);
      setCurrentProject((prev) => {
        if (!prev) return prev;
        const newSuggestions = prev.suggestions.map((s) =>
          s.id === id ? { ...s, status: 'rejected' } : s
        );
        return { ...prev, suggestions: newSuggestions };
      });
      showToast('Suggestion dismissed.');
    } catch (err) {
      showToast(`Reject failed: ${err.message}`);
    }
  };

  const handleSendMessage = async (text) => {
    if (!currentProject?.id || isSendingChat) return;

    // Optimistically push user message
    const tempUserMsg = {
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };
    setCurrentProject((prev) => ({
      ...prev,
      messages: [...(prev.messages || []), tempUserMsg],
    }));

    setIsSendingChat(true);
    try {
      const res = await api.sendChatMessage(currentProject.id, text);
      setCurrentProject((prev) => {
        const msgs = [...(prev.messages || [])];
        msgs.push({
          ...res.assistant_message,
          reasoning_mode: res.reasoning_mode,
        });
        return { ...prev, messages: msgs };
      });
    } catch (err) {
      showToast(`Chat error: ${err.message}`);
    } finally {
      setIsSendingChat(false);
    }
  };

  return (
    <div className={styles.appContainer}>
      <Header
        project={currentProject}
        wsStatus={wsStatus}
        onBackToHome={() => setCurrentProject(null)}
        onOpenReadme={() => setIsReadmeOpen(true)}
        isChatOpen={isChatOpen}
        onToggleChat={() => setIsChatOpen(!isChatOpen)}
      />

      {toastMessage && <div className={styles.toast}>{toastMessage}</div>}

      {!currentProject ? (
        // ----------------- HOME VIEW -----------------
        <main className={styles.homeContainer}>
          <div className={styles.heroSection}>
            <div className={styles.brandBadge}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              <span>NVIDIA & Nebius Token Factory Copilot</span>
            </div>
            <h1 className={styles.heroTitle}>Turn rough ideas into actionable roadmaps.</h1>
            <p className={styles.heroSubtitle}>
              Paste raw thoughts, product notes, or hackathon concepts. Pitchly’s hybrid AI engine
              splits decomposition and deep reasoning into an interactive Kanban board.
            </p>
          </div>

          <form className={styles.inputCard} onSubmit={handleCreateProject}>
            <textarea
              className={styles.ideaTextarea}
              placeholder="Describe your project idea in detail, paste rough notes, or outline features..."
              value={ideaInput}
              onChange={(e) => setIdeaInput(e.target.value)}
              disabled={isGenerating}
            />

            <div className={styles.samplePromptsContainer}>
              <span className={styles.sampleLabel}>Or try a sample idea:</span>
              <div className={styles.sampleChips}>
                {SAMPLE_IDEAS.map((sample, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className={styles.chipButton}
                    onClick={() => setIdeaInput(sample.text)}
                    disabled={isGenerating}
                  >
                    💡 {sample.title}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              className={styles.submitButton}
              disabled={!ideaInput.trim() || isGenerating}
            >
              {isGenerating ? (
                <>
                  <div className={styles.spinner} />
                  <span>Synthesizing Plan with Nebius AI...</span>
                </>
              ) : (
                <>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                  </svg>
                  <span>Deconstruct into Plan</span>
                </>
              )}
            </button>
          </form>

          {recentProjects.length > 0 && (
            <div className={styles.recentSection}>
              <div className={styles.recentTitle}>Recent Projects</div>
              <div className={styles.recentGrid}>
                {recentProjects.map((p) => (
                  <div
                    key={p.id}
                    className={styles.recentCard}
                    onClick={() => handleSelectRecent(p)}
                    role="button"
                    tabIndex={0}
                  >
                    <div className={styles.recentCardTitle}>{p.title}</div>
                    <div className={styles.recentCardMeta}>
                      <span>{p.tasks?.length || 0} tasks</span>
                      <span>{p.total_days || 0}d est.</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </main>
      ) : (
        // ----------------- PROJECT WORKSPACE -----------------
        <main className={styles.projectWorkspace}>
          <div className={styles.boardLayout}>
            <div className={styles.kanbanArea}>
              <Board
                tasks={currentProject.tasks || []}
                onUpdateTask={handleUpdateTask}
                onDeleteTask={handleDeleteTask}
              />
            </div>

            <div className={styles.suggestionsSidebar}>
              <SuggestionPanel
                suggestions={currentProject.suggestions || []}
                onAccept={handleAcceptSuggestion}
                onReject={handleRejectSuggestion}
              />
            </div>
          </div>

          <ChatDrawer
            isOpen={isChatOpen}
            onClose={() => setIsChatOpen(false)}
            messages={currentProject.messages || []}
            onSendMessage={handleSendMessage}
            isSending={isSendingChat}
          />

          <ReadmeModal
            isOpen={isReadmeOpen}
            onClose={() => setIsReadmeOpen(false)}
            projectId={currentProject.id}
            api={api}
          />
        </main>
      )}
    </div>
  );
}
