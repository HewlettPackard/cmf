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

// Sidebar.js

import React, { useState, useEffect } from "react";

// Human-readable labels for lineage type keys
const LINEAGE_LABELS = {
  Artifact_Tree: "Artifact Lineage",
  Execution_Tree: "Execution Lineage",
  Artifact_Execution_Tree: "Artifact Execution Lineage",
};

// Icon per lineage type
const LineageIcon = ({ type }) => {
  if (type === "Artifact_Tree") {
    return (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3h14M5 9h8m-8 6h5M3 21h18M9 3v18" />
      </svg>
    );
  }
  if (type === "Execution_Tree") {
    return (
      <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-2-2 2M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
      </svg>
    );
  }
  return (
    <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  );
};

/**
 * Sidebar — two modes:
 *   • Stages mode  (artifacts / executions pages): pass `stages`, `selectedStage`, `handleStageClick`
 *   • Lineage mode (lineage page):                 pass `lineageTypes`, `selectedLineageType`, `handleLineageTypeClick`
 */
const Sidebar = ({
  pipelines,
  selectedPipeline,
  // Stages mode
  stages,
  selectedStage,
  handleStageClick,
  // Lineage mode
  lineageTypes,
  selectedLineageType,
  handleLineageTypeClick,
  // Common
  handlePipelineClick,
}) => {
  const [expandedPipeline, setExpandedPipeline] = useState(0);

  // Sync expanded pipeline with selectedPipeline prop (e.g. when navigating from home)
  useEffect(() => {
    if (selectedPipeline && pipelines.length > 0) {
      const idx = pipelines.indexOf(selectedPipeline);
      if (idx !== -1) {
        setExpandedPipeline(idx);
      }
    }
  }, [selectedPipeline, pipelines]);

  const isLineageMode = Array.isArray(lineageTypes) && lineageTypes.length > 0;

  const handlePipelineToggle = (pipeline, index) => {
    if (expandedPipeline === index) {
      setExpandedPipeline(null);
    } else {
      setExpandedPipeline(index);
      handlePipelineClick(pipeline);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50 border-r border-gray-200">
      {/* Header */}
      <div className="px-4 py-4 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          {/* pipeline icon */}
          <svg className="w-4 h-4 text-teal-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
          </svg>
          <h1 className="text-sm font-bold text-gray-800 uppercase tracking-wider">Pipelines</h1>
          {pipelines.length > 0 && (
            <span className="ml-auto inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-teal-100 text-teal-700">
              {pipelines.length}
            </span>
          )}
        </div>
      </div>

      {/* Pipeline list */}
      <div className="flex-1 overflow-y-auto py-2">
        <ul className="list-none p-0 m-0 space-y-0.5 px-2">
          {pipelines.map((pipeline, index) => (
            <li key={index}>
              {/* Pipeline button */}
              <button
                className={`w-full text-left px-3 py-2.5 rounded-lg transition-all duration-200 break-words group ${selectedPipeline === pipeline
                    ? "bg-teal-600 text-white shadow-sm"
                    : "text-gray-700 hover:bg-white hover:shadow-sm hover:text-gray-900"
                  }`}
                onClick={() => handlePipelineToggle(pipeline, index)}
              >
                <span className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium flex-1 text-left break-all">{pipeline}</span>
                  <svg
                    className={`w-4 h-4 flex-shrink-0 transition-transform duration-200 ${expandedPipeline === index ? "rotate-90" : ""
                      } ${selectedPipeline === pipeline ? "text-white" : "text-gray-400 group-hover:text-gray-600"}`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </span>
              </button>

              {expandedPipeline === index && selectedPipeline === pipeline && (
                <>
                  {/* ── LINEAGE MODE: show 3 lineage sub-types ── */}
                  {isLineageMode && (
                    <>
                      <div className="mt-1 px-3 pb-1">
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Lineage</span>
                      </div>
                      <ul className="mb-1 list-none space-y-0.5 pl-2 border-l-2 border-teal-200 ml-3">
                        {lineageTypes.map((type) => (
                          <li key={type}>
                            <button
                              className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-all duration-200 flex items-center gap-2 ${selectedLineageType === type
                                  ? "bg-teal-50 text-teal-700 font-semibold border border-teal-200"
                                  : "text-gray-600 hover:bg-white hover:text-gray-900 hover:shadow-sm"
                                }`}
                              onClick={(e) => {
                                e.preventDefault();
                                handleLineageTypeClick(type);
                              }}
                            >
                              {selectedLineageType === type && (
                                <span className="w-1.5 h-1.5 rounded-full bg-teal-500 flex-shrink-0" />
                              )}
                              <LineageIcon type={type} />
                              <span className="break-words">{LINEAGE_LABELS[type] || type}</span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}

                  {/* ── STAGES MODE: show stage list ── */}
                  {!isLineageMode && Array.isArray(stages) && stages.length > 0 && (
                    <>
                      <div className="mt-1 px-3 pb-1">
                        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Stages</span>
                      </div>
                      <ul className="mb-1 list-none space-y-0.5 pl-2 border-l-2 border-teal-200 ml-3">
                        {stages.map((stage, stageIndex) => (
                          <li key={stageIndex}>
                            <button
                              className={`w-full text-left px-3 py-2 text-sm rounded-lg transition-all duration-200 break-words ${selectedStage === stage
                                  ? "bg-teal-50 text-teal-700 font-semibold border border-teal-200"
                                  : "text-gray-600 hover:bg-white hover:text-gray-900 hover:shadow-sm"
                                }`}
                              onClick={(e) => {
                                e.preventDefault();
                                handleStageClick(stage);
                              }}
                            >
                              <span className="flex items-center gap-2">
                                {selectedStage === stage && (
                                  <span className="w-1.5 h-1.5 rounded-full bg-teal-500 flex-shrink-0" />
                                )}
                                <span className="break-all">{stage.split("/").pop() || stage}</span>
                              </span>
                            </button>
                          </li>
                        ))}
                      </ul>
                    </>
                  )}
                </>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default Sidebar;

