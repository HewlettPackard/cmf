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

    const formatDate = (timestamp) => {
        if (!timestamp || timestamp === "N/A") return "N/A";
        try {
            const date = new Date(parseInt(timestamp));
            return date.toLocaleString();
        } catch {
            return timestamp;
        }
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
                            className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer max-w-full"
                            onClick={(e) => {
                                e.preventDefault();
                                e.stopPropagation();
                                if (onLabelClick) {
                                    onLabelClick(label_name, artifact);
                                }
                            }}
                            title={label_name}
                        >
                            <span className="truncate block max-w-full">
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
                        className={`bg-white rounded-lg border-2 ${selectedItems.some(a => a.artifact_id === artifact.artifact_id)
                                ? 'border-teal-500 shadow-lg'
                                : 'border-gray-300 hover:border-teal-500 hover:shadow-lg'
                            } transition-all duration-200 overflow-hidden ${onArtifactClick ? 'cursor-pointer' : ''}`}
                        onClick={() => onArtifactClick && onArtifactClick(artifact)}
                    >
                        {/* Card Header */}
                        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
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
                                        <h3 className="text-sm font-bold text-gray-900 break-all line-clamp-2" title={artifact.name}>
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
                                                    <Highlight text={String(artifact.name)} highlight={filterValue} />
                                                </a>
                                            ) : (
                                                <Highlight text={String(artifact.name)} highlight={filterValue} />
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

                            {/* URI */}
                            {artifact.uri && artifact.uri !== "N/A" && (
                                <div className="flex items-start gap-2">
                                    <svg className="w-4 h-4 text-gray-400 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M12.586 4.586a2 2 0 112.828 2.828l-3 3a2 2 0 01-2.828 0 1 1 0 00-1.414 1.414 4 4 0 005.656 0l3-3a4 4 0 00-5.656-5.656l-1.5 1.5a1 1 0 101.414 1.414l1.5-1.5zm-5 5a2 2 0 012.828 0 1 1 0 101.414-1.414 4 4 0 00-5.656 0l-3 3a4 4 0 105.656 5.656l1.5-1.5a1 1 0 10-1.414-1.414l-1.5 1.5a2 2 0 11-2.828-2.828l3-3z" clipRule="evenodd" />
                                    </svg>
                                    <div className="flex-1 min-w-0">
                                        <span className="text-xs text-gray-500 block">URI:</span>
                                        <span className="text-sm text-gray-900 break-all">
                                            <Highlight text={String(artifact.uri)} highlight={filterValue} />
                                        </span>
                                    </div>
                                </div>
                            )}

                            {/* Git Info */}
                            {(getPropertyValue(artifact.artifact_properties, "git_repo") !== "N/A" ||
                                getPropertyValue(artifact.artifact_properties, "Commit") !== "N/A") && (
                                    <div className="flex flex-wrap gap-2">
                                        {getPropertyValue(artifact.artifact_properties, "git_repo") !== "N/A" && (
                                            <div className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-purple-50 border border-purple-200 rounded-md max-w-full">
                                                <svg className="w-3.5 h-3.5 text-purple-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M12.316 3.051a1 1 0 01.633 1.265l-4 12a1 1 0 11-1.898-.632l4-12a1 1 0 011.265-.633zM5.707 6.293a1 1 0 010 1.414L3.414 10l2.293 2.293a1 1 0 11-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0zm8.586 0a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 11-1.414-1.414L16.586 10l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
                                                </svg>
                                                <span className="text-xs text-purple-700 truncate" title={getPropertyValue(artifact.artifact_properties, "git_repo")}>
                                                    <Highlight text={getPropertyValue(artifact.artifact_properties, "git_repo")} highlight={filterValue} />
                                                </span>
                                            </div>
                                        )}
                                        {getPropertyValue(artifact.artifact_properties, "Commit") !== "N/A" && (
                                            <div className="inline-flex items-center gap-1.5 px-2.5 py-1.5 bg-green-50 border border-green-200 rounded-md">
                                                <svg className="w-3.5 h-3.5 text-green-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                                    <path fillRule="evenodd" d="M10 6a4 4 0 100 8 4 4 0 000-8zM2 9a1 1 0 000 2h4.126a6 6 0 000-2H2zm11.874 0a6 6 0 000 2H18a1 1 0 100-2h-4.126z" clipRule="evenodd" />
                                                </svg>
                                                <span className="text-xs text-green-700 font-mono truncate" title={getPropertyValue(artifact.artifact_properties, "Commit")}>
                                                    <Highlight text={getPropertyValue(artifact.artifact_properties, "Commit")} highlight={filterValue} />
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                )}

                            {/* Labels for Dataset */}
                            {artifactType === "Dataset" && (
                                <div>
                                    <span className="text-xs text-gray-500 block mb-1">Labels:</span>
                                    {renderLabels(artifact)}
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

                        {/* Card Footer - Expandable Properties */}
                        <div className="border-t border-gray-200">
                            <button
                                onClick={(e) => { e.stopPropagation(); toggleCard(index); }}
                                className="w-full px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-between"
                            >
                                <span className="flex items-center gap-2">
                                    <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                                        <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd" />
                                    </svg>
                                    View All Properties ({artifact.artifact_properties?.length || 0})
                                </span>
                                <svg
                                    className={`w-5 h-5 text-gray-400 transition-transform ${expandedCard === index ? 'transform rotate-180' : ''
                                        }`}
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                >
                                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>

                            {expandedCard === index && (
                                <div className="px-4 pb-4 max-h-64 overflow-y-auto bg-gray-50">
                                    <div className="space-y-2">
                                        {artifact.artifact_properties?.map((property, idx) => (
                                            <div
                                                key={idx}
                                                className="bg-white rounded p-2 border border-gray-200"
                                            >
                                                <div className="text-xs font-semibold text-gray-500 uppercase mb-1">
                                                    <Highlight text={String(property.name)} highlight={filterValue} />
                                                </div>
                                                <div className="text-sm text-gray-900 break-all">
                                                    <Highlight text={String(property.value)} highlight={filterValue} />
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
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
