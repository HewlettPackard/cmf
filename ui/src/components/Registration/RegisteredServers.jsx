function RegisteredServers({serverList}){
    return(
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
                  host_or_ip
                </th>
              </tr>
            </thead>
            <tbody className="body divide-y divide-gray-200">
              {serverList.length === 0 && (
                  alert('No registered servers found.')
              )}
              {serverList.map((server) => (
                  <tr key={server.id} className="text-xs font-sans text-gray-700">
                  <td className="id px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {server.id}
                  </td>
                  <td className="id px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {server.server_name}
                  </td>
                  <td className="exe_uuid px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {server.ip_or_host}
                  </td>
                  </tr>
              ))}
            </tbody>
          </table>
        </div>
    );
}

export default RegisteredServers;