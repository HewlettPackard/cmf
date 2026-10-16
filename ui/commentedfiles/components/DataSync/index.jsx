// import React, { useState } from 'react';
// import FastAPIClient from '../../client';

// const client = new FastAPIClient();

// const DataSync = ({ servers, onClearScreen }) => {
//     const [selectedServer, setSelectedServer] = useState('');
//     const [syncStatus, setSyncStatus] = useState('');

//     const handleSync = () => {
//         if (selectedServer) {
//             setSyncStatus('Syncing data...');
//             console.log(`Initiating sync with server: ${selectedServer}`);

//             // Extract server_name and server_url from the selected server
//             const [server_name, server_url] = selectedServer.split(' - ');

//             // Call the sync API
//             client.sync(server_name, server_url)
//                 .then((data) => {
//                     console.log('Sync response from server:', data);
//                     alert(data.message);
//                     alert(`Sync Status: ${data.status}`);
//                     setSyncStatus(`Sync Status: ${data.status}`);
//                 })
//                 .catch((error) => {
//                     console.error('Error during sync:', error);
//                     setSyncStatus('Failed to sync data.');
//                     alert('Failed to sync data.');
//                 });
//         } else {
//             alert('Please select a server to sync data.');
//         }
//     };

//     return (
//         <div className="max-w-md mx-auto mt-8 p-8 bg-white rounded-lg shadow-md">
//             <h2 className="text-2xl font-bold mb-6 text-teal-600 text-center">Data Sync</h2>
//             <div className="mb-6">
//                 <label htmlFor="serverSelect" className="block text-gray-700 font-semibold mb-2">
//                     Select a server:
//                 </label>
//                 <select
//                     id="serverSelect"
//                     value={selectedServer}
//                     onChange={(e) => setSelectedServer(e.target.value)}
//                     className="w-full px-4 py-2 border border-teal-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400 bg-gray-50"
//                 >
//                     <option value="">-- Select a server --</option>
//                     {servers.map((server, index) => (
//                         <option key={index} value={`${server.server_name} - ${server.server_url}`}>
//                             {server.server_name} - {server.server_url}
//                         </option>
//                     ))}
//                 </select>
//             </div>
//             <button
//                 onClick={() => {
//                     onClearScreen();
//                     handleSync();
//                 }}
//                 className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200"
//             >
//                 Sync Data
//             </button>
//             {syncStatus && <p className="mt-4 text-center text-teal-700 font-semibold">{syncStatus}</p>}
//         </div>
//     );
// };

// export default DataSync;
