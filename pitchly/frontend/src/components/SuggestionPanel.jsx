import React, { useState } from 'react';
import styles from './SuggestionPanel.module.css';

export default function SuggestionPanel({
  suggestions = [],
  onAccept,
  onReject,
}) {
  const [activeTab, setActiveTab] = useState('all');

  const filteredSuggestions = suggestions.filter((s) => {
    if (activeTab === 'all') return true;
    if (activeTab === 'pending') return s.status === 'pending';
    return s.kind === activeTab;
  });

  const pendingCount = suggestions.filter((s) => s.status === 'pending').length;
  const tasksCount = suggestions.filter((s) => s.kind === 'task').length;
  const risksCount = suggestions.filter((s) => s.kind === 'risk').length;
  const notesCount = suggestions.filter((s) => s.kind === 'note').length;

  const renderBadge = (kind) => {
    switch (kind) {
      case 'task':
        return <span className={`${styles.kindBadge} ${styles.kindTask}`}>Task Candidate</span>;
      case 'risk':
        return <span className={`${styles.kindBadge} ${styles.kindRisk}`}>Risk</span>;
      case 'note':
        return <span className={`${styles.kindBadge} ${styles.kindNote}`}>Architecture Note</span>;
      default:
        return <span className={styles.kindBadge}>{kind}</span>;
    }
  };

  const getCardStatusClass = (status) => {
    if (status === 'accepted') return styles.cardAccepted;
    if (status === 'rejected') return styles.cardRejected;
    return '';
  };

  return (
    <aside className={styles.container}>
      <div className={styles.header}>
        <div className={styles.titleArea}>
          <span className={styles.title}>AI Suggestions</span>
          {pendingCount > 0 && (
            <span className={styles.badge} style={{ background: '#d97706', color: '#fff' }}>
              {pendingCount} new
            </span>
          )}
        </div>
      </div>

      <div className={styles.tabsRow}>
        <button
          className={`${styles.tabButton} ${activeTab === 'all' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('all')}
        >
          All <span className={styles.badge}>{suggestions.length}</span>
        </button>
        <button
          className={`${styles.tabButton} ${activeTab === 'task' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('task')}
        >
          Tasks <span className={styles.badge}>{tasksCount}</span>
        </button>
        <button
          className={`${styles.tabButton} ${activeTab === 'risk' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('risk')}
        >
          Risks <span className={styles.badge}>{risksCount}</span>
        </button>
        <button
          className={`${styles.tabButton} ${activeTab === 'note' ? styles.activeTab : ''}`}
          onClick={() => setActiveTab('note')}
        >
          Notes <span className={styles.badge}>{notesCount}</span>
        </button>
      </div>

      <div className={styles.cardList}>
        {filteredSuggestions.map((sugg) => {
          const isPending = sugg.status === 'pending';
          const payload = sugg.payload || {};

          return (
            <div
              key={sugg.id}
              className={`${styles.card} ${getCardStatusClass(sugg.status)}`}
            >
              <div className={styles.cardTopRow}>
                {renderBadge(sugg.kind)}
                <span className={styles.statusText}>{sugg.status}</span>
              </div>

              {sugg.kind === 'task' ? (
                <>
                  <div className={styles.content} style={{ fontWeight: 600 }}>
                    {payload.title || sugg.content}
                  </div>
                  {payload.description && (
                    <div style={{ fontSize: '0.8rem', color: '#8b949e' }}>
                      {payload.description}
                    </div>
                  )}
                  <div className={styles.taskDetail}>
                    <span>Target: <strong>{payload.column || 'todo'}</strong></span>
                    <span>Estimate: <strong>{payload.estimate_days || 1.0}d</strong></span>
                  </div>
                </>
              ) : (
                <div className={styles.content}>{sugg.content}</div>
              )}

              {isPending && (
                <div className={styles.actionsRow}>
                  <button
                    className={styles.acceptButton}
                    onClick={() => onAccept(sugg.id)}
                    title="Accept and add to board"
                  >
                    ✓ {sugg.kind === 'task' ? 'Accept to Board' : 'Accept'}
                  </button>
                  <button
                    className={styles.rejectButton}
                    onClick={() => onReject(sugg.id)}
                    title="Dismiss this suggestion"
                  >
                    ✕ Dismiss
                  </button>
                </div>
              )}
            </div>
          );
        })}

        {filteredSuggestions.length === 0 && (
          <div className={styles.emptyState}>No suggestions in this category.</div>
        )}
      </div>
    </aside>
  );
}
