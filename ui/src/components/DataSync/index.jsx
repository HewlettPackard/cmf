import React, { useState } from 'react';

const DataSync = ({ servers, onClearScreen }) => {
    const [selectedServer, setSelectedServer] = useState('');
    const [syncStatus, setSyncStatus] = useState('');

    const handleSync = async () => {
        if (selectedServer) {
            try {
                setSyncStatus('Syncing data...');
                console.log(`Initiating sync with server: ${selectedServer}`);
                const response = await fetch(`http://${selectedServer}:8080/mlmd_pull`);
                const data = await response.json();

                console.log('Sync response from server:', data); // Log the response from the server

                // Process the response to find unique executions
                const uniqueExecutions = findUniqueExecutions(data);
                if (uniqueExecutions.length > 0) {
                    // Replay unique executions on server 1
                    await replayExecutionsOnServer1(uniqueExecutions);
                    setSyncStatus('Data sync completed successfully.');
                    alert('Data sync completed successfully!'); // Alert on success
                } else {
                    setSyncStatus('No unique executions found to sync.');
                    alert('No unique executions found to sync.');
                }
            } catch (error) {
                console.error('Error during sync:', error);
                setSyncStatus('Failed to sync data.');
                alert('Failed to sync data.');
            }
        } else {
            alert('Please select a server to sync data.');
        }
    };

    const findUniqueExecutions = (data) => {
        // Logic to find unique executions from the JSON response
        const executions = data.executions || [];
        const uniqueExecutions = executions.filter((execution) => {
            // Add logic to determine uniqueness
            return true; // Placeholder
        });
        return uniqueExecutions;
    };

    const replayExecutionsOnServer1 = async (uniqueExecutions) => {
        // Logic to replay unique executions on server 1
        for (const execution of uniqueExecutions) {
            console.log('Replaying execution on server 1:', execution); // Log each execution being replayed
            await fetch(`http://${selectedServer}:8080/replay_execution`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(execution),
            });
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
                        <option key={index} value={server.ip}>
                            {server.server_name} - {server.ip_or_host}
                        </option>
                    ))}
                </select>
            </div>
            <button
                onClick={() => {
                    onClearScreen();
                    handleSync();
                }}
                className="bg-green-500 text-white font-bold py-2 px-4 rounded"
            >
                Sync Data
            </button>
            {syncStatus && <p className="mt-4">{syncStatus}</p>}
        </div>
    );
};

export default DataSync;
