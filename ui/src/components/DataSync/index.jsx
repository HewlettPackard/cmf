import React, { useState } from 'react';
import FastAPIClient from '../../client';

const client = new FastAPIClient();

const DataSync = ({ servers, onClearScreen }) => {
    const [selectedServer, setSelectedServer] = useState('');
    const [syncStatus, setSyncStatus] = useState('');

    const handleSync = () => {
        if (selectedServer) {
            setSyncStatus('Syncing data...');
            console.log(`Initiating sync with server: ${selectedServer}`);

            // Extract server_name and ip_or_host from the selected server
            const [server_name, host_info] = selectedServer.split(' - ');

            // Call the sync API
            client.sync(server_name, host_info)
                .then((data) => {
                    console.log('Sync response from server:', data); // Log the response from the server

                    // Display the message in an alert
                    alert(data.message);

                    // After the user clicks "OK," display the status in another alert
                    alert(`Sync Status: ${data.status}`);

                    // Update the sync status in the UI
                    setSyncStatus(`Sync Status: ${data.status}`);
                })
                .catch((error) => {
                    console.error('Error during sync:', error);
                    setSyncStatus('Failed to sync data.');
                    alert('Failed to sync data.');
                });
        } else {
            alert('Please select a server to sync data.');
        }
    };

    return (
        <div>
            <h2 className="text-lg font-bold mb-4">Data Sync</h2>
            <div className="mb-4">
                <label htmlFor="serverSelect" className="block mb-2">
                    Select a server:
                </label>
                <select
                    id="serverSelect"
                    value={selectedServer}
                    onChange={(e) => setSelectedServer(e.target.value)}
                    className="border border-gray-300 rounded px-2 py-1"
                >
                    <option value="">-- Select a server --</option>
                    {servers.map((server, index) => (
                        <option key={index} value={`${server.server_name} - ${server.host_info}`}>
                            {server.server_name} - {server.host_info}
                        </option>
                    ))}
                </select>
            </div>
            <button
                onClick={() => {
                    onClearScreen();
                    handleSync();
                }}
                className="bg-gray-300 hover:bg-gray-400 text-black font-bold py-2 px-4 rounded"
            >
                Sync Data
            </button>
            {syncStatus && <p className="mt-4">{syncStatus}</p>}
        </div>
    );
};

export default DataSync;
