/***
 * Copyright (2025) Hewlett Packard Enterprise Development LP
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

import React, { useState } from 'react';

const PeriodicSyncPicker = ({ serverId, serverName, onSchedule }) => {
    const [scheduledDateTime, setScheduledDateTime] = useState('');
    const [isScheduled, setIsScheduled] = useState(false);
    const [scheduledTime, setScheduledTime] = useState('');

    const getMinDateTime = () => {
        // To ensure the user cannot select a past date/time
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        return `${year}-${month}-${day}T${hours}:${minutes}`;
    };

    const formatDateTime = (dateTimeString) => {
        // Format date-time string to a more readable format
        if (!dateTimeString) return '';
        const date = new Date(dateTimeString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
        });
    };

    const handleDateTimeChange = (dateTime) => {
        setScheduledDateTime(dateTime);
        setIsScheduled(false);
    };

    const handlePeriodicSync = () => {
        if (!scheduledDateTime) {
            alert('Please select a date and time');
            return;
        }

        setIsScheduled(true);
        setScheduledTime(scheduledDateTime);

        if (onSchedule) {
            onSchedule(serverId, serverName, scheduledDateTime);
        }

        alert(`Periodic sync scheduled for ${serverName} at ${formatDateTime(scheduledDateTime)}`);
    };

    return (
        <div className="flex flex-col gap-2">
            <input
                type="datetime-local"
                value={scheduledDateTime}
                onChange={(e) => handleDateTimeChange(e.target.value)}
                min={getMinDateTime()}
                className="px-3 py-2 border-2 border-teal-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-400"
            />
            {scheduledDateTime && (
                <button
                    className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200"
                    onClick={handlePeriodicSync}
                >
                    Periodic Sync
                </button>
            )}
            {isScheduled && scheduledTime && (
                <div className="text-xs text-green-700 font-semibold bg-green-50 p-2 rounded">
                    ✓ Scheduled: {formatDateTime(scheduledTime)}
                </div>
            )}
        </div>
    );
};

export default PeriodicSyncPicker;
