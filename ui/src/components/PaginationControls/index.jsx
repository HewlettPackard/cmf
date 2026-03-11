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

import React from "react";

// Shared pagination component used by both artifacts_postgres_grid and executions_postgres_grid.

const PaginationControls = ({
    totalItems,
    activePage,
    onPageClick,
    onPrevClick,
    onNextClick,
    itemsPerPage = 6,
}) => {
    const totalPages = Math.ceil(totalItems / itemsPerPage);

    if (totalPages <= 1) return null;

    const getPageNumbers = () => {
        const pages = [];
        const maxVisible = 5;
        let start = Math.max(1, activePage - 2);
        let end = Math.min(totalPages, start + maxVisible - 1);
        if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
        }
        for (let i = start; i <= end; i++) {
            pages.push(i);
        }
        return pages;
    };

    return (
        <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 mt-4">
            <div className="text-sm text-gray-600">
                Page <span className="font-semibold">{activePage}</span> of{" "}
                <span className="font-semibold">{totalPages}</span>
                <span className="ml-2 text-gray-400">({totalItems} total)</span>
            </div>
            <div className="flex items-center gap-1">
                <button
                    onClick={onPrevClick}
                    disabled={activePage === 1}
                    className="px-3 py-1.5 rounded-md text-sm font-medium border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
                >
                    ← Prev
                </button>
                {getPageNumbers().map((page) => (
                    <button
                        key={page}
                        onClick={() => onPageClick(page)}
                        className={`px-3 py-1.5 rounded-md text-sm font-medium border transition ${activePage === page
                                ? "bg-teal-600 text-white border-teal-600 shadow-sm"
                                : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
                            }`}
                    >
                        {page}
                    </button>
                ))}
                <button
                    onClick={onNextClick}
                    disabled={activePage === totalPages}
                    className="px-3 py-1.5 rounded-md text-sm font-medium border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed transition"
                >
                    Next →
                </button>
            </div>
        </div>
    );
};

export default PaginationControls;
