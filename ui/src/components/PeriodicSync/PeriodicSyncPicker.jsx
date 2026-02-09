/***
 * Copyright (2026) Hewlett Packard Enterprise Development LP
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * You may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 ***/

import React, { useMemo, useState } from 'react';
import { buildTimeZoneOptions, getLocalTimeZone } from '../../utils/timezones';

function toLocalInputValue(date) {
  const pad = (n) => String(n).padStart(2, '0');
  const yyyy = date.getFullYear();
  const mm = pad(date.getMonth() + 1);
  const dd = pad(date.getDate());
  const hh = pad(date.getHours());
  const mi = pad(date.getMinutes());
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
}

function formatInTZ(date, timeZone) {
  try {
    return new Intl.DateTimeFormat('en-IN', {
      timeZone,
      year: 'numeric', month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit', hour12: true,
    }).format(date);
  } catch {
    return date.toUTCString();
  }
}

// Timezones will be populated dynamically from browser support
function addMinutes(date, minutes) {
  return new Date(date.getTime() + minutes * 60000);
}

export default function PeriodicSyncPicker({ serverId, serverName, onSchedule, mode = 'periodic', open, onClose, inline = false }) {
  const tzOptions = useMemo(() => buildTimeZoneOptions(), []);
  const defaultTZ = useMemo(() => getLocalTimeZone(), []);

  const [timezone, setTimezone] = useState(defaultTZ);
  const [startLocal, setStartLocal] = useState(() => {
    const d = new Date(Date.now() + 5 * 60 * 1000);
    return toLocalInputValue(d);
  });
  const [submitting, setSubmitting] = useState(false);

  // Periodic specifics
  const [recurrenceMode, setRecurrenceMode] = useState('interval'); // interval | daily | weekly
  const [intervalUnit, setIntervalUnit] = useState('hours'); // minutes | hours
  const [intervalValue, setIntervalValue] = useState(6);
  const [dailyTime, setDailyTime] = useState('09:00'); // Time for daily sync
  const [weeklyDay, setWeeklyDay] = useState('monday'); // Day for weekly sync
  const [weeklyTime, setWeeklyTime] = useState('09:00'); // Time for weekly sync

  const startDate = useMemo(() => new Date(startLocal), [startLocal]);

  const preview = useMemo(() => {
    if (mode === 'one-time') {
      return [new Date(startDate)];
    }
    if (recurrenceMode === 'interval') {
      const mins = intervalUnit === 'hours' ? intervalValue * 60 : intervalValue;
      const out = [];
      let cursor = new Date(startDate);
      // First sync starts immediately at the start time
      out.push(new Date(cursor));
      for (let i = 0; i < 4; i++) {
        cursor = addMinutes(cursor, mins);
        out.push(new Date(cursor));
      }
      return out;
    }
    if (recurrenceMode === 'daily') {
      const out = [];
      let cursor = new Date(startDate);
      // First sync starts immediately at the start time
      out.push(new Date(cursor));
      for (let i = 0; i < 4; i++) {
        cursor = new Date(cursor.getTime() + 24 * 60 * 60 * 1000);
        out.push(new Date(cursor));
      }
      return out;
    }
    if (recurrenceMode === 'weekly') {
      const out = [];

      // Map weekday names to numbers (0 = Sunday, 1 = Monday, ..., 6 = Saturday)
      const dayMap = {
        sunday: 0,
        monday: 1,
        tuesday: 2,
        wednesday: 3,
        thursday: 4,
        friday: 5,
        saturday: 6,
      };

      const targetDay = dayMap[weeklyDay.toLowerCase()];
      const [hours, minutes] = weeklyTime.split(':').map(Number);

      // Start from current date/time as reference (not startDate)
      const now = new Date();
      let cursor = new Date(now);
      cursor.setHours(hours, minutes, 0, 0);

      const currentDay = cursor.getDay();
      let daysUntilTarget = targetDay - currentDay;

      // If target day is in the past this week, move to next week
      if (daysUntilTarget < 0) {
        daysUntilTarget += 7;
      }
      // If it's the same day but the time has passed, move to next week
      else if (daysUntilTarget === 0 && cursor <= now) {
        daysUntilTarget = 7;
      }

      cursor.setDate(cursor.getDate() + daysUntilTarget);

      // Add first occurrence and next 4 weekly occurrences
      for (let i = 0; i < 5; i++) {
        out.push(new Date(cursor));
        cursor = new Date(cursor.getTime() + 7 * 24 * 60 * 60 * 1000);
      }

      return out;
    }
    return [];
  }, [mode, startDate, recurrenceMode, intervalUnit, intervalValue, dailyTime, weeklyDay, weeklyTime]);

  const isPastTime = useMemo(() => {
    const selectedDateTime = new Date(startLocal);
    const now = new Date();
    return selectedDateTime < now;
  }, [startLocal]);

  const canSubmit = useMemo(() => {
    if (!serverId || !serverName) return false;
    if (!timezone) return false;
    if (!startLocal) return false;
    if (isPastTime) return false; // Prevent past times
    if (mode === 'periodic') {
      if (recurrenceMode === 'interval') return intervalValue > 0;
      if (recurrenceMode === 'daily') return dailyTime !== '';
      if (recurrenceMode === 'weekly') return weeklyDay !== '' && weeklyTime !== '';
    }
    return true;
  }, [serverId, serverName, timezone, startLocal, isPastTime, mode, recurrenceMode, intervalValue, dailyTime, weeklyDay, weeklyTime]);

  const handleSubmit = async () => {
    if (!canSubmit || submitting) return;
    setSubmitting(true);

    try {
      const one_time = mode === 'one-time';
      // Build schedule data based on recurrence mode
      const scheduleData = {
        serverId,
        serverName,
        startTimeLocalIso: startLocal,
        timezone,
        one_time,
      };

      // Only add recurrence mode data for periodic syncs
      if (!one_time) {
        scheduleData.recurrenceMode = recurrenceMode;

        // Add mode-specific data
        if (recurrenceMode === 'interval') {
          scheduleData.intervalUnit = intervalUnit;
          scheduleData.intervalValue = intervalValue;
        } else if (recurrenceMode === 'daily') {
          scheduleData.dailyTime = dailyTime;
        } else if (recurrenceMode === 'weekly') {
          scheduleData.weeklyDay = weeklyDay;
          scheduleData.weeklyTime = weeklyTime;
        }
      }

      console.log('Submitting schedule data:', scheduleData); // Debug log
      await onSchedule(scheduleData);
      if (onClose && !inline) {
        onClose();
      }
    } finally {
      setSubmitting(false);
    }
  };

  // Inline rendering without modal
  if (inline) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Server</label>
            <div className="text-sm text-gray-900">{serverName} (ID: {serverId})</div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            >
              {!tzOptions.find(o => o.value === timezone) && (
                <option value={timezone}>{timezone}</option>
              )}
              {tzOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date & Time</label>
            <input
              type="datetime-local"
              className={`w-full border rounded px-3 py-2 text-sm ${isPastTime ? 'border-red-500' : ''}`}
              value={startLocal}
              onChange={(e) => setStartLocal(e.target.value)}
            />
            {isPastTime && (
              <p className="text-red-600 text-xs mt-1">
                ⚠ Cannot select a past date and time. Please choose a future time.
              </p>
            )}
          </div>
          {mode === 'periodic' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Recurrence Mode</label>
              <select
                className="w-full border rounded px-3 py-2 text-sm"
                value={recurrenceMode}
                onChange={(e) => setRecurrenceMode(e.target.value)}
              >
                <option value="interval">Every N minutes/hours</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>
          )}
        </div>

        {mode === 'periodic' && recurrenceMode === 'interval' && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Interval Value</label>
              <input
                type="number"
                min={1}
                className="w-full border rounded px-3 py-2 text-sm"
                value={intervalValue}
                onChange={(e) => setIntervalValue(parseInt(e.target.value || '0', 10))}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
              <select
                className="w-full border rounded px-3 py-2 text-sm"
                value={intervalUnit}
                onChange={(e) => setIntervalUnit(e.target.value)}
              >
                <option value="minutes">Minutes</option>
                <option value="hours">Hours</option>
              </select>
            </div>
          </div>
        )}

        {mode === 'periodic' && recurrenceMode === 'daily' && (
          <div className="text-sm text-gray-600 italic">
            Daily sync will run at the time specified in "Start Date & Time" above.
          </div>
        )}

        {mode === 'periodic' && recurrenceMode === 'weekly' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week</label>
            <select
              className="w-full border rounded px-3 py-2 text-sm"
              value={weeklyDay}
              onChange={(e) => setWeeklyDay(e.target.value)}
            >
              <option value="monday">Monday</option>
              <option value="tuesday">Tuesday</option>
              <option value="wednesday">Wednesday</option>
              <option value="thursday">Thursday</option>
              <option value="friday">Friday</option>
              <option value="saturday">Saturday</option>
              <option value="sunday">Sunday</option>
            </select>
            <p className="text-sm text-gray-600 italic">
              Weekly sync will run at the time specified in "Start Date & Time" above.
            </p>
          </div>
        )}


        <div>
          <div className="text-sm font-medium text-gray-700 mb-2">Preview next runs (in {timezone})</div>
          <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1 bg-gray-50 p-3 rounded border border-gray-200">
            {preview.length === 0 && (
              <li>No upcoming runs (adjust settings)</li>
            )}
            {preview.map((d, idx) => (
              <li key={idx}>{formatInTZ(d, timezone)}</li>
            ))}
          </ul>
        </div>

        <div className="flex justify-end">
          <button
            type="button"
            className={`px-6 py-2 rounded text-white font-semibold ${canSubmit && !submitting ? 'bg-teal-600 hover:bg-teal-700' : 'bg-gray-400 cursor-not-allowed'}`}
            disabled={!canSubmit || submitting}
            onClick={handleSubmit}
          >
            {submitting ? 'Creating...' : (mode === 'periodic' ? 'Create Periodic Schedule' : 'Create One-time Schedule')}
          </button>
        </div>
      </div>
    );
  }

  // Modal rendering (original behavior)
  return (
    <div>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl">
            <div className="px-4 py-3 border-b">
              <h3 className="text-lg font-semibold text-teal-700">
                {mode === 'periodic' ? 'Configure Periodic Sync' : 'Configure One-time Sync'}
              </h3>
            </div>

            <div className="p-4 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Server</label>
                  <div className="text-sm text-gray-900">{serverName} (ID: {serverId})</div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Timezone</label>
                  <select
                    className="w-full border rounded px-3 py-2 text-sm"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                  >
                    {/* Ensure current selection is present even if not in options */}
                    {!tzOptions.find(o => o.value === timezone) && (
                      <option value={timezone}>{timezone}</option>
                    )}
                    {tzOptions.map((opt) => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Start Date & Time</label>
                  <input
                    type="datetime-local"
                    className={`w-full border rounded px-3 py-2 text-sm ${isPastTime ? 'border-red-500' : ''}`}
                    value={startLocal}
                    onChange={(e) => setStartLocal(e.target.value)}
                  />
                  {isPastTime && (
                    <p className="text-red-600 text-xs mt-1">
                      ⚠ Cannot select a past date and time. Please choose a future time.
                    </p>
                  )}
                </div>
                {mode === 'periodic' && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Recurrence Mode</label>
                    <select
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={recurrenceMode}
                      onChange={(e) => setRecurrenceMode(e.target.value)}
                    >
                      <option value="interval">Every N minutes/hours</option>
                      <option value="daily">Daily</option>
                      <option value="weekly">Weekly</option>
                    </select>
                  </div>
                )}
              </div>

              {mode === 'periodic' && recurrenceMode === 'interval' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Interval Value</label>
                    <input
                      type="number"
                      min={1}
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={intervalValue}
                      onChange={(e) => setIntervalValue(parseInt(e.target.value || '0', 10))}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Unit</label>
                    <select
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={intervalUnit}
                      onChange={(e) => setIntervalUnit(e.target.value)}
                    >
                      <option value="minutes">Minutes</option>
                      <option value="hours">Hours</option>
                    </select>
                  </div>
                </div>
              )}

              {mode === 'periodic' && recurrenceMode === 'daily' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Time of Day</label>
                    <input
                      type="time"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={dailyTime}
                      onChange={(e) => setDailyTime(e.target.value)}
                    />
                  </div>
                </div>
              )}

              {mode === 'periodic' && recurrenceMode === 'weekly' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Day of Week</label>
                    <select
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={weeklyDay}
                      onChange={(e) => setWeeklyDay(e.target.value)}
                    >
                      <option value="monday">Monday</option>
                      <option value="tuesday">Tuesday</option>
                      <option value="wednesday">Wednesday</option>
                      <option value="thursday">Thursday</option>
                      <option value="friday">Friday</option>
                      <option value="saturday">Saturday</option>
                      <option value="sunday">Sunday</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Time of Day</label>
                    <input
                      type="time"
                      className="w-full border rounded px-3 py-2 text-sm"
                      value={weeklyTime}
                      onChange={(e) => setWeeklyTime(e.target.value)}
                    />
                  </div>
                </div>
              )}

              <div className="mt-2">
                <div className="text-sm font-medium text-gray-700 mb-1">Preview next runs (in {timezone})</div>
                <ul className="list-disc pl-5 text-sm text-gray-800 space-y-1">
                  {preview.length === 0 && (
                    <li>No upcoming runs (adjust settings)</li>
                  )}
                  {preview.map((d, idx) => (
                    <li key={idx}>{formatInTZ(d, timezone)}</li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="px-4 py-3 border-t flex items-center justify-end gap-2">
              <button
                type="button"
                className="bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 px-4 py-2 rounded"
                onClick={() => onClose && onClose()}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="button"
                className={`px-4 py-2 rounded text-white ${canSubmit && !submitting ? 'bg-teal-600 hover:bg-teal-700' : 'bg-gray-400 cursor-not-allowed'}`}
                disabled={!canSubmit || submitting}
                onClick={handleSubmit}
              >
                {submitting ? 'Creating...' : (mode === 'periodic' ? 'Create Periodic Schedule' : 'Create One-time Schedule')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
