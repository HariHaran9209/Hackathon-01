import React, { useState } from 'react';
import {
  DndContext,
  closestCorners,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
} from '@dnd-kit/core';
import Column from './Column.jsx';
import TaskCard from './TaskCard.jsx';
import styles from './Board.module.css';

const COLUMNS = ['todo', 'doing', 'done'];

export default function Board({ tasks = [], onUpdateTask, onDeleteTask }) {
  const [activeTask, setActiveTask] = useState(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 5,
      },
    })
  );

  const tasksByColumn = {
    todo: tasks.filter((t) => t.column === 'todo'),
    doing: tasks.filter((t) => t.column === 'doing'),
    done: tasks.filter((t) => t.column === 'done'),
  };

  const handleDragStart = (event) => {
    const { active } = event;
    const taskIdStr = String(active.id).replace('task-', '');
    const found = tasks.find((t) => String(t.id) === taskIdStr);
    if (found) {
      setActiveTask(found);
    }
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    setActiveTask(null);

    if (!over) return;

    const activeTaskId = parseInt(String(active.id).replace('task-', ''), 10);
    const activeTaskObj = tasks.find((t) => t.id === activeTaskId);
    if (!activeTaskObj) return;

    let targetColumn = activeTaskObj.column;

    // Check if dropped onto a column
    if (String(over.id).startsWith('column-')) {
      targetColumn = String(over.id).replace('column-', '');
    } else if (String(over.id).startsWith('task-')) {
      const overTaskId = parseInt(String(over.id).replace('task-', ''), 10);
      const overTaskObj = tasks.find((t) => t.id === overTaskId);
      if (overTaskObj) {
        targetColumn = overTaskObj.column;
      }
    }

    if (targetColumn && COLUMNS.includes(targetColumn)) {
      if (targetColumn !== activeTaskObj.column) {
        onUpdateTask(activeTaskId, { column: targetColumn });
      }
    }
  };

  const handleManualMove = (taskId, newColumn) => {
    onUpdateTask(taskId, { column: newColumn });
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className={styles.boardContainer}>
        {COLUMNS.map((colId) => (
          <Column
            key={colId}
            columnId={colId}
            tasks={tasksByColumn[colId] || []}
            onMoveColumn={handleManualMove}
            onDeleteTask={onDeleteTask}
          />
        ))}
      </div>

      <DragOverlay>
        {activeTask ? (
          <TaskCard
            task={activeTask}
            onMoveColumn={() => {}}
            onDelete={() => {}}
            isOverlay
          />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
