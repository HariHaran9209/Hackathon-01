import React from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import styles from './TaskCard.module.css';

export default function TaskCard({ task, onMoveColumn, onDelete, isOverlay = false }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: `task-${task.id}`,
    data: {
      type: 'task',
      task,
    },
    disabled: isOverlay,
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  const handleSelectColumn = (e) => {
    e.stopPropagation();
    onMoveColumn(task.id, e.target.value);
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    if (confirm(`Delete task "${task.title}"?`)) {
      onDelete(task.id);
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`${styles.card} ${isDragging ? styles.dragging : ''} ${isOverlay ? styles.cardOverlay : ''}`}
      {...attributes}
      {...listeners}
    >
      <div className={styles.headerRow}>
        <div className={styles.title}>{task.title}</div>
        <div className={styles.dragHandle} title="Drag to reorder or move column">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="9" cy="5" r="1" fill="currentColor" />
            <circle cx="9" cy="12" r="1" fill="currentColor" />
            <circle cx="9" cy="19" r="1" fill="currentColor" />
            <circle cx="15" cy="5" r="1" fill="currentColor" />
            <circle cx="15" cy="12" r="1" fill="currentColor" />
            <circle cx="15" cy="19" r="1" fill="currentColor" />
          </svg>
        </div>
      </div>

      {task.description && (
        <div className={styles.description}>{task.description}</div>
      )}

      <div className={styles.footerRow}>
        <span className={styles.estimateBadge}>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          {task.estimate_days}d
        </span>

        <div className={styles.controls}>
          <select
            className={styles.colSelect}
            value={task.column}
            onChange={handleSelectColumn}
            onPointerDown={(e) => e.stopPropagation()}
            title="Move to column"
          >
            <option value="todo">To Do</option>
            <option value="doing">Doing</option>
            <option value="done">Done</option>
          </select>

          <button
            className={styles.deleteButton}
            onClick={handleDelete}
            onPointerDown={(e) => e.stopPropagation()}
            title="Delete task"
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="3 6 5 6 21 6" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
