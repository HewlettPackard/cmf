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
import ModelCardPopup from "../ModelCardPopup";
import Highlight from "../Highlight";
import FastAPIClient from "../../client";
import config from "../../config";
import "./index.css";
import LabelCardPopup from "../LabelCardPopup";

const client = new FastAPIClient(config);

const ArtifactPTable = ({artifacts, artifactType, onsortOrder, onsortTimeOrder, filterValue}) => {
  const [data, setData] = useState([]);
  const [sortOrder, setSortOrder] = useState("asc");
  const [sortTimeOrder, setSortTimeOrder] = useState("asc");
  const [expandedRow, setExpandedRow] = useState(null);
  const [showPopup, setShowPopup] = useState(false);
  const [popupData, setPopupData] = useState("");
  const [labelData, setLabelData] = useState("");

  useEffect(() => {
    // if data then set artifacts with that data else set it null.
    setData(artifacts);
    // handle expanded row based on filter value
    if (filterValue.trim() !== ""){
      // expand all rows when filter value is set
      setExpandedRow("all");
    }else{
      // collapse all rows when filter value is empty
      setExpandedRow(null);
    }
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
    // disable manual toggle when all rows are expanded 
    if (expandedRow === "all") return; 
    setExpandedRow(expandedRow === rowId ? null : rowId);
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

  const handleClosePopup = () => {
    setShowPopup(false);
  };

  const getLabelData = (label_name) => {
    console.log(label_name)
    client.getLabelData(label_name).then((data) => {
      console.log(data);
      setLabelData(data);
    });
  }


  return (
    <div className="flex flex-col mx-auto p-2 mr-4 w-full">
      <div className="overflow-x-auto w-full">
        <div className="p-1.5 inline-block align-middle w-full">
            <table className="divide-y divide-gray-200 border-4 w-full">
              <thead>
                <tr className="text-xs font-bold font-sans text-left text-black uppercase">
                <th scope="col" className="px-6 py-3"></th>
                <th scope="col" className="px-6 py-3">ID</th>
                <th scope="col" className="px-6 py-3" onClick={toggleSortOrder}>
                <span style={{ display: 'inline-flex', alignItems: 'center' }} >
                  Name {renderArrow()}
                </span>
                </th>
                <th className="px-6 py-3" scope="col">Execution TYPE</th>
                {artifactType === "Model" && (
                  <th scope="col" className="px-6 py-3">
                    Model Card
                  </th>
                )}
                <th scope="col" className="px-6 py-3" onClick={toggleSortTimeOrder}>
                <span style={{ display: 'inline-flex', alignItems: 'center' }} >
                  DATE {renderArrowDate()}
                </span>
                </th>
                {artifactType === "Dataset" && (
                  <th scope="col" className="label px-6 py-3">LABEL</th>
                )}
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
                        {expandedRow === index || expandedRow === "all" ? "-" : "+"}
                  </td>
                  { /* Convert artifact ID to string and render it with highlighted search term if it matches the filter value */}
                  <td className="px-6 py-4"><Highlight text={String(artifact.artifact_id)} highlight={filterValue}/></td>
                  <td className="px-6 py-4"><Highlight text={String(artifact.name)} highlight={filterValue}/></td>
                  <td className="px-6 py-4"><Highlight text={String(artifact.execution)} highlight={filterValue}/></td>
                  {artifactType === "Model" && (
                    <td className="px-6 py-4">
                      <button
                        className="text-blue-500 hover:text-blue-700"
                        onClick={() => {
                          client.getModelCard(artifact.artifact_id).then((res) => {
                            setPopupData(res);
                            setShowPopup(true);
                          });
                        }}
                      >
                        View Model Card
                      </button>
                      {showPopup && (
                        <ModelCardPopup
                          show={showPopup}
                          model_data={popupData}
                          onClose={handleClosePopup}
                        />
                      )}
                    </td>
                  )}
                  <td className="px-6 py-4"><Highlight text={String(artifact.create_time_since_epoch)} highlight={filterValue}/></td>
                  {artifactType === "Dataset" && (
                    <td className="px-6 py-4">
                      {(getPropertyValue(artifact.artifact_properties, "labels_uri") || "")
                        .split(",")
                        .map((label_name) => label_name.trim())
                        .filter((label_name) => label_name.length > 0) // Optional: skip empty strings
                        .map((label_name) => (
                          <div key={label_name} className="label">
                            <a
                              href="#"
                              onClick={(e) => {
                                e.preventDefault();
                                getLabelData(label_name.split(":")[1] || label_name);
                                setShowPopup(true);
                              }}
                            >
                              {label_name.split(":")[0] || label_name}
                            </a>
                            {showPopup && (
                              <LabelCardPopup
                                show={showPopup}
                                label_data={labelData}
                                onClose={handleClosePopup}
                              />
                            )}
                          </div>
                        ))}
                    </td>
                  )}
                  <td className="px-6 py-4"><Highlight text={String(artifact.uri)} highlight={filterValue}/></td>
                  <td className="px-6 py-4"><Highlight text={getPropertyValue(artifact.artifact_properties, "url")} highlight={filterValue}/></td>
                  <td className="px-6 py-4"><Highlight text={getPropertyValue(artifact.artifact_properties, "git_repo")} highlight={filterValue}/></td>
                  <td className="px-6 py-4"><Highlight text={getPropertyValue(artifact.artifact_properties, "Commit")} highlight={filterValue}/></td>
                </tr>
                {(expandedRow === "all" || expandedRow === index) && (
                  <tr>
                  <td colSpan="6">
                  <table className="expanded-table">
                    <tbody>
                    {artifact.artifact_properties.map((property, idx) => (
                    <tr key={idx}>
                    <td><Highlight text={String(property.name)} highlight={filterValue}/></td>
                    <td><Highlight text={String(property.value)} highlight={filterValue}/></td>
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
export default ArtifactPTable;
