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
import React, { useState, useEffect, useRef } from "react";
import ModelCardPopup from "../ModelCardPopup";
import Highlight from "../Highlight";
import FastAPIClient from "../../client";
import config from "../../config";
import "./index.css";
import LabelCardPopup from "../LabelCardPopup";

const client = new FastAPIClient(config);


const ArtifactPTable = ({
  artifacts,
  artifactType,
  onSortOrder,
  onSortTimeOrder,
  filterValue,
  onLabelClick,
  expandedRow: externalExpandedRow,
  setExpandedRow: externalSetExpandedRow,
}) => {
  
  const [sortOrder, setSortOrder] = useState("asc");
  const [sortTimeOrder, setSortTimeOrder] = useState("asc");
  // Use internal state as fallback if external state is not provided
  const [internalExpandedRow, setInternalExpandedRow] = useState(null);
  // Use external state if provided, otherwise use internal state
  const expandedRow = externalExpandedRow !== undefined ? externalExpandedRow : internalExpandedRow;
  const setExpandedRow = externalSetExpandedRow || setInternalExpandedRow;

  
  const [showModelPopup, setShowModelPopup] = useState(false);
  const [showLabelPopup, setShowLabelPopup] = useState(false);
  const [popupData, setPopupData] = useState("");
  const [labelData, setLabelData] = useState("");

  // Handle expanded row based on filter value - only when filter actually changes
  const prevFilterRef = useRef(String(filterValue || ""));

  console.log("artifacts in ArtifactPTable:", artifacts);
  useEffect(() => {
    const prev = prevFilterRef.current;
    const current = String(filterValue || "");

    if (prev !== current) {
      if (current.trim() !== "") {
        setExpandedRow("all");
      } else if (prev.trim() !== "") {
        // only collapse if previously non-empty
        setExpandedRow(null);
      }
      prevFilterRef.current = current;
    }
  }, [filterValue, setExpandedRow, artifactType]); // minimal deps
  // removed expandedRow - not sure for what reason it was here


  const renderArrow = (order) => (
    <span className="text-2xl cursor-pointer" style={{ marginLeft: '4px', display: 'inline-flex' }}>
      {order === "asc" ? "↑" : "↓"}
    </span>
  );

  const getPropertyValue = (properties, propertyName) => {
    // Check if properties is a string and parse it
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
        return "N/A";
    }

    // Filter the properties by name and extract string_value
    const values = properties
      .filter(prop => prop.name === propertyName)  // Filter properties by name
      .map(prop => prop.value);  // Extract string_value

    // Return the values as a comma-separated string or "N/A" if no values are found
    return values.length > 0 ? values.join(", ") : "N/A";
  };

  const toggleRow = (rowId) => {
    // disable manual toggle when all rows are expanded 
    if (expandedRow === "all") return; 
    setExpandedRow(expandedRow === rowId ? null : rowId);
  };

  const toggleSort = (currentOrder, setOrder, callback) => {
    const newSortOrder = currentOrder === "asc" ? "desc" : "asc";
    setOrder(newSortOrder);
    callback(newSortOrder);
  };

  const toggleSortOrder = () => {
    toggleSort(sortOrder, setSortOrder, onSortOrder);
  };

  const toggleSortTimeOrder = () => {
    toggleSort(sortTimeOrder, setSortTimeOrder, onSortTimeOrder);
  };

  const handleCloseModelPopup = () => {
    setShowModelPopup(false);
  };

  const handleCloseLabelPopup = () => {
    setShowLabelPopup(false);
  };

  const renderLabels = (artifact) => {
    const labelsUri = getPropertyValue(artifact.artifact_properties, "labels_uri");

    if (!labelsUri || labelsUri === "N/A" || labelsUri.trim() === "") {
      return <span className="text-gray-500">N/A</span>;
    }

    return labelsUri
      .split(",")
      .map((label_name) => label_name.trim())
      .filter((label_name) => label_name.length > 0 && label_name !== "N/A")
      .map((label_name) => (
        <div key={label_name} className="label">
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault();
              client.getLabelData(label_name.split(":")[1] || label_name).then((data) => {
                setLabelData(data);
                setShowLabelPopup(true);
              });
            }}
          >
            <Highlight text={label_name} highlight={filterValue}/>
          </a>
        </div>
      ));
  };

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
                <span className="sort-header-content">
                  Name {renderArrow(sortOrder)}
                </span>
                </th>
                <th className="px-6 py-3" scope="col">Execution TYPE</th>
                {artifactType === "Model" && (
                  <th scope="col" className="px-6 py-3">
                    Model Card
                  </th>
                )}
                <th scope="col" className="px-6 py-3" onClick={toggleSortTimeOrder}>
                <span className="sort-header-content">
                  DATE {renderArrow(sortTimeOrder)}
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
                  <td className="px-6 py-4">
                    {artifactType === "Label" && onLabelClick ? (
                      <a
                        href="#"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          onLabelClick(artifact.name, artifact);
                        }}
                        className="text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
                      >
                        <Highlight text={String(artifact.name)} highlight={filterValue}/>
                      </a>
                    ) : (
                      <Highlight text={String(artifact.name)} highlight={filterValue}/>
                    )}
                  </td>
                  <td className="px-6 py-4"><Highlight text={String(artifact.execution)} highlight={filterValue}/></td>
                  {artifactType === "Model" && (
                    <td className="px-6 py-4">
                      <button
                        className="text-blue-500 hover:text-blue-700"
                        onClick={() => {
                          client.getModelCard(artifact.artifact_id).then((res) => {
                            setPopupData(res);
                            setShowModelPopup(true);
                          });
                        }}
                      >
                        View Model Card
                      </button>
                    </td>
                  )}
                  <td className="px-6 py-4"><Highlight text={String(artifact.create_time_since_epoch)} highlight={filterValue}/></td>
                  {artifactType === "Dataset" && (
                    <td className="px-6 py-4">
                      {renderLabels(artifact)}
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
      {showModelPopup && (
        <ModelCardPopup
          show={showModelPopup}
          model_data={popupData}
          onClose={handleCloseModelPopup}
        />
      )}
      {showLabelPopup && (
        <LabelCardPopup
          show={showLabelPopup}
          label_data={labelData}
          onClose={handleCloseLabelPopup}
        />
      )}
    </div>
  );
};
export default ArtifactPTable;
