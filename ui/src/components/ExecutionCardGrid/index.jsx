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

import React, { useState } from "react";
import Highlight from "../Highlight";
import FastAPIClient from "../../client";
import config from "../../config";
import PythonEnvPopup from "../PythonEnvPopup";

const client = new FastAPIClient(config);

const ExecutionCard = ({ execution, filterValue, onCardClick, isSelected = false, onToggle }) => {
    const [showPythonPopup, setShowPythonPopup] = useState(false);
    const [pythonEnvData, setPythonEnvData] = useState("");
    const [expandedProperties, setExpandedProperties] = useState(false);

    const getProp = (name) => {
        if (!execution.execution_properties) return "N/A";
        const props = Array.isArray(execution.execution_properties)
            ? execution.execution_properties
            : (() => {
                try {
                    return JSON.parse(execution.execution_properties);
                } catch {
                    return [];
                }
            })();
        const match = props.filter((p) => p.name === name).map((p) => p.value);
        return match.length > 0 ? match.join(", ") : "N/A";
    };

    const contextType = getProp("Context_Type");
    const executionName = getProp("Execution");
    const gitRepo = getProp("Git_Repo");
    const gitCommit = getProp("Git_Start_Commit");
    const pipelineType = getProp("Pipeline_Type");
    const pythonEnv = getProp("Python_Env");

    const formatDate = (timestamp) => {
        if (!timestamp || timestamp === "N/A") return null;
        try {
            return new Date(parseFloat(timestamp)).toLocaleString();
        } catch {
            return null;
        }
    };

    const createdAt = formatDate(getProp("original_create_time_since_epoch"));

    const handlePythonEnvClick = (e) => {
        e.stopPropagation();
        if (pythonEnv && pythonEnv !== "N/A") {
            client.getPythonEnv(pythonEnv).then((data) => {
                setPythonEnvData(data);
                setShowPythonPopup(true);
            });
        }
    };

    const allProps = Array.isArray(execution.execution_properties)
        ? execution.execution_properties
        : (() => {
            try {
                return JSON.parse(execution.execution_properties || "[]");
            } catch {
                return [];
            }
        })();

    return (
        <>
            <div
                className={`bg-white rounded-lg border-2 ${isSelected
                    ? 'border-teal-500 shadow-lg'
                    : 'border-gray-300 hover:border-teal-500 hover:shadow-lg'
                    } transition-all duration-200 overflow-hidden cursor-pointer`}
                onClick={() => onCardClick && onCardClick(execution)}
            >
                {/* Card Header */}
                <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
                    <div className="flex items-start justify-between gap-2">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                            <div className="text-teal-600 flex-shrink-0">
                                <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                                    <path
                                        fillRule="evenodd"
                                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                                        clipRule="evenodd"
                                    />
                                </svg>
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className="text-xs font-semibold text-gray-500 uppercase">
                                        ID: <Highlight text={String(execution.execution_id || "")} highlight={filterValue} />
                                    </span>
                                    {pipelineType !== "N/A" && (
                                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-teal-100 text-teal-800">
                                            {pipelineType}
                                        </span>
                                    )}
                                </div>
                                {createdAt && (
                                    <div className="flex items-center gap-1 mb-1">
                                        <svg className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                                        </svg>
                                        <span className="text-xs text-gray-500">{createdAt}</span>
                                    </div>
                                )}
                                <h3 className="text-sm font-bold text-gray-900 break-all line-clamp-2" title={contextType}>
                                    <Highlight text={String(contextType)} highlight={filterValue} />
                                </h3>
                            </div>
                        </div>
                        {onToggle && (
                            <input
                                type="checkbox"
                                title={isSelected ? "Deselect" : "Select for comparison"}
                                checked={isSelected}
                                onChange={() => { }}
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onToggle(execution);
                                }}
                                className="w-4 h-4 mt-1 flex-shrink-0 accent-teal-600 cursor-pointer"
                            />
                        )}
                    </div>
                </div>

                {/* Card Body */}
                <div className="p-4 space-y-3">
                    {executionName !== "N/A" && (
                        <div className="flex items-start gap-2">
                            <svg className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd" />
                            </svg>
                            <div className="flex-1 min-w-0">
                                <span className="text-xs text-gray-500 block">Execution:</span>
                                <span className="text-sm font-medium text-gray-700 break-all">
                                    <Highlight text={String(executionName)} highlight={filterValue} />
                                </span>
                            </div>
                        </div>
                    )}

                    {(gitRepo !== "N/A" || gitCommit !== "N/A") && (
                        <div className="flex flex-wrap gap-2 min-w-0">
                            {gitRepo !== "N/A" && (
                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-purple-50 border border-purple-200 rounded-md max-w-full">
                                    <svg className="w-3.5 h-3.5 text-purple-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                                    </svg>
                                    <span className="text-xs text-purple-700 truncate" title={gitRepo}>
                                        <Highlight text={gitRepo} highlight={filterValue} />
                                    </span>
                                </div>
                            )}
                            {gitCommit !== "N/A" && (
                                <div className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-green-50 border border-green-200 rounded-md max-w-full overflow-hidden">
                                    <svg className="w-3.5 h-3.5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 6a4 4 0 100 8 4 4 0 000-8zM2 9a1 1 0 000 2h4.126a6 6 0 000-2H2zm11.874 0a6 6 0 000 2H18a1 1 0 100-2h-4.126z" clipRule="evenodd" />
                                    </svg>
                                    <span className="text-xs text-green-700 font-mono truncate min-w-0" title={gitCommit}>
                                        <Highlight text={gitCommit} highlight={filterValue} />
                                    </span>
                                </div>
                            )}
                        </div>
                    )}

                    {pythonEnv !== "N/A" && (
                        <button
                            className="w-full px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-md text-sm font-medium transition-colors shadow-sm hover:shadow mt-2"
                            onClick={handlePythonEnvClick}
                        >
                            View Python Env
                        </button>
                    )}
                </div>

                {/* Card Footer - Expandable all properties */}
                <div className="border-t border-gray-200">
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            setExpandedProperties(!expandedProperties);
                        }}
                        className="w-full px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-between"
                    >
                        <span className="flex items-center gap-2">
                            <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                                <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                            </svg>
                            View All Properties ({allProps.length})
                        </span>
                        <svg
                            className={`w-5 h-5 text-gray-400 transition-transform ${expandedProperties ? "transform rotate-180" : ""}`}
                            fill="currentColor"
                            viewBox="0 0 20 20"
                        >
                            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                    </button>
                    {expandedProperties && (
                        <div className="px-4 pb-4 max-h-64 overflow-y-auto bg-gray-50">
                            <div className="space-y-2">
                                {allProps.map((prop, idx) => (
                                    <div key={idx} className="bg-white rounded p-2 border border-gray-200">
                                        <div className="text-xs font-semibold text-gray-500 uppercase mb-1">
                                            <Highlight text={String(prop.name)} highlight={filterValue} />
                                        </div>
                                        <div className="text-sm text-gray-900 break-all">
                                            <Highlight text={String(prop.value)} highlight={filterValue} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {showPythonPopup && (
                <PythonEnvPopup
                    show={showPythonPopup}
                    python_env={pythonEnvData}
                    onClose={() => setShowPythonPopup(false)}
                />
            )}
        </>
    );
};

export default ExecutionCard;
