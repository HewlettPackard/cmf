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

import React from "react";

/**
 * CompareModal
 *   items    — array of artifact or execution objects to compare
 *   itemType — "artifact" | "execution"
 *   onClose  — close handler
 */
const CompareModal = ({ items, itemType, onClose }) => {
    const propsKey =
        itemType === "artifact" ? "artifact_properties" : "execution_properties";

    const getProps = (item) => {
        const p = item[propsKey];
        return Array.isArray(p) ? p : [];
    };

    const getPropValue = (item, key) => {
        const match = getProps(item)
            .filter((p) => p.name === key)
            .map((p) => p.value);
        return match.length > 0 ? match.join(", ") : "—";
    };

    // All unique property keys across all items
    const allKeys = Array.from(
        new Set(items.flatMap((item) => getProps(item).map((p) => p.name)))
    );

    const getItemTitle = (item) =>
        itemType === "artifact"
            ? item.name || `Artifact #${item.artifact_id}`
            : getPropValue(item, "Context_Type") || `Execution #${item.execution_id}`;

    const coreFields =
        itemType === "artifact"
            ? [
                { label: "ID", fn: (i) => i.artifact_id },
                { label: "Name", fn: (i) => i.name },
                { label: "URI", fn: (i) => i.uri || "—" },
            ]
            : [
                { label: "ID", fn: (i) => i.execution_id },
                { label: "Context Type", fn: (i) => getPropValue(i, "Context_Type") },
            ];

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-xl shadow-2xl w-11/12 max-w-6xl max-h-[90vh] flex flex-col"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 flex-shrink-0">
                    <div>
                        <h2 className="text-lg font-bold text-gray-900">
                            Compare {itemType === "artifact" ? "Artifacts" : "Executions"}
                        </h2>
                        <p className="text-sm text-gray-500">
                            {items.length} item{items.length !== 1 ? "s" : ""} selected
                            &nbsp;:&nbsp;
                            <span className="text-yellow-600 font-medium">Yellow rows</span> indicate differing values
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded-lg hover:bg-gray-100"
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

                {/* Table */}
                <div className="overflow-auto flex-1 p-6">
                    <table className="w-full border-collapse text-sm">
                        <tbody>
                            {/* Core fields */}
                            {coreFields.map(({ label, fn }) => (
                                <tr key={label} className="hover:bg-gray-50">
                                    <td className="px-4 py-2 border border-gray-200 font-medium text-gray-600 bg-gray-50 sticky left-0 z-10">
                                        {label}
                                    </td>
                                    {items.map((item, idx) => (
                                        <td
                                            key={idx}
                                            className="px-4 py-2 border border-gray-200 text-gray-900 break-all"
                                        >
                                            {String(fn(item))}
                                        </td>
                                    ))}
                                </tr>
                            ))}

                            {/* Properties section header */}
                            {allKeys.length > 0 && (
                                <tr>
                                    <td
                                        colSpan={items.length + 1}
                                        className="px-4 py-1.5 bg-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider border border-gray-200"
                                    >
                                        Properties
                                    </td>
                                </tr>
                            )}

                            {/* Dynamic properties */}
                            {allKeys.map((key) => {
                                const values = items.map((item) => getPropValue(item, key));
                                const allSame = values.every((v) => v === values[0]);
                                return (
                                    <tr
                                        key={key}
                                        className={`hover:bg-opacity-80 ${!allSame ? "bg-yellow-50" : "hover:bg-gray-50"}`}
                                    >
                                        <td className="px-4 py-2 border border-gray-200 font-medium text-gray-600 bg-gray-50 sticky left-0 z-10">
                                            {key}
                                        </td>
                                        {values.map((val, idx) => (
                                            <td
                                                key={idx}
                                                className={`px-4 py-2 border border-gray-200 break-all ${!allSame
                                                    ? "text-orange-700 font-medium"
                                                    : "text-gray-900"
                                                    }`}
                                            >
                                                {val}
                                            </td>
                                        ))}
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* Footer */}
                <div className="px-6 py-3 border-t border-gray-200 flex-shrink-0 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                    >
                        Close
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CompareModal;
