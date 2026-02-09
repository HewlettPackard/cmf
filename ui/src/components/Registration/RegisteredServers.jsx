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

import React, { useState, useEffect } from 'react';
import FastAPIClient from '../../client';
import PeriodicSyncPicker from '../PeriodicSync/PeriodicSyncPicker';

const client = new FastAPIClient();

function RegisteredServers({ serverList }) {
  const [syncStatus, setSyncStatus] = useState({});
  const [isSyncing, setIsSyncing] = useState({}); // Track if sync is in progress
  const [openManageFor, setOpenManageFor] = useState(null); // serverId for popup
  const [activeSyncMode, setActiveSyncMode] = useState({}); // per-server: 'sync-now' | 'schedule-once' | 'periodic'
  const [showCompletedLogs, setShowCompletedLogs] = useState({}); // per-server boolean
  const [showScheduledLogs, setShowScheduledLogs] = useState({}); // per-server boolean
  const [showSyncActions, setShowSyncActions] = useState({}); // per-server boolean
  const [completedLogs, setCompletedLogs] = useState({}); // per-server completed logs data
  const [scheduledLogs, setScheduledLogs] = useState({}); // per-server scheduled logs data

  // Auto-refresh scheduled logs every 10 seconds for servers with open scheduled logs section
  useEffect(() => {
    const interval = setInterval(() => {
      Object.keys(showScheduledLogs).forEach((serverId) => {
        if (showScheduledLogs[serverId]) {
          fetchScheduledLogs(parseInt(serverId));
        }
      });
    }, 10000); // Refresh every 10 seconds

    return () => clearInterval(interval);
  }, [showScheduledLogs]);

  const toggleSection = (serverId, section, setState, onOpen) => {
    const newState = !section[serverId];
    setState((prev) => ({ ...prev, [serverId]: newState }));
    if (newState && onOpen) onOpen(serverId);
  };

  const formatEpochToHumanReadable = (epoch) => {
    if (!epoch) return "Never Synced";
    const date = new Date(epoch);
    return date.toUTCString();
  };

  const formatEpochMs = (epochMs) => {
    const date = new Date(epochMs);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
  };

  // Fetch completed logs for a server
  const fetchCompletedLogs = async (serverId) => {
    try {
      const logs = await client.getCompletedLogs(serverId);
      setCompletedLogs((prev) => ({ ...prev, [serverId]: logs }));
    } catch (error) {
      console.error('Error fetching completed logs:', error);
      setCompletedLogs((prev) => ({ ...prev, [serverId]: [] }));
    }
  };

  // Fetch scheduled syncs for a server
  const fetchScheduledLogs = async (serverId) => {
    try {
      const schedules = await client.getSchedules(serverId);
      setScheduledLogs((prev) => ({ ...prev, [serverId]: schedules }));
    } catch (error) {
      console.error('Error fetching scheduled syncs:', error);
      setScheduledLogs((prev) => ({ ...prev, [serverId]: [] }));
    }
  };

  // Delete scheduled sync
  const handleDeleteScheduledSync = async (serverId, scheduleId) => {
    if (window.confirm('Are you sure you want to delete this scheduled sync?')) {
      try {
        await client.deleteSchedule(scheduleId);
        // Refresh the scheduled logs after deletion
        await fetchScheduledLogs(serverId);
        alert('Scheduled sync deleted successfully');
      } catch (error) {
        console.error('Error deleting scheduled sync:', error);
        alert('Failed to delete scheduled sync');
      }
    }
  };

  // Handle schedule creation
  const handleScheduleSync = async (serverId, scheduleData) => {
    try {
      // Delete existing schedules for this server
      const existingSchedules = scheduledLogs[serverId] || [];
      for (const schedule of existingSchedules) {
        await client.deleteSchedule(schedule.id).catch(err =>
          console.error(`Error deleting schedule ${schedule.id}:`, err)
        );
      }

      const { timezone, startTimeLocalIso, one_time, recurrenceMode, intervalUnit, intervalValue, dailyTime, weeklyDay, weeklyTime } = scheduleData;
      await client.scheduleSync(serverId, timezone, startTimeLocalIso, one_time, recurrenceMode, intervalUnit, intervalValue, dailyTime, weeklyDay, weeklyTime);

      alert('Schedule created successfully!');
      await fetchScheduledLogs(serverId);
      setActiveSyncMode((prev) => ({ ...prev, [serverId]: null }));
    } catch (error) {
      console.error('Error creating schedule:', error);
      alert('Failed to create schedule');
    }
  };

  const handleSync = async (server_name, server_url, id) => {
    setIsSyncing((prev) => ({ ...prev, [id]: true }));
    setSyncStatus((prev) => ({ ...prev, [id]: 'Syncing data...' }));

    try {
      const data = await client.sync(server_name, server_url);
      alert(data.message);
      setSyncStatus((prev) => ({ ...prev, [id]: `Sync Status: ${data.status}` }));
      fetchCompletedLogs(id);
    } catch (error) {
      console.error('Error during sync:', error);
      setSyncStatus((prev) => ({ ...prev, [id]: 'Failed to sync data.' }));
      alert('Failed to sync data.');
    } finally {
      setIsSyncing((prev) => ({ ...prev, [id]: false }));
    }
  };

  if (!serverList || serverList.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 bg-white rounded-lg shadow-md">No servers registered.</div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow-md w-full max-w-7xl mx-auto mt-8 overflow-x-auto">
      <h2 className="text-xl font-bold mb-4 text-teal-600 text-center">Registered Servers</h2>
      <table className="min-w-full divide-y divide-gray-200 border border-teal-600 rounded-lg">
        <thead className="bg-teal-600">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">ID</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Server Name</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Server URL</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Last Sync Time</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Manage</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {serverList.map((server) => (
            <tr key={server.id} className="hover:bg-teal-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{server.id}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{server.server_name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{server.host_info}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{formatEpochToHumanReadable(server.last_sync_time)}</td>
              <td className="px-6 py-4 text-sm">
                <button
                  className="font-semibold py-1 px-3 rounded border bg-teal-50 hover:bg-teal-100 text-teal-700 border-teal-600"
                  onClick={() => {
                    setOpenManageFor(server.id);
                    setActiveSyncMode((prev) => ({ ...prev, [server.id]: null }));
                    setShowCompletedLogs((prev) => ({ ...prev, [server.id]: false }));
                    setShowScheduledLogs((prev) => ({ ...prev, [server.id]: false }));
                  }}
                >
                  Manage
                </button>

                {/* Manage Popup Modal */}
                {openManageFor === server.id && (
                  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg shadow-xl p-6 max-w-3xl w-full max-h-[90vh] overflow-y-auto">
                      {/* Header */}
                      <div className="flex justify-between items-center mb-4 pb-3 border-b-2 border-gray-300">
                        <h3 className="text-lg font-bold text-teal-600">Manage Server - {server.server_name}</h3>
                        <button
                          onClick={() => setOpenManageFor(null)}
                          className="text-gray-500 hover:text-gray-700 text-2xl font-bold"
                        >
                          &times;
                        </button>
                      </div>

                      {/* Section 1: Scheduled Syncs */}
                      <div className="mb-4">
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-semibold text-teal-700 text-base">Scheduled Syncs</h4>
                          <button
                            className="text-teal-600 hover:text-teal-700 p-1"
                            onClick={() => toggleSection(server.id, showScheduledLogs, setShowScheduledLogs, fetchScheduledLogs)}
                            title={showScheduledLogs[server.id] ? 'Hide' : 'Show'}
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              {showScheduledLogs[server.id] ? (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                              ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              )}
                            </svg>
                          </button>
                        </div>
                        {showScheduledLogs[server.id] && (
                          <div className="p-4 bg-teal-50 rounded border border-teal-200">
                            <div className="max-h-64 overflow-y-auto">
                              {(scheduledLogs[server.id] || []).length > 0 ? (
                                <table className="min-w-full divide-y divide-teal-200 bg-white rounded">
                                  <thead className="bg-teal-100">
                                    <tr>
                                      <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-teal-800 uppercase tracking-wider">Type</th>
                                      <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-teal-800 uppercase tracking-wider">Created On</th>
                                      <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-teal-800 uppercase tracking-wider">Scheduled For</th>
                                      <th scope="col" className="px-4 py-2 text-center text-xs font-semibold text-teal-800 uppercase tracking-wider">Action</th>
                                    </tr>
                                  </thead>
                                  <tbody className="bg-white divide-y divide-teal-200">
                                    {(scheduledLogs[server.id] || []).map((log) => (
                                      <tr key={log.id} className="hover:bg-teal-50">
                                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-teal-700">
                                          {log.one_time ? 'Sync in Future' : 'Periodic Sync'}
                                        </td>
                                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{formatEpochMs(log.created_at)}</td>
                                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{formatEpochMs(log.next_run_time_utc)}</td>
                                        <td className="px-4 py-3 whitespace-nowrap text-center">
                                          <button
                                            className="p-1 text-red-600 hover:text-red-700 hover:bg-red-100 rounded inline-flex items-center justify-center"
                                            onClick={() => handleDeleteScheduledSync(server.id, log.id)}
                                            title="Delete scheduled sync"
                                          >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                          </button>
                                        </td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : (
                                <div className="text-sm text-gray-500 italic">No scheduled syncs</div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* Section 2: Sync Actions */}
                      <div className="border-t-2 border-gray-300 pt-4 mb-4">
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-semibold text-teal-700 text-base">Sync Actions</h4>
                          <button
                            className="text-teal-600 hover:text-teal-700 p-1"
                            onClick={() => toggleSection(server.id, showSyncActions, setShowSyncActions)}
                            title={showSyncActions[server.id] ? 'Hide' : 'Show'}
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              {showSyncActions[server.id] ? (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                              ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              )}
                            </svg>
                          </button>
                        </div>

                        {showSyncActions[server.id] && (
                          <>
                            {/* Sync Action Buttons */}
                            <div className="flex gap-2 flex-wrap mb-4">
                              <button
                                className={`py-2 px-4 rounded font-semibold text-sm border ${activeSyncMode[server.id] === 'sync-now'
                                  ? 'bg-teal-600 text-white border-teal-600'
                                  : 'bg-white text-teal-700 border-teal-600 hover:bg-teal-50'
                                  }`}
                                onClick={() => setActiveSyncMode((prev) => ({
                                  ...prev,
                                  [server.id]: prev[server.id] === 'sync-now' ? null : 'sync-now'
                                }))}
                              >
                                Sync Now
                              </button>
                              {!isSyncing[server.id] && (
                                <>
                                  <button
                                    className={`py-2 px-4 rounded font-semibold text-sm border ${activeSyncMode[server.id] === 'schedule-once'
                                      ? 'bg-teal-600 text-white border-teal-600'
                                      : 'bg-white text-teal-700 border-teal-600 hover:bg-teal-50'
                                      }`}
                                    onClick={() => setActiveSyncMode((prev) => ({
                                      ...prev,
                                      [server.id]: prev[server.id] === 'schedule-once' ? null : 'schedule-once'
                                    }))}
                                  >
                                    Sync in Future
                                  </button>
                                  <button
                                    className={`py-2 px-4 rounded font-semibold text-sm border ${activeSyncMode[server.id] === 'periodic'
                                      ? 'bg-teal-600 text-white border-teal-600'
                                      : 'bg-white text-teal-700 border-teal-600 hover:bg-teal-50'
                                      }`}
                                    onClick={() => setActiveSyncMode((prev) => ({
                                      ...prev,
                                      [server.id]: prev[server.id] === 'periodic' ? null : 'periodic'
                                    }))}
                                  >
                                    Periodic Sync
                                  </button>
                                </>
                              )}
                            </div>

                            {/* Sync Mode Content */}
                            {activeSyncMode[server.id] === 'sync-now' && (
                              <div className="p-4 bg-gray-50 rounded border border-teal-200 mb-4">
                                <h4 className="font-semibold text-teal-700 mb-3">Sync Now</h4>
                                <p className="text-sm text-gray-600 mb-3">
                                  Click the button below to start immediate synchronization for {server.server_name}.
                                </p>
                                {syncStatus[server.id] && (
                                  <p className="text-sm text-gray-700 mb-3 p-2 bg-blue-50 rounded border border-blue-200">
                                    Status: {syncStatus[server.id]}
                                  </p>
                                )}
                                <button
                                  className="px-6 py-2 rounded text-white font-semibold bg-teal-600 hover:bg-teal-700"
                                  onClick={() => handleSync(server.server_name, server.host_info, server.id)}
                                >
                                  Start Sync Now
                                </button>
                              </div>
                            )}

                            {activeSyncMode[server.id] === 'schedule-once' && (
                              <div className="p-4 bg-gray-50 rounded border border-teal-200 mb-4">
                                <h4 className="font-semibold text-teal-700 mb-3">Sync in Future</h4>
                                <PeriodicSyncPicker
                                  serverId={server.id}
                                  serverName={server.server_name}
                                  mode="one-time"
                                  inline={true}
                                  onSchedule={(scheduleData) => handleScheduleSync(server.id, scheduleData)}
                                />
                              </div>
                            )}

                            {activeSyncMode[server.id] === 'periodic' && (
                              <div className="p-4 bg-gray-50 rounded border border-teal-200 mb-4">
                                <h4 className="font-semibold text-teal-700 mb-3">Periodic Sync</h4>
                                <PeriodicSyncPicker
                                  serverId={server.id}
                                  serverName={server.server_name}
                                  mode="periodic"
                                  inline={true}
                                  onSchedule={(scheduleData) => handleScheduleSync(server.id, scheduleData)}
                                />
                              </div>
                            )}
                          </>
                        )}
                      </div>

                      {/* Section 3: Completed Logs */}
                      <div className="border-t-2 border-gray-300 pt-4">
                        <div className="flex justify-between items-center mb-3">
                          <h4 className="font-semibold text-teal-700 text-base">Completed Logs</h4>
                          <button
                            className="text-teal-600 hover:text-teal-700 p-1"
                            onClick={() => toggleSection(server.id, showCompletedLogs, setShowCompletedLogs,
                              (id) => !completedLogs[id] && fetchCompletedLogs(id))}
                            title={showCompletedLogs[server.id] ? 'Hide' : 'Show'}
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              {showCompletedLogs[server.id] ? (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                              ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              )}
                            </svg>
                          </button>
                        </div>
                        {showCompletedLogs[server.id] && (
                          <div className="p-4 bg-teal-50 rounded border border-teal-200">
                            <div className="max-h-64 overflow-y-auto">
                              {(completedLogs[server.id] || []).length > 0 ? (
                                <table className="min-w-full divide-y divide-teal-200 bg-white rounded">
                                  <thead className="bg-teal-100">
                                    <tr>
                                      <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-teal-800 uppercase tracking-wider">Sync Type</th>
                                      <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-teal-800 uppercase tracking-wider">Completed At</th>
                                      <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-teal-800 uppercase tracking-wider">Status</th>
                                      <th scope="col" className="px-4 py-2 text-left text-xs font-semibold text-teal-800 uppercase tracking-wider">Message</th>
                                    </tr>
                                  </thead>
                                  <tbody className="bg-white divide-y divide-teal-200">
                                    {(completedLogs[server.id] || []).map((log) => (
                                      <tr key={log.id} className="hover:bg-teal-50">
                                        <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-teal-700">
                                          {log.sync_type === 'sync_now' ? 'Sync Now' : log.sync_type === 'schedule_once' ? 'One-time Sync' : 'Periodic Sync'}
                                        </td>
                                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">{formatEpochMs(log.run_time_utc)}</td>
                                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-700">
                                          <span className={`px-2 py-1 rounded text-xs font-semibold ${log.status === 'success' ? 'bg-green-100 text-green-800' :
                                            log.status === 'failed' ? 'bg-red-100 text-red-800' :
                                              'bg-yellow-100 text-yellow-800'
                                            }`}>
                                            {log.status}
                                          </span>
                                        </td>
                                        <td className="px-4 py-3 text-sm text-gray-700">{log.message || 'N/A'}</td>
                                      </tr>
                                    ))}
                                  </tbody>
                                </table>
                              ) : (
                                <div className="text-sm text-gray-500 italic">No completed logs yet</div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RegisteredServers;