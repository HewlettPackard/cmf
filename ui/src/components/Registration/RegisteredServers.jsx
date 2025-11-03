import React, { useState } from 'react';
import FastAPIClient from '../../client';

const client = new FastAPIClient();

function RegisteredServers({ serverList }) {
  const [syncStatus, setSyncStatus] = useState({});

  const formatEpochToHumanReadable = (epoch) => {
    if (!epoch) return "Never Synced";
    const date = new Date(epoch);
    return date.toUTCString();
  };

  console.log(serverList)

  const handleSync = (server_name, server_url, id) => {
    setSyncStatus((prev) => ({ ...prev, [id]: 'Syncing data...' }));
    client.sync(server_name, server_url)
      .then((data) => {
        alert(data.message);
        // alert(`Sync Status: ${data.status}`);
        setSyncStatus((prev) => ({ ...prev, [id]: `Sync Status: ${data.status}` }));
      })
      .catch((error) => {
        console.error('Error during sync:', error);
        setSyncStatus((prev) => ({ ...prev, [id]: 'Failed to sync data.' }));
        alert('Failed to sync data.');
      });
  };

  if (!serverList || serverList.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 bg-white rounded-lg shadow-md">No servers registered.</div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow-md w-full max-w-6xl mx-auto mt-8 overflow-x-auto">
      <h2 className="text-xl font-bold mb-4 text-teal-600 text-center">Registered Servers</h2>
      <table className="min-w-full divide-y divide-gray-200 border border-teal-600 rounded-lg">
        <thead className="bg-teal-600">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">ID</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Server Name</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Server URL</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Last Sync Time</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {serverList.map((server) => (
            <tr key={server.id} className="hover:bg-teal-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{server.id}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{server.server_name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{server.host_info}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{formatEpochToHumanReadable(server.last_sync_time)}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm">
                <button
                  className="bg-teal-600 hover:bg-teal-700 text-white font-bold py-1 px-3 rounded-lg transition duration-200"
                  onClick={() => handleSync(server.server_name, server.host_info, server.id)}
                >
                  Sync
                </button>
                {syncStatus[server.id] && (
                  <div className="mt-2 text-teal-700 font-semibold text-xs">{syncStatus[server.id]}</div>
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