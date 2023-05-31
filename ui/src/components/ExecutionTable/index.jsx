//ExecutionTable.jsx

import React from "react";

const ExecutionTable = ({ executions }) => {

return (
    <div className="flex flex-col object-cover h-80 w-240 h-screen ">
      <div className="overflow-scroll">
        <div className="p-1.5 w-full inline-block align-middle">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr className="text-xs font-bold text-left text-gray-500 uppercase">
                <th scope="col" className="px-6 py-3 Context_ID">Context_ID</th>
                <th scope="col" className="px-6 py-3 Context_Type">Context_Type</th>
                <th scope="col" className="px-6 py-3 Execution">Execution</th>
                <th scope="col" className="px-6 py-3 Git_End_Commit">Git_End_Commit</th>
                <th scope="col" className="px-6 py-3 Git_Repo">Git_Repo</th>
                <th scope="col" className="px-6 py-3 Git_Start_Commit">Git_Start_Commit</th>
                <th scope="col" className="px-6 py-3 Pipeline_Type">Pipeline_Type</th>
                <th scope="col" className="px-6 py-3 Pipeline_id">Pipeline_id</th>
                <th scope="col" className="px-6 py-3 id">id</th>
                <th scope="col" className="px-6 py-3 seed">seed</th>
                <th scope="col" className="px-6 py-3 split">split</th>
              </tr>
            </thead>
            <tbody className="body divide-y divide-gray-200">
              {executions.map((data, index) => (
                <tr key={index} className="text-sm font-medium text-gray-800">
                  <td className="px-6 py-4">{data.Context_ID}</td>
                  <td className="px-6 py-4">{data.Context_Type}</td>
                  <td className="px-6 py-4">{data.Execution}</td>
                  <td className="px-6 py-4">{data.Git_End_Commit}</td>
                  <td className="px-6 py-4">{data.Git_Repo}</td>
                  <td className="px-6 py-4">{data.Git_Start_Commit}</td>
                  <td className="px-6 py-4">{data.Pipeline_Type}</td>
                  <td className="px-6 py-4">{data.Pipeline_id}</td>
                  <td className="px-6 py-4">{data.id}</td>
                  <td className="px-6 py-4">{data.seed}</td>
                  <td className="px-6 py-4">{data.split}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


export default ExecutionTable;
