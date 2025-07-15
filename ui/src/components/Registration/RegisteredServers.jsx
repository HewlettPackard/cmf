function RegisteredServers({ serverList }) {
  const formatEpochToHumanReadable = (epoch) => {
    if (!epoch) return "Never Synced";
    const date = new Date(epoch);
    return date.toUTCString();
  };

  if (serverList.length === 0) {
    return <div className="p-1.5 inline-block align-middle w-full">No servers registered.</div>;
  }

  return (
    <div className="p-1.5 inline-block align-middle w-full">
      <table className="divide-y divide-gray-200 border-4 w-full">
        <thead>
          <tr className="text-xs font-bold font-sans text-left text-black uppercase">
            <th scope="col" className="id px-6 py-3">
              id
            </th>
            <th scope="col" className="id px-6 py-3">
              server_name
            </th>
            <th scope="col" className="exe_uuid px-6 py-3">
              host
            </th>
            <th scope="col" className="exe_uuid px-6 py-3">
              last_sync_time
            </th>
          </tr>
        </thead>
        <tbody className="body divide-y divide-gray-200">
          {serverList.map((server) => (
            <tr key={server.id} className="text-xs font-sans text-gray-700">
              <td className="id px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {server.id}
              </td>
              <td className="id px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {server.server_name}
              </td>
              <td className="exe_uuid px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {server.host_info}
              </td>
              <td className="exe_uuid px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                {formatEpochToHumanReadable(server.last_sync_time)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default RegisteredServers;