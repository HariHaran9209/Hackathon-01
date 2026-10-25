import React from 'react';
import { useDroppable } from '@dnd-kit/core';
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable';
import TaskCard from './TaskCard.jsx';
import styles from './Column.module.css';

const COLUMN_CONFIG = {
  todo: { title: 'To Do', indicatorClass: styles.indicatorTodo },
  doing: { title: 'In Progress', indicatorClass: styles.indicatorDoing },
  done: { title: 'Done', indicatorClass: styles.indicatorDone },
};

export default function Column({ columnId, tasks, onMoveColumn, onDeleteTask }) {
  const { setNodeRef, isOver } = useDroppable({
    id: `column-${columnId}`,
    data: {
      type: 'column',
      columnId,
    },
  });

  const config = COLUMN_CONFIG[columnId] || { title: columnId, indicatorClass: '' };
  const taskIds = tasks.map((t) => `task-${t.id}`);
  const totalDays = tasks.reduce((sum, t) => sum + (parseFloat(t.estimate_days) || 0), 0).toFixed(1);

  return (
    <div
      ref={setNodeRef}
      className={`${styles.column} ${isOver ? styles.columnHovered : ''}`}
    >
      <div className={styles.columnHeader}>
        <div className={styles.titleArea}>
          <span className={`${styles.colIndicator} ${config.indicatorClass}`} />
          <span className={styles.columnTitle}>{config.title}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '0.72rem', color: '#8b949e' }}>{totalDays}d</span>
          <span className={styles.countBadge}>{tasks.length}</span>
        </div>
      </div>

      <div className={styles.taskList}>
        <SortableContext items={taskIds} strategy={verticalListSortingStrategy}>
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onMoveColumn={onMoveColumn}
              onDelete={onDeleteTask}
            />
          ))}
        </SortableContext>

        {tasks.length === 0 && (
          <div className={styles.emptyState}>
            Drop tasks here or accept from suggestions
          </div>
        )}
      </div>
    </div>
  );
}
