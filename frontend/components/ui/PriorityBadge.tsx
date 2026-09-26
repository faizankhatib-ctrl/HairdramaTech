import React from 'react';
import { TaskPriority } from '@/lib/types';
import { AlertCircle, AlertTriangle, ArrowUp, ArrowDown } from 'lucide-react';

interface PriorityBadgeProps {
  priority: TaskPriority;
}

export function PriorityBadge({ priority }: PriorityBadgeProps) {
  const badgeClass = `badge badge-${priority.toLowerCase()}`;

  return (
    <span className={badgeClass}>
      {priority === 'URGENT' && <AlertCircle size={10} />}
      {priority === 'HIGH' && <AlertTriangle size={10} />}
      {priority === 'MEDIUM' && <ArrowUp size={10} />}
      {priority === 'LOW' && <ArrowDown size={10} />}
      <span>{priority}</span>
    </span>
  );
}
