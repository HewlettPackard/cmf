/***
* Copyright (2023) Hewlett Packard Enterprise Development LP
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


//ExecutionTable.jsx
import React, { useState, useEffect } from "react";
import "./index.css";

const ExecutionTable = ({ executions, onSort, onFilter}) => {

// Default sorting order
  const [sortOrder, setSortOrder] = useState(onSort);
  const [sortedData, setSortedData] = useState([]);
  // Local filter value state
  const [filterValue, setFilterValue] = useState("");
  const [expandedRow, setExpandedRow] = useState(null);

  const consistentColumns = [];

  useEffect(() => {
    // Set initial sorting order when component mounts
    setSortedData([...executions]);
  }, [executions]);


  const handleSort = () => {
    const newSortOrder = sortOrder === "asc" ? "desc" : "asc";
    setSortOrder(newSortOrder);
    const sorted = [...executions].sort((a, b) => {
        if(newSortOrder === "asc"){
            return a.Context_Type.localeCompare(b.Context_Type);
        }else{
            return b.Context_Type.localeCompare(a.Context_Type);
        }
    });
    setSortedData(sorted); // Notify parent component about sorting change
  };

  const handleFilterChange = (event) => {
    const value = event.target.value;
    setFilterValue(value);
    onFilter("Context_Type", value); // Notify parent component about filter change
  };

  const toggleRow = (rowId) => {
    if (expandedRow === rowId) {
      setExpandedRow(null);
    } else {
      setExpandedRow(rowId);
    }
  };

  return (
    <div className="flex flex-col">
      <div
        style={{
          display: "flex",
          justifyContent: "flex-end",
          marginBottom: "0.5rem",
          marginTop: "0.5rem",
        }}
      >
        <input
          type="text"
          value={filterValue}
          onChange={handleFilterChange}
          placeholder="Filter by Context_Type"
          style={{
            marginRight: "1rem",
            padding: "0.5rem",
            border: "1px solid #ccc",
          }}
        />
      </div>
      <div className="overflow-x-auto">
        <div className="p-1.5 w-full inline-block align-middle">
          <table className="min-w-full divide-y divide-gray-200" id="mytable">
            <thead className="bg-gray-100">
              <tr className="text-xs font-bold text-left text-gray-500 uppercase">
                <th scope="col" className="px-6 py-3"></th>
                <th
                  scope="col"
                  onClick={handleSort}
                  className="px-6 py-3 Context_Type"
                >
                  Context_Type {sortOrder === "asc" && <span className="cursor-pointer">&#8593;</span>}
                  {sortOrder === "desc" && <span className="cursor-pointer">&#8595;</span>}
                </th>
                <th scope="col" className="px-6 py-3 Execution">
                  Execution
                </th>
                <th scope="col" className="px-6 py-3 Git_Repo">
                  Git_Repo
                </th>
                <th scope="col" className="px-6 py-3 Git_Start_Commit">
                  Git_Start_Commit
                </th>
                <th scope="col" className="px-6 py-3 Pipeline_Type">
                  Pipeline_Type
                </th>
              </tr>
            </thead>
            <tbody className="body divide-y divide-gray-200">
              {sortedData.map((data, index) => (
                <React.Fragment key={index}>
                  <tr
                    key={index}
                    onClick={() => toggleRow(index)}
                    className="text-sm font-medium text-gray-800"
                  >
                    <td className="px-6 py-4 cursor-pointer">
                      {expandedRow === index ? "-" : "+"}
                    </td>
                    <td className="px-6 py-4">{data.Context_Type}</td>
                    <td className="px-6 py-4">{data.Execution}</td>
                    <td className="px-6 py-4">{data.Git_Repo}</td>
                    <td className="px-6 py-4">{data.Git_Start_Commit}</td>
                    <td className="px-6 py-4">{data.Pipeline_Type}</td>
                  </tr>
                  {expandedRow === index && (
                    <tr>
                      <td colSpan="4">
                        <table className="expanded-table">
                          <tbody>
                            {Object.entries(data).map(([key, value]) => {
                              if (
                                !consistentColumns.includes(key) &&
                                value != null
                              ) {
                                return (
                                  <React.Fragment key={key}>
                                    <tr>
                                      <td key={key}>{key}</td>
                                      <td key={value}>
                                        {value ? value : "Null"}
                                      </td>
                                    </tr>
                                  </React.Fragment>
                                );
                              }
                              return null;
                            })}
                          </tbody>
                        </table>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ExecutionTable;