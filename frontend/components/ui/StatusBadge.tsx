import React from 'react';
import { TaskStatus } from '@/lib/types';
import { Circle, Clock, CheckCircle2 } from 'lucide-react';

interface StatusBadgeProps {
  status: TaskStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const label = status === 'IN_PROGRESS' ? 'In Progress' : status === 'TODO' ? 'To Do' : 'Completed';
  const badgeClass = `badge badge-${status.toLowerCase()}`;

  return (
    <span className={badgeClass}>
      {status === 'TODO' && <Circle size={10} />}
      {status === 'IN_PROGRESS' && <Clock size={10} />}
      {status === 'COMPLETED' && <CheckCircle2 size={10} />}
      <span>{label}</span>
    </span>
  );
}
