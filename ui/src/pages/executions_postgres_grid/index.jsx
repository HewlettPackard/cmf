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

import React, { useEffect, useState } from "react";
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import Footer from "../../components/Footer";
import Sidebar from "../../components/Sidebar";
import ExecutionCard from "../../components/ExecutionCardGrid";
import DetailDrawer from "../../components/DetailDrawer";
import PaginationControls from "../../components/PaginationControls";
import CompareModal from "../../components/CompareModal";

const client = new FastAPIClient(config);

const ITEMS_PER_PAGE = 6;

const ExecutionsPostgresGrid = () => {
    const [pipelines, setPipelines] = useState([]);
    const [selectedPipeline, setSelectedPipeline] = useState(null);
    const [stages, setStages] = useState([]);
    const [totalStages, setTotalStages] = useState(0);
    const [selectedStage, setSelectedStage] = useState(null);
    const [executions, setExecutions] = useState([]);
    const [totalItems, setTotalItems] = useState(0);
    const [activePage, setActivePage] = useState(1);
    const [filter, setFilter] = useState("");
    const [sortOrder, setSortOrder] = useState("desc");
    const [selectedExecution, setSelectedExecution] = useState(null);

    // Compare feature
    const [selectedExecutions, setSelectedExecutions] = useState([]);
    const [showCompareModal, setShowCompareModal] = useState(false);

    // Fetch pipelines on mount
    useEffect(() => {
        client.getPipelines("").then((data) => {
            setPipelines(data);
            if (data.length > 0) {
                setSelectedPipeline(data[0]);
            }
        });
    }, []);

    // Fetch execution stages when pipeline changes
    useEffect(() => {
        if (selectedPipeline) {
            client.getPipelineStages(selectedPipeline).then((data) => {
                const allStages = data.stages || [];
                setStages(allStages);
                setTotalStages(data.total_stages || 0);
                setSelectedStage(allStages.length > 0 ? allStages[0] : null);
                setExecutions([]);
                setTotalItems(0);
                setActivePage(1);
            }).catch(() => {
                setStages([]);
                setTotalStages(0);
                setSelectedStage(null);
                setExecutions([]);
                setTotalItems(0);
            });
        }
    }, [selectedPipeline]);

    // Fetch executions when stage, page, sort, or filter changes
    useEffect(() => {
        if (selectedPipeline && selectedStage) {
            client
                .getExecutionsByStage(selectedPipeline, selectedStage, activePage, ITEMS_PER_PAGE, sortOrder, filter)
                .then((data) => {
                    setExecutions(data.items || []);
                    setTotalItems(data.total_items || 0);
                })
                .catch(() => {
                    setExecutions([]);
                    setTotalItems(0);
                });
        }
    }, [selectedStage, activePage, sortOrder, filter]);

    // Handlers
    const handlePipelineClick = (pipeline) => {
        setSelectedPipeline(pipeline);
        setSelectedStage(null);
        setExecutions([]);
        setActivePage(1);
        setSelectedExecution(null);
        setSelectedExecutions([]);
    };

    const handleStageClick = (stage) => {
        setSelectedStage(stage);
        setExecutions([]);
        setActivePage(1);
        setSelectedExecution(null);
        setSelectedExecutions([]);
    };

    const handlePageClick = (page) => {
        setActivePage(page);
    };

    const handlePrevClick = () => {
        if (activePage > 1) setActivePage((p) => p - 1);
    };

    const handleNextClick = () => {
        if (activePage < Math.ceil(totalItems / ITEMS_PER_PAGE))
            setActivePage((p) => p + 1);
    };

    const handleFilter = (value) => {
        setFilter(value);
        setActivePage(1);
    };

    const handleToggleExecution = (execution) => {
        setSelectedExecutions((prev) => {
            const isAlreadySelected = prev.some(e => e.execution_id === execution.execution_id);
            if (isAlreadySelected) return prev.filter(e => e.execution_id !== execution.execution_id);
            if (prev.length >= 5) return prev;
            return [...prev, execution];
        });
    };

    const executionDetailProperties = selectedExecution
        ? (Array.isArray(selectedExecution.execution_properties)
            ? selectedExecution.execution_properties
            : (() => {
                try {
                    return JSON.parse(selectedExecution.execution_properties || "[]");
                } catch {
                    return [];
                }
            })())
        : [];

    const getExecutionDetailProperty = (name) => {
        const matchedValues = executionDetailProperties
            .filter((property) => property.name === name)
            .map((property) => property.value);
        return matchedValues.length > 0 ? matchedValues.join(", ") : "N/A";
    };

    const executionDetailSummaryFields = selectedExecution ? [
        { label: "Context Type", value: getExecutionDetailProperty("Context_Type"), color: "teal" },
        { label: "Execution", value: getExecutionDetailProperty("Execution"), color: "blue" },
        { label: "Pipeline Type", value: getExecutionDetailProperty("Pipeline_Type"), color: "indigo" },
        { label: "Git Repo", value: getExecutionDetailProperty("Git_Repo"), color: "purple" },
        { label: "Git Start Commit", value: getExecutionDetailProperty("Git_Start_Commit"), color: "green" },
    ] : [];

    // Render
    return (
        <>
            <section className="flex flex-col bg-white min-h-screen">
                <DashboardHeader />
                <div className="flex flex-row flex-grow">
                    {/* Sidebar */}
                    <div className="min-h-screen bg-gray-50 w-1/5 flex-grow-0 shadow-sm border-r border-gray-200">
                        <Sidebar
                            pipelines={pipelines}
                            selectedPipeline={selectedPipeline}
                            stages={stages}
                            selectedStage={selectedStage}
                            handlePipelineClick={handlePipelineClick}
                            handleStageClick={handleStageClick}
                            className="flex-grow"
                        />
                    </div>

                    {/* Main Content */}
                    <div className="w-4/5 px-8 py-6 flex-grow bg-white">
                        {selectedPipeline && (
                            <>
                                {/* Header */}
                                <div className="mb-8">
                                    <div className="flex items-center justify-between mb-6">
                                        <h2 className="text-2xl font-bold text-gray-900">
                                            Executions -{" "}
                                            {selectedStage
                                                ? selectedStage.split("/").pop() || selectedStage
                                                : "All Stages"}
                                        </h2>
                                        <div className="flex gap-6 text-sm bg-gray-50 rounded-lg px-4 py-2.5 border border-gray-200">
                                            <span className="text-gray-600">
                                                Total:{" "}
                                                <span className="text-gray-900 font-bold text-base">
                                                    {totalItems}
                                                </span>
                                            </span>
                                            <span className="text-gray-300">|</span>
                                            <span className="text-gray-600">
                                                Stages:{" "}
                                                <span className="text-gray-900 font-bold text-base">
                                                    {totalStages}
                                                </span>
                                            </span>
                                        </div>
                                    </div>

                                    {/* Sort + Search Row */}
                                    {selectedStage && (
                                        <div className="mb-6 flex items-center gap-3">
                                            <label htmlFor="exec-sort" className="text-sm font-bold text-gray-700 whitespace-nowrap">Sort by:</label>
                                            <select
                                                id="exec-sort"
                                                value={`time__${sortOrder}`}
                                                onChange={(e) => {
                                                    const [, order] = e.target.value.split("__");
                                                    setSortOrder(order);
                                                    setActivePage(1);
                                                }}
                                                className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-bold text-gray-700 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 cursor-pointer"
                                            >
                                                <option value="time__asc">Time: Oldest First ↑</option>
                                                <option value="time__desc">Time: Latest First ↓</option>
                                            </select>

                                            <button
                                                onClick={() => setShowCompareModal(true)}
                                                disabled={selectedExecutions.length < 2}
                                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold border transition-all shadow-sm ${selectedExecutions.length >= 2
                                                    ? 'bg-teal-600 text-white border-teal-600 hover:bg-teal-700'
                                                    : 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                                                    }`}
                                                title={selectedExecutions.length < 2 ? 'Select at least 2 executions to compare' : `Compare ${selectedExecutions.length} executions`}
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                                </svg>
                                                Compare{selectedExecutions.length >= 2 ? ` (${selectedExecutions.length})` : ''}
                                            </button>

                                            {selectedExecutions.length > 0 && (
                                                <span className="text-xs text-gray-500">
                                                    {selectedExecutions.length}/5 selected
                                                </span>
                                            )}

                                            <div className="relative ml-auto w-64">
                                                <input
                                                    type="text"
                                                    value={filter}
                                                    onChange={(e) => handleFilter(e.target.value)}
                                                    placeholder="Filter by Context Type / Properties..."
                                                    className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 shadow-sm transition text-sm"
                                                />
                                                <svg
                                                    className="absolute left-3 top-2.5 w-4 h-4 text-gray-400"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                                                </svg>
                                                {filter && (
                                                    <button
                                                        onClick={() => handleFilter("")}
                                                        className="absolute right-3 top-2 text-gray-400 hover:text-gray-600"
                                                    >
                                                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                                        </svg>
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {/* Execution Cards Grid */}
                                {selectedStage ? (
                                    executions.length > 0 ? (
                                        <>
                                            <div className="grid gap-4 p-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                                                {executions.map((execution, index) => (
                                                    <ExecutionCard
                                                        key={execution.execution_id || index}
                                                        execution={execution}
                                                        filterValue={filter}
                                                        onCardClick={setSelectedExecution}
                                                        isSelected={selectedExecutions.some(e => e.execution_id === execution.execution_id)}
                                                        onToggle={handleToggleExecution}
                                                    />
                                                ))}
                                            </div>
                                            <PaginationControls
                                                totalItems={totalItems}
                                                activePage={activePage}
                                                onPageClick={handlePageClick}
                                                onPrevClick={handlePrevClick}
                                                onNextClick={handleNextClick}
                                                itemsPerPage={ITEMS_PER_PAGE}
                                            />
                                        </>
                                    ) : (
                                        <div className="text-center py-16">
                                            <div className="text-gray-400 mb-3">
                                                <svg
                                                    className="w-16 h-16 mx-auto"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    viewBox="0 0 24 24"
                                                >
                                                    <path
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        strokeWidth={1.5}
                                                        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                                                    />
                                                </svg>
                                            </div>
                                            <p className="text-gray-500 text-base font-medium">
                                                {filter
                                                    ? "No executions match the current filter"
                                                    : "No executions found for this stage"}
                                            </p>
                                        </div>
                                    )
                                ) : (
                                    <div className="text-center py-16">
                                        <p className="text-gray-500 text-base font-medium">
                                            Please select a stage to view executions
                                        </p>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
                <Footer />
            </section>

            {/* Execution Detail Drawer (slide-in on card click) */}
            {selectedExecution && (
                <DetailDrawer
                    title="Execution Details"
                    subtitle={<>ID: <span className="font-mono font-semibold">{selectedExecution.execution_id || "—"}</span></>}
                    summaryFields={executionDetailSummaryFields}
                    allProperties={executionDetailProperties}
                    onClose={() => setSelectedExecution(null)}
                />
            )}

            {/* Compare Modal */}
            {showCompareModal && selectedExecutions.length >= 2 && (
                <CompareModal
                    items={selectedExecutions}
                    itemType="execution"
                    onClose={() => setShowCompareModal(false)}
                />
            )}
        </>
    );
};

export default ExecutionsPostgresGrid;
