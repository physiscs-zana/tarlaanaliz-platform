/* BOUND: TARLAANALIZ_SSOT_v1_2_0.txt – canonical rules are referenced, not duplicated. */
/* KR-015-5: Ciftci ekraninda tum sezon icin planlanan tarama gunleri takvim gorunumunde gosterilir. */

'use client';

import { useMemo } from 'react';

export interface ScheduledMission {
  readonly date: string; // ISO date (YYYY-MM-DD)
  readonly status: 'planned' | 'completed' | 'cancelled' | 'rescheduled';
  readonly missionId?: string;
}

interface MissionScheduleCalendarProps {
  readonly startDate: string;
  readonly endDate: string;
  readonly missions: readonly ScheduledMission[];
}

const STATUS_COLORS: Record<ScheduledMission['status'], string> = {
  planned: 'bg-blue-100 text-blue-800 border-blue-300',
  completed: 'bg-green-100 text-green-800 border-green-300',
  cancelled: 'bg-red-100 text-red-800 border-red-300',
  rescheduled: 'bg-amber-100 text-amber-800 border-amber-300',
};

const STATUS_LABELS: Record<ScheduledMission['status'], string> = {
  planned: 'Planlanan',
  completed: 'Tamamlanan',
  cancelled: 'İptal',
  rescheduled: 'Ertelenen',
};

export function MissionScheduleCalendar({ startDate, endDate, missions }: MissionScheduleCalendarProps) {
  const missionsByDate = useMemo(() => {
    const map = new Map<string, ScheduledMission>();
    for (const m of missions) {
      map.set(m.date, m);
    }
    return map;
  }, [missions]);

  const calendarDays = useMemo(() => {
    const days: string[] = [];
    const start = new Date(startDate);
    const end = new Date(endDate);
    const cursor = new Date(start);
    while (cursor <= end) {
      days.push(cursor.toISOString().slice(0, 10));
      cursor.setDate(cursor.getDate() + 1);
    }
    return days;
  }, [startDate, endDate]);

  return (
    <div className="space-y-3">
      <h3 className="font-medium">Sezon Takvimi</h3>
      <div className="flex flex-wrap gap-1 text-xs">
        {Object.entries(STATUS_LABELS).map(([key, label]) => (
          <span key={key} className={`rounded border px-2 py-0.5 ${STATUS_COLORS[key as ScheduledMission['status']]}`}>
            {label}
          </span>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1 text-xs">
        {['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'].map((d) => (
          <div key={d} className="text-center font-medium text-slate-500">{d}</div>
        ))}
        {calendarDays.map((day) => {
          const mission = missionsByDate.get(day);
          const dayNum = new Date(day).getDate();
          const colorClass = mission ? STATUS_COLORS[mission.status] : '';
          return (
            <div
              key={day}
              className={`rounded border p-1 text-center ${mission ? colorClass : 'border-slate-100 text-slate-400'}`}
              title={mission ? `${STATUS_LABELS[mission.status]}${mission.missionId ? ` (${mission.missionId})` : ''}` : day}
            >
              {dayNum}
            </div>
          );
        })}
      </div>
    </div>
  );
}
