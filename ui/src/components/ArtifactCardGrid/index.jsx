/***
 * Copyright (2026) Hewlett Packard Enterprise Development LP
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
import ModelCardPopup from "../ModelCardPopup";
import Highlight from "../Highlight";
import FastAPIClient from "../../client";
import config from "../../config";
import "./index.css";

const client = new FastAPIClient(config);

const ArtifactCardGrid = ({
    artifacts,
    artifactType,
    filterValue,
    onLabelClick,
    onArtifactClick,
    isSplitView = false,
    selectedItems = [],
    onToggleItem,
    selectedArtifactId = null,
}) => {
    const [expandedCard, setExpandedCard] = useState(null);
    const [showModelPopup, setShowModelPopup] = useState(false);
    const [popupData, setPopupData] = useState("");

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
            return "N/A";
        }

        const values = properties
            .filter(prop => prop.name === propertyName)
            .map(prop => prop.value);

        return values.length > 0 ? values.join(", ") : "N/A";
    };

    const toggleCard = (index) => {
        setExpandedCard(expandedCard === index ? null : index);
    };

    // Format date as 'YYYY-MM-DD HH:mm:ss' in UTC for display and search consistency
    const formatDate = (timestamp) => {
        if (!timestamp || timestamp === "N/A") return "N/A";
        try {
            const date = new Date(parseInt(timestamp, 10));
            // Pad single digit numbers with leading zeros for consistent formatting
            const pad = (n) => n.toString().padStart(2, '0');
            return `${date.getUTCFullYear()}-${pad(date.getUTCMonth() + 1)}-${pad(date.getUTCDate())} ` +
                   `${pad(date.getUTCHours())}:${pad(date.getUTCMinutes())}:${pad(date.getUTCSeconds())}`;
        } catch {
            return timestamp;
        }
    };

    const normalizeStepMetricsName = (value) => {
        const text = String(value || "");
        return text.toLowerCase().includes("training_metrics") ? "training_metrics" : text;
    };

    const getCardDisplayName = (artifact) => {
        const baseValue = artifact?.uri || artifact?.name || "N/A";
        return normalizeStepMetricsName(baseValue);
    };

    const renderLabels = (artifact) => {
        const labelsUri = getPropertyValue(artifact.artifact_properties, "labels_uri");

        if (!labelsUri || labelsUri === "N/A" || labelsUri.trim() === "") {
            return <span className="text-gray-500 text-sm">No labels</span>;
        }

        return (
            <div className="flex flex-wrap gap-1 mt-1">
                {labelsUri
                    .split(",")
                    .map((label_name) => label_name.trim())
                    .filter((label_name) => label_name.length > 0 && label_name !== "N/A")
                    .map((label_name, idx) => (
                        <span
                            key={idx}
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer max-w-[14rem] min-w-0 overflow-hidden"
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                if (onLabelClick) {
                                    onLabelClick(label_name, artifact);
                                }
                            }}
                            title={label_name}
                        >
                            <span className="block w-full truncate">
                                <Highlight text={label_name} highlight={filterValue} />
                            </span>
                        </span>
                    ))}
            </div>
        );
    };

    const getArtifactIcon = (type) => {
        switch (type) {
            case "Dataset":
                return (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M3 12v3c0 1.657 3.134 3 7 3s7-1.343 7-3v-3c0 1.657-3.134 3-7 3s-7-1.343-7-3z" />
                        <path d="M3 7v3c0 1.657 3.134 3 7 3s7-1.343 7-3V7c0 1.657-3.134 3-7 3S3 8.657 3 7z" />
                        <path d="M17 5c0 1.657-3.134 3-7 3S3 6.657 3 5s3.134-3 7-3 7 1.343 7 3z" />
                    </svg>
                );
            case "Model":
                return (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6 6V5a3 3 0 013-3h2a3 3 0 013 3v1h2a2 2 0 012 2v3.57A22.952 22.952 0 0110 13a22.95 22.95 0 01-8-1.43V8a2 2 0 012-2h2zm2-1a1 1 0 011-1h2a1 1 0 011 1v1H8V5zm1 5a1 1 0 011-1h.01a1 1 0 110 2H10a1 1 0 01-1-1z" clipRule="evenodd" />
                        <path d="M2 13.692V16a2 2 0 002 2h12a2 2 0 002-2v-2.308A24.974 24.974 0 0110 15c-2.796 0-5.487-.46-8-1.308z" />
                    </svg>
                );
            case "Metrics":
                return (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M2 11a1 1 0 011-1h2a1 1 0 011 1v5a1 1 0 01-1 1H3a1 1 0 01-1-1v-5zM8 7a1 1 0 011-1h2a1 1 0 011 1v9a1 1 0 01-1 1H9a1 1 0 01-1-1V7zM14 4a1 1 0 011-1h2a1 1 0 011 1v12a1 1 0 01-1 1h-2a1 1 0 01-1-1V4z" />
                    </svg>
                );
            default:
                return (
                    <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                );
        }
    };

    return (
        <>
            <div className={`grid gap-4 p-4 ${isSplitView ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"}`}>
                {artifacts.map((artifact, index) => (
                    <div
                        key={index}
                        className={`rounded-lg border-2 ${selectedArtifactId === artifact.artifact_id
                            ? 'bg-cyan-50 border-cyan-500 shadow-lg'
                            : selectedItems.some(a => a.artifact_id === artifact.artifact_id)
                                ? 'bg-teal-50 border-teal-500 shadow-lg'
                                : 'bg-white border-gray-300 hover:bg-teal-50 hover:border-teal-500 hover:shadow-lg'
                            } transition-all duration-200 overflow-hidden ${onArtifactClick ? 'cursor-pointer' : ''}`}
                        onClick={() => onArtifactClick && onArtifactClick(artifact)}
                    >
                        {/* Card Header */}
                        <div className="p-4 border-b border-gray-200">
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex items-center gap-3 flex-1 min-w-0">
                                    <div className="text-teal-600">
                                        {getArtifactIcon(artifactType)}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-semibold text-gray-500 uppercase">
                                                ID: <Highlight text={String(artifact.artifact_id)} highlight={filterValue} />
                                            </span>
                                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-teal-100 text-teal-800">
                                                {artifactType}
                                            </span>
                                        </div>
                                        <h3 className="text-sm font-bold text-gray-900 break-all line-clamp-2" title={getCardDisplayName(artifact)}>
                                            <span className="text-gray-500 font-semibold">URI: </span>
                                            {artifactType === "Label" && onLabelClick ? (
                                                <a
                                                    href="#"
                                                    onClick={(e) => {
                                                        e.preventDefault();
                                                        e.stopPropagation();
                                                        onLabelClick(artifact.name, artifact);
                                                    }}
                                                    className="text-teal-600 hover:text-teal-800 hover:underline"
                                                >
                                                    <Highlight text={getCardDisplayName(artifact)} highlight={filterValue} />
                                                </a>
                                            ) : (
                                                <Highlight text={getCardDisplayName(artifact)} highlight={filterValue} />
                                            )}
                                        </h3>
                                    </div>
                                </div>
                                {onToggleItem && (
                                    <input
                                        type="checkbox"
                                        title={
                                            selectedItems.some(a => a.artifact_id === artifact.artifact_id)
                                                ? "Deselect"
                                                : selectedItems.length >= 5
                                                    ? "Max 5 items can be selected"
                                                    : "Select for comparison"
                                        }
                                        checked={selectedItems.some(a => a.artifact_id === artifact.artifact_id)}
                                        disabled={
                                            !selectedItems.some(a => a.artifact_id === artifact.artifact_id) &&
                                            selectedItems.length >= 5
                                        }
                                        onChange={() => { }}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onToggleItem(artifact);
                                        }}
                                        className="w-4 h-4 mt-1 flex-shrink-0 accent-teal-600 cursor-pointer disabled:cursor-not-allowed disabled:opacity-40"
                                    />
                                )}
                            </div>
                        </div>

                        {/* Card Body */}
                        <div className="p-4 space-y-3">
                            {/* Date */}
                            <div className="flex items-center gap-2">
                                <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                                </svg>
                                <span className="text-xs text-gray-500">Created:</span>
                                <span className="text-sm font-medium text-gray-700">
                                    {formatDate(artifact.create_time_since_epoch)}
                                </span>
                            </div>

                            {/* Artifact Names from ExecutionLogs */}
                            {(() => {
                                const rawNames = artifact.execution_names;
                                const stripQuotes = n => typeof n === 'string' ? n.replace(/^"|"$/g, '') : n;
                                const names = Array.isArray(rawNames)
                                    ? rawNames.map(stripQuotes).filter(n => n && n !== 'null')
                                    : (typeof rawNames === 'string'
                                        ? (() => { try { const p = JSON.parse(rawNames); return Array.isArray(p) ? p.map(stripQuotes).filter(n => n && n !== 'null') : []; } catch { return []; } })()
                                        : []);
                                const uniqueDisplayNames = [...new Set(names.map((n) => normalizeStepMetricsName(n)))];
                                if (uniqueDisplayNames.length === 0) return null;
                                return (
                                    <div>
                                        <div className="flex flex-wrap gap-1.5">
                                            {uniqueDisplayNames.map((n, i) => (
                                                <span key={i} className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                                                    <Highlight text={n} highlight={filterValue} />
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })()}

                            {/* Labels for Dataset */}
                            {artifactType === "Dataset" && (
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-xs text-gray-500">Labels:</span>
                                    {renderLabels(artifact)}
                                </div>
                            )}

                            {/* Execution count badge */}
                            {artifact.execution_count != null && Number(artifact.execution_count) > 0 && (
                                <div className="flex items-center gap-2 pt-1">
                                    <div className="text-teal-600 flex-shrink-0">
                                        <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 24 24">
                                            <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                                        </svg>
                                    </div>
                                    <span className="text-xs text-gray-600">
                                        Linked in {" "}
                                        <span className="font-semibold text-emerald-700">
                                            {artifact.execution_count}
                                        </span>{" "}
                                        {Number(artifact.execution_count) === 1 ? "execution" : "executions"}
                                    </span>
                                </div>
                            )}

                            {/* Model Card Button */}
                            {artifactType === "Model" && (
                                <button
                                    className="w-full px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-md text-sm font-medium transition-colors shadow-sm hover:shadow mt-2"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        client.getModelCard(artifact.artifact_id).then((res) => {
                                            setPopupData(res);
                                            setShowModelPopup(true);
                                        });
                                    }}
                                >
                                    View Model Card
                                </button>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            {/* Model Card Popup */}
            {showModelPopup && (
                <ModelCardPopup
                    show={showModelPopup}
                    model_data={popupData}
                    onClose={() => setShowModelPopup(false)}
                />
            )}
        </>
    );
};

export default ArtifactCardGrid;
