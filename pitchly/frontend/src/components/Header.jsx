import React from 'react';
import styles from './Header.module.css';

export default function Header({
  project,
  wsStatus,
  onBackToHome,
  onOpenReadme,
  isChatOpen,
  onToggleChat,
  unreadChatCount = 0,
}) {
  const totalDays = project?.tasks
    ? project.tasks.reduce((sum, t) => sum + (parseFloat(t.estimate_days) || 0), 0).toFixed(1)
    : '0.0';

  const pendingCount = project?.suggestions
    ? project.suggestions.filter((s) => s.status === 'pending').length
    : 0;

  return (
    <header className={styles.header}>
      <div className={styles.leftSection}>
        <button className={styles.logoButton} onClick={onBackToHome} title="Go to Pitchly Home">
          <div className={styles.logoIcon}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
            </svg>
          </div>
          <span>Pitchly</span>
        </button>

        {project && (
          <>
            <div className={styles.divider} />
            <button className={styles.backButton} onClick={onBackToHome} title="Return to ideas list">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="19" y1="12" x2="5" y2="12" />
                <polyline points="12 19 5 12 12 5" />
              </svg>
            </button>
            <div className={styles.projectInfo}>
              <h1 className={styles.projectTitle} title={project.title}>
                {project.title}
              </h1>
              <div className={styles.statBadge}>
                <span>Estimate:</span>
                <span className={styles.statValue}>{totalDays}d</span>
              </div>
              {pendingCount > 0 && (
                <div className={styles.statBadge} style={{ borderColor: '#d97706' }}>
                  <span style={{ color: '#fbbf24' }}>{pendingCount} Pending</span>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      <div className={styles.actionsSection}>
        {/* WebSocket Live Status */}
        <div
          className={`${styles.wsBadge} ${
            wsStatus === 'connected' ? styles.wsConnected : styles.wsDisconnected
          }`}
          title={wsStatus === 'connected' ? 'Realtime WebSocket active' : 'Reconnecting to WebSocket...'}
        >
          <span className={styles.pulseDot} />
          <span>{wsStatus === 'connected' ? 'Live' : 'Syncing'}</span>
        </div>

        {project && (
          <>
            <button className={styles.actionButton} onClick={onOpenReadme}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
              </svg>
              <span>Export README</span>
            </button>

            <button
              className={`${styles.actionButton} ${isChatOpen ? styles.chatToggleActive : ''}`}
              onClick={onToggleChat}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              <span>AI Copilot</span>
              {unreadChatCount > 0 && (
                <span style={{ background: '#3b82f6', color: '#fff', padding: '1px 6px', borderRadius: '999px', fontSize: '0.7rem' }}>
                  {unreadChatCount}
                </span>
              )}
            </button>
          </>
        )}
      </div>
    </header>
  );
}
