
function RegisteredServers({ serverList }) {
  const formatEpochToHumanReadable = (epoch) => {
    if (!epoch) return "Never Synced";
    const date = new Date(epoch);
    return date.toUTCString();
  };

  if (!serverList || serverList.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500 bg-white rounded-lg shadow-md">No servers registered.</div>
    );
  }

  return (
    <div className="p-4 bg-white rounded-lg shadow-md max-w-2xl mx-auto mt-8">
      <h2 className="text-xl font-bold mb-4 text-teal-600 text-center">Registered Servers</h2>
      <table className="min-w-full divide-y divide-gray-200 border border-teal-600 rounded-lg overflow-hidden">
        <thead className="bg-teal-600">
          <tr>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">ID</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Server Name</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Server URL</th>
            <th scope="col" className="px-6 py-3 text-left text-xs font-bold text-white uppercase tracking-wider">Last Sync Time</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {serverList.map((server) => (
            <tr key={server.id} className="hover:bg-teal-50">
              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{server.id}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{server.server_name}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{server.server_url}</td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{formatEpochToHumanReadable(server.last_sync_time)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RegisteredServers;