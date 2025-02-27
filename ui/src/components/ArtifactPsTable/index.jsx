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

// ArtifactTable.jsx
import React, { useState, useEffect } from "react";
import "./index.css";
import FastAPIClient from "../../client";
import config from "../../config";

const client = new FastAPIClient(config);

const ArtifactPsTable = ({artifacts, onsortOrder, onsortTimeOrder}) => {
  const [data, setData] = useState([]);
  const [sortOrder, setSortOrder] = useState("asc");
  const [sortTimeOrder, setSortTimeOrder] = useState("asc");
  const [expandedRow, setExpandedRow] = useState(null);

  const consistentColumns = [];

  console.log("artifacts",artifacts);

  useEffect(() => {
    // if data then set artifacts with that data else set it null.
    setData(artifacts);
    //setSortedData([data]);
  }, [artifacts]);


  const renderArrow = () => (
    <span className="text-2xl cursor-pointer" style={{ marginLeft: '4px', display: 'inline-flex' }}>
      {sortOrder === "asc" ? "↑" : sortOrder === "desc" ? "↓" : "↑"}
    </span>
  );

  const renderArrowDate = () => (
    <span className="text-2xl cursor-pointer" style={{ marginLeft: '4px', display: 'inline-flex' }}>
      {sortTimeOrder === "asc" ? "↑" : sortTimeOrder === "desc" ? "↓" : "↑"}
    </span>
  );

  const getPropertyValue = (properties, propertyName) => {
    // console.log(artifacts);
    // console.log(properties);
    // console.log(propertyName);
    // // Check if properties is a string and parse it
    if (typeof properties === "string") {
        try {
            properties = JSON.parse(properties);  // Parse the string to an array
        } catch (e) {
            console.error("Failed to parse properties:", e);
            return "N/A";  // Return "N/A" if parsing fails
        }
    }

    // Ensure properties is now an array
    if (!Array.isArray(properties)) {
        console.warn("Expected an array for properties, got:", properties);
        return "N/A";
    }

    // Filter the properties by name and extract string_value
    const values = properties
      .filter(prop => prop.name === propertyName)  // Filter properties by name
      .map(prop => prop.value);  // Extract string_value

    // // Return the values as a comma-separated string or "N/A" if no values are found
    return values.length > 0 ? values.join(", ") : "N/A";
  };

  const toggleRow = (rowId) => {
    if (expandedRow === rowId) {
      setExpandedRow(null);
    } else {
      setExpandedRow(rowId);
    }
  };

  const toggleSortOrder = () => {
    const newSortOrder = sortOrder === "asc" ? "desc" : "asc";
    setSortOrder(newSortOrder);
    onsortOrder(newSortOrder);
  };

  const toggleSortTimeOrder = () => {
    const newSortOrder = sortTimeOrder === "asc" ? "desc" : "asc";
    setSortTimeOrder(newSortOrder);
    onsortTimeOrder(newSortOrder);
  };


  return (
    <div className="flex flex-col mx-auto p-2 mr-4 w-full">
      <div className="overflow-x-auto w-full">
        <div className="p-1.5 inline-block align-middle w-full">
            <table className="divide-y divide-gray-200 border-4 w-full">
              <thead>
                <tr className="text-xs font-bold font-sans text-left text-black uppercase">
                <th scope="col" className="px-6 py-3"></th>
                <th className="px-6 py-3" scope="col">ID</th>
                <th className="px-6 py-3" onClick={toggleSortOrder}>
                <span scope="col" 
                      style={{ display: 'inline-flex', alignItems: 'center' }} >
                Name {renderArrow()}
                </span>
                </th>
                <th className="px-6 py-3" scope="col">Execution TYPE</th>
                <th className="px-6 py-3" onClick={toggleSortTimeOrder}>
                <span scope="col" 
                      style={{ display: 'inline-flex', alignItems: 'center' }} >
                DATE {renderArrowDate()}
                </span>
                </th>
                <th className="px-6 py-3" scope="col">URI</th>
                <th className="px-6 py-3" scope="col">URL</th>
                <th className="px-6 py-3" scope="col">GIT REPO</th>
                <th className="px-6 py-3" scope="col">COMMIT</th>
                </tr>
              </thead>
              <tbody className="body divide-y divide-gray-200">
                {artifacts.map((artifact, index) => (
                <React.Fragment key={index}>
                <tr key={index} className="text-sm font-medium text-gray-800">
                  <td
                        className="px-6 py-4 cursor-pointer"
                        onClick={() => toggleRow(index)}
                      >
                        {expandedRow === index ? "-" : "+"}
                  </td>
                  <td className="px-6 py-4">{artifact.artifact_id}</td>
                  <td className="px-6 py-4">{artifact.name}</td>
                  <td className="px-6 py-4">{artifact.execution}</td>
                  <td className="px-6 py-4">{artifact.create_time_since_epoch}</td>
                  <td className="px-6 py-4">{artifact.uri}</td>
                  <td className="px-6 py-4">{getPropertyValue(artifact.artifact_properties, "url")}</td>
                  <td className="px-6 py-4">{getPropertyValue(artifact.artifact_properties, "git_repo")}</td>
                  <td className="px-6 py-4">{getPropertyValue(artifact.artifact_properties, "Commit")}</td>
                </tr>
                {expandedRow === index && (
                <tr>
                <td colSpan="6">
                <table className="expanded-table">
                  <tbody>
                  {artifact.artifact_properties.map((property, idx) => (
                  <tr key={idx}>
                  <td>{property.name}</td>
                  <td>{property.value}</td>
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
export default ArtifactPsTable;
