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

/**
 * Generic reusable detail drawer that slides in from the right.
 *
 * Props:
 *  - title          {string}      — Drawer heading (e.g. "Execution Details")
 *  - subtitle       {node}        — Sub-heading node rendered below the title
 *  - allProperties  {Array}       — [{ name, value }] full property list
 *  - onClose        {function}    — Called when overlay or ✕ is clicked
 *  - children       {node}        — Optional custom content rendered below properties
 *  - showAllProperties {boolean}  — Toggle All Properties section visibility
 */
const DetailDrawer = ({
    title,
    subtitle,
    allProperties = [],
    onClose,
    children,
    showAllProperties = true,
}) => {
    const [isFullscreen, setIsFullscreen] = useState(false);

    if (!onClose) return null;

    return (
        <>
            {/* Overlay */}
            <div
                className="fixed inset-0 bg-black bg-opacity-30 z-40"
                onClick={onClose}
            />

            {/* Drawer panel */}
            <div className={`fixed top-0 right-0 h-full w-full bg-white shadow-2xl z-50 flex flex-col transition-all duration-300 ${isFullscreen ? "max-w-none" : "max-w-2xl"}`}>
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-teal-50 to-white">
                    <div>
                        <h3 className="text-lg font-bold text-gray-900">{title}</h3>
                        {subtitle && (
                            <div className="text-sm text-gray-500 mt-1 leading-5">{subtitle}</div>
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setIsFullscreen((prev) => !prev)}
                            className="p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
                            title={isFullscreen ? "Exit full screen" : "Open full screen"}
                            aria-label={isFullscreen ? "Exit full screen" : "Open full screen"}
                        >
                            {isFullscreen ? (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 15H5v4m0 0l5-5m5 0l5 5m-5-5h4v4M9 9L4 4m0 0h4M4 4v4m11 1l5-5m0 0v4m0-4h-4" />
                                </svg>
                            ) : (
                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8V5a2 2 0 012-2h3M21 8V5a2 2 0 00-2-2h-3M3 16v3a2 2 0 002 2h3M21 16v3a2 2 0 01-2 2h-3" />
                                </svg>
                            )}
                        </button>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition"
                            title="Close"
                            aria-label="Close"
                        >
                            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path
                                    fillRule="evenodd"
                                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                    clipRule="evenodd"
                                />
                            </svg>
                        </button>
                    </div>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto px-6 py-4">
                    {showAllProperties && (
                        <>
                            {/* Divider + section title */}
                            <div className="border-t border-gray-200 mb-4">
                                <p className="text-xs font-semibold text-gray-400 uppercase mt-4 mb-3">Properties</p>
                            </div>

                            {/* All properties */}
                            <div className="space-y-2">
                                {allProperties.map((prop, idx) => (
                                    <div key={idx} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                                        <div className="text-xs font-semibold text-gray-500 uppercase mb-1">{prop.name}</div>
                                        <div className="text-sm text-gray-900 break-all">{prop.value}</div>
                                    </div>
                                ))}
                                {allProperties.length === 0 && (
                                    <p className="text-gray-400 text-sm text-center py-8">No properties available</p>
                                )}
                            </div>
                        </>
                    )}

                    {children && (
                        <div className="mt-6 border-t border-gray-200 pt-4">
                            {children}
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default DetailDrawer;
