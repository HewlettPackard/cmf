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
import Highlight from "../../components/Highlight";
import "./index.module.css";
import config from "../../config";
import FastAPIClient from "../../client";
import PythonEnvPopup from "../../components/PythonEnvPopup";

const client = new FastAPIClient(config);

const ExecutionPsTable = ({ executions, onSort, onFilter }) => {
  const [sortOrder, setSortOrder] = useState(onSort);
  const [sortedData, setSortedData] = useState([]);
  const [filterValue, setFilterValue] = useState("");
  const [expandedRow, setExpandedRow] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [popupData, setPopupData] = useState("");

  useEffect(() => {
    setSortedData([...executions]);
  }, [executions]);

  const handleFilterChange = (event) => {
    const value = event.target.value;
    setFilterValue(value);
    onFilter(value);
  };

  const toggleRow = (rowId) => {
    setExpandedRow(expandedRow === rowId ? null : rowId);
  };

  const getPropertyValue = (properties, propertyName) => {
    if (typeof properties === "string") {
      try {
        properties = JSON.parse(properties);
      } catch (e) {
        console.error("Failed to parse properties:", e);
        return "N/A";
      }
    }

    if (!Array.isArray(properties)) {
      console.warn("Expected an array for properties, got:", properties);
      return "N/A";
    }

    const values = properties
      .filter(prop => prop.name === propertyName)
      .map(prop => prop.value);

    return values.length > 0 ? values.join(", ") : "N/A";
  };

  const toggleSortOrder = () => {
    const newSortOrder = sortOrder === "asc" ? "desc" : "asc";
    setSortOrder(newSortOrder);
    onSort(newSortOrder);
  };

  const renderArrow = () => {
    if (sortOrder === "desc") {
      return (
        <span className="text-2xl cursor-pointer" style={{ marginLeft: "4px", display: "inline-flex" }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-arrow-down" viewBox="0 0 16 16">
            <path fillRule="evenodd" d="M8 1a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L7.5 13.293V1.5A.5.5 0 0 1 8 1" />
          </svg>
        </span>
      );
    } else if (sortOrder === "asc") {
      return (
        <span className="text-2xl cursor-pointer" style={{ marginLeft: "4px", display: "inline-flex" }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-arrow-up" viewBox="0 0 16 16">
            <path fillRule="evenodd" d="M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5" />
          </svg>
        </span>
      );
    } else {
      return (
        <span className="text-2xl cursor-pointer" style={{ marginLeft: "4px", display: "inline-flex" }}>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-arrow-down-up" viewBox="0 0 16 16">
            <path fillRule="evenodd" d="M11.5 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L11 2.707V14.5a.5.5 0 0 0 .5.5m-7-14a.5.5 0 0 1 .5.5v11.793l3.146-3.147a.5.5 0 0 1 .708.708l-4 4a.5.5 0 0 1-.708 0l-4-4a.5.5 0 0 1 .708-.708L4 13.293V1.5a.5.5 0 0 1 .5-.5" />
          </svg>
        </span>
      );
    }
  };

  const handleClosePopup = () => {
    setShowPopup(false);			 
  };

  return (
    <div className="flex flex-col">
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "0.5rem", marginTop: "0.5rem" }}>
        <input
          type="text"
          value={filterValue}
          onChange={handleFilterChange}
          placeholder="Filter by Context Type/Properties"
          style={{ marginRight: "1rem", padding: "0.5rem", border: "1px solid #ccc", width: "300px" }}
        />
      </div>
      <div className="overflow-x-auto">
        <div className="p-1.5 w-full inline-block align-middle">
          <table className="min-w-full divide-y divide-gray-200" id="mytable">
            <thead>
              <tr className="text-xs font-bold text-left text-black uppercase">
                <th scope="col" className="px-6 py-3"></th>
                <th scope="col" onClick={toggleSortOrder} className="px-6 py-3 Context_Type">
                  <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                    Context Type {renderArrow()}
                  </span>
                </th>
                <th scope="col" className="px-6 py-3 Execution">Execution</th>
                <th scope="col" className="px-6 py-3">
                  Python Env
                </th>
                <th scope="col" className="px-6 py-3 Git_Repo">Git Repo</th>
                <th scope="col" className="px-6 py-3 Git_Start_Commit">Git Start Commit</th>
                <th scope="col" className="px-6 py-3 Pipeline_Type">Pipeline Type</th>
              </tr>
            </thead>
            <tbody className="body divide-y divide-gray-200">
              {sortedData.map((data, index) => (
                <React.Fragment key={index}>
                  <tr key={index} onClick={() => toggleRow(index)} className="text-sm font-medium text-gray-800">
                    <td className="px-6 py-4 cursor-pointer">{expandedRow === index ? "-" : "+"}</td>
                    <td className="px-6 py-4"><Highlight text={getPropertyValue(data.execution_properties, "Context_Type")} highlight={filterValue} /></td>
                    <td className="px-6 py-4"><Highlight text={getPropertyValue(data.execution_properties, "Execution")} highlight={filterValue} /></td>
                    <td className="px-6 py-4">
                      <button
                        className="text-blue-500 hover:text-blue-700"
                        onClick={() => {
                          setShowPopup(true)
                          client.getPythonEnv(getPropertyValue(data.execution_properties, "Python_Env")).then((data) => {
                            setPopupData(data)
                          });
                        }}
                      >
                        View Env Details
                      </button>    
                      {showPopup && (
                        <PythonEnvPopup
                          show={showPopup}
                          python_env={popupData}
                          onClose={handleClosePopup}
                        />
                      )}                
                    </td>
                    <td className="px-6 py-4"><Highlight text={getPropertyValue(data.execution_properties, "Git_Repo")} highlight={filterValue} /></td>
                    <td className="px-6 py-4"><Highlight text={getPropertyValue(data.execution_properties, "Git_Start_Commit")} highlight={filterValue} /></td>
                    <td className="px-6 py-4"><Highlight text={getPropertyValue(data.execution_properties, "Pipeline_Type")} highlight={filterValue} /></td>
                  </tr>
                  {expandedRow === index && (
                    <tr>
                      <td colSpan="6">
                        <table className="expanded-table">
                          <tbody>
                            {data.execution_properties.map((property, idx) => (
                              <tr key={idx}>
                                <td>{property.name}</td>
                                <td><Highlight text={property.value} highlight={filterValue} /></td>
                              </tr>
                            ))}
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

export default ExecutionPsTable;