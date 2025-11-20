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

import React, { useState, useEffect } from "react";
import "./index.css";

const SearchHelpModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg max-w-2xl max-h-96 overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Advanced Search Help</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            ✕
          </button>
        </div>
        <div className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">Supported Operators:</h4>
            <ul className="text-sm space-y-1">
              <li><code>&gt;</code> - Greater than (e.g., lines&gt;240)</li>
              <li><code>&lt;</code> - Less than (e.g., score&lt;0.5)</li>
              <li><code>&gt;=</code> - Greater than or equal (e.g., count&gt;=100)</li>
              <li><code>&lt;=</code> - Less than or equal (e.g., accuracy&lt;=0.8)</li>
              <li><code>=</code> - Equal to (e.g., status=active)</li>
              <li><code>!=</code> - Not equal to (e.g., type!=test)</li>
              <li><code>~</code> - Contains (e.g., name~prod)</li>
              <li><code>!~</code> - Does not contain (e.g., path!~temp)</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Examples:</h4>
            <ul className="text-sm space-y-1">
              <li><code>lines&gt;240</code> - Find rows where lines column &gt; 240</li>
              <li><code>score&lt;=0.5</code> - Find rows where score column ≤ 0.5</li>
              <li><code>name="test"</code> - Find rows where name equals "test"</li>
              <li><code>status!=active</code> - Find rows where status is not "active"</li>
              <li><code>lines&gt;240 score&lt;=0.5</code> - Multiple conditions (AND logic)</li>
            </ul>
          </div>
          <div>
            <p className="text-sm text-gray-600">
              You can combine structured conditions with plain text search.
              Use quotes for values containing spaces.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

const ArtifactTypeSidebar = ({
  artifactTypes,
  handleArtifactTypeClick,
  onFilter
}) => {
  const [clickedArtifactType, setClickedArtifactType] = useState(
    artifactTypes[0],
  );

  // Local filter value state
  const [filterValue, setFilterValue] = useState("");
  const [showHelpModal, setShowHelpModal] = useState(false);

  useEffect(() => {
    handleClick(artifactTypes[0]);
    // eslint-disable-next-line
  }, []);
  useEffect(() => {
    setClickedArtifactType(artifactTypes[0]);
    // eslint-disable-next-line
  }, [artifactTypes]);
  const handleClick = (artifactType) => {
    setClickedArtifactType(artifactType);
    handleArtifactTypeClick(artifactType);
  };

  const handleFilterChange = (event) => {
    const filterValue = event.target.value;
    setFilterValue(filterValue); // update the filter string
    onFilter(filterValue); // Notify parent component about filter change
  };

  return (
    <>
      <div className="flex justify-between border-b border-gray-200">
        <div className="artifacttype-tabs flex flex-row ">
          {artifactTypes.map((artifactType, index) => (
            <button
              key={artifactType}
              className={
                clickedArtifactType === artifactType
                  ? "art-tabs art-active-tabs"
                  : "art-tabs"
              }
              onClick={() => handleClick(artifactType)}
            >
              {artifactType}
            </button>
          ))}
        </div>
        <div className="flex flex-row">
          <div
            style={{
              display: "flex",
              justifyContent: "flex-end",
              marginBottom: "0.5rem",
              marginTop: "0.5rem",
              fontfamily: "Arial,sans-serif",
            }}
          >
            <input
              type="text"
              value={filterValue}
              onChange={handleFilterChange}
              placeholder={
                clickedArtifactType === "Label"
                  ? "Search labels: lines>240, score<=0.5, name=\"test\""
                  : "Filter by Name/Properties"
              }
              title={
                clickedArtifactType === "Label"
                  ? "Advanced search: Use operators like >, <, >=, <=, =, !=, ~, !~ with column names. Examples: lines>240, score<=0.5, status!=active"
                  : "Filter by Name/Properties"
              }
              style={{
                marginRight: "1rem",
                padding: "0.5rem",
                border: "1px solid #ccc",
                width: clickedArtifactType === "Label" ? "350px" : "auto",
              }}
            />
            {clickedArtifactType === "Label" && (
              <button
                onClick={() => setShowHelpModal(true)}
                className="ml-2 px-2 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
                title="Show advanced search help"
              >
                ?
              </button>
            )}
          </div>
        </div>
      </div>
      <SearchHelpModal
        isOpen={showHelpModal}
        onClose={() => setShowHelpModal(false)}
      />
    </>
  );
};

export default ArtifactTypeSidebar;
