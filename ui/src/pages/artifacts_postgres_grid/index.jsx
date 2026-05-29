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
import { useSearchParams } from "react-router-dom";
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import ArtifactCardGrid from "../../components/ArtifactCardGrid";
import DetailDrawer from "../../components/DetailDrawer";
import Footer from "../../components/Footer";
import Sidebar from "../../components/Sidebar";
import LabelContentPanel from "./components/LabelContentPanel";
import ResizableSplitPane from "../../components/ResizableSplitPane";
import PaginationControls from "../../components/PaginationControls";
import CompareModal from "../../components/CompareModal";
import Papa from "papaparse";

const client = new FastAPIClient(config);

const ArtifactsPostgres = () => {
    const [searchParams] = useSearchParams();
    const [selectedPipeline, setSelectedPipeline] = useState(null);
    const [pipelines, setPipelines] = useState([]);
    const [stages, setStages] = useState([]);
    const [totalStages, setTotalStages] = useState(0);
    const [selectedStage, setSelectedStage] = useState(null);
    const [artifactTypes, setArtifactTypes] = useState([]);
    const [selectedArtifactType, setSelectedArtifactType] = useState(null);
    const [artifacts, setArtifacts] = useState([]);
    const [filter, setFilter] = useState("");
    const [totalItems, setTotalItems] = useState(0);
    const [activePage, setActivePage] = useState(1);
    const [sortOrder, setSortOrder] = useState("desc");
    const [selectedCol, setSelectedCol] = useState("create_time_since_epoch");

    // Artifact detail drawer state
    const [selectedArtifact, setSelectedArtifact] = useState(null);

    // Label content panel states
    const [selectedTableLabel, setSelectedTableLabel] = useState(null);
    const [labelContentLoading, setLabelContentLoading] = useState(false);
    const [labelData, setLabelData] = useState(null);
    const [parsedLabelData, setParsedLabelData] = useState([]);
    const [labelColumns, setLabelColumns] = useState([]);
    const [labelCurrentPage, setLabelCurrentPage] = useState(0);
    const [labelRowsPerPage, setLabelRowsPerPage] = useState(10);

    // Compare feature
    const [selectedArtifacts, setSelectedArtifacts] = useState([]);
    const [showCompareModal, setShowCompareModal] = useState(false);

    useEffect(() => {
        fetchPipelines();
    }, []);

    const fetchPipelines = () => {
        client.getPipelines("").then((data) => {
            setPipelines(data);
            const pipelineParam = searchParams.get("pipeline");
            if (pipelineParam && data.includes(pipelineParam)) {
                setSelectedPipeline(pipelineParam);
            } else if (data.length > 0) {
                setSelectedPipeline(data[0]);
            }
        });
    };

    useEffect(() => {
        if (selectedPipeline) {
            fetchStagesByPipelineName(selectedPipeline);
        }
    }, [selectedPipeline]);

    // Fetch stages from the backend for the selected pipeline name.
    const fetchStagesByPipelineName = (pipeline_name) => {
        client.getPipelineStages(pipeline_name).then((data) => {
            console.log("Artifact Stages Data:", data);
            const allStages = data.stages || [];
            setStages(allStages);
            setTotalStages(data.total_stages || 0);

            // Auto-select the first returned stage.
            if (allStages.length > 0) {
                setSelectedStage(allStages[0]);
            } else {
                setSelectedStage(null);
                setArtifactTypes([]);
                setSelectedArtifactType(null);
            }
        });
    };

    useEffect(() => {
        if (selectedPipeline && selectedStage) {
            fetchArtifactTypesByStage(selectedPipeline, selectedStage);
        }
    }, [selectedStage]);

    const fetchArtifactTypesByStage = (pipelineName, stageName) => {
        client.getArtifactTypesByStage(pipelineName, stageName).then((types) => {
            console.log("Artifact Types for Stage:", types);
            setArtifactTypes(types);
            if (types.length > 0) {
                setSelectedArtifactType(types[0]);
            } else {
                setSelectedArtifactType(null);
                setArtifacts([]);
                setTotalItems(0);
            }
        }).catch((error) => {
            console.error("Error fetching artifact types:", error);
            setArtifactTypes([]);
            setSelectedArtifactType(null);
            setArtifacts([]);
        });
    };

    useEffect(() => {
        if (selectedPipeline && selectedStage && selectedArtifactType) {
            fetchArtifactsByStage(selectedPipeline, selectedStage, selectedArtifactType, sortOrder, activePage, filter, selectedCol);
        }
    }, [selectedArtifactType, sortOrder, activePage, selectedCol, filter]);

    // Fetch artifacts from the backend based on selected pipeline, stage, and artifact type, along with pagination, sorting, and filtering parameters.
    const fetchArtifactsByStage = (pipelineName, stageName, artifactType, sortOrder, activePage, filter = "", selectedCol) => {
        client.getArtifactsByStage(pipelineName, stageName, artifactType, sortOrder, activePage, 6, filter, selectedCol)
            .then((data) => {
                setArtifacts(data.items);
                setTotalItems(data.total_items);
            }).catch((error) => {
                console.error("Error fetching artifacts by stage:", error);
                setArtifacts([]);
                setTotalItems(0);
            });
    };

    const handlePipelineClick = (pipeline) => {
        setSelectedPipeline(pipeline);
        setSelectedStage(null);
        setArtifactTypes([]);
        setSelectedArtifactType(null);
        setArtifacts([]);
        setActivePage(1);
        setSelectedArtifacts([]);
    };

    const handleStageClick = (stage) => {
        setSelectedStage(stage);
        setSelectedArtifactType(null);
        setArtifacts([]);
        setActivePage(1);
        setSelectedArtifacts([]);
    };

    const handleArtifactTypeClick = (artifactType) => {
        if (selectedArtifactType !== artifactType) {
            setArtifacts(null);
            // Reset label panel state when switching artifact types
            setSelectedTableLabel(null);
            setLabelData(null);
            setParsedLabelData([]);
            setLabelColumns([]);
        }
        setSelectedArtifactType(artifactType);
        setActivePage(1);
        setSelectedArtifacts([]);
    };

    const handleArtifactCardClick = (artifact) => {
        setSelectedArtifact(artifact);
    };

    const handleFilter = (value) => {
        setFilter(value);
        setActivePage(1);
    };

    const handleToggleArtifact = (artifact) => {
        setSelectedArtifacts((prev) => {
            const isAlreadySelected = prev.some(a => a.artifact_id === artifact.artifact_id);
            if (isAlreadySelected) return prev.filter(a => a.artifact_id !== artifact.artifact_id);
            if (prev.length >= 5) return prev;
            return [...prev, artifact];
        });
    };

    const handlePageClick = (page) => {
        setActivePage(page);
    };

    const handlePrevClick = () => {
        if (activePage > 1) setActivePage(activePage - 1);
    };

    const handleNextClick = () => {
        if (activePage < Math.ceil(totalItems / 6)) setActivePage(activePage + 1);
    };

    const handleLabelClick = (labelName, artifact) => {
        setSelectedTableLabel({ name: labelName, ...artifact });
        setLabelContentLoading(true);
        setLabelCurrentPage(0);

        const labelId = labelName.includes(":") ? labelName.split(":")[1] : labelName;

        client.getLabelData(labelId).then((csvData) => {
            setLabelData(csvData);
            console.log("label CSV data = ", csvData);

            if (csvData && typeof csvData === 'string' && csvData.trim().length > 0) {
                const parsed = Papa.parse(csvData, { header: true });
                console.log("parsed data = ", parsed.data);

                if (parsed.data && parsed.data.length > 0) {
                    setParsedLabelData(parsed.data);
                    if (parsed.meta.fields) {
                        const columns = parsed.meta.fields.map(field => ({ name: field }));
                        console.log("columns = ", columns);
                        setLabelColumns(columns);
                    }
                } else {
                    setParsedLabelData([]);
                    setLabelColumns([]);
                }
            } else {
                setParsedLabelData([]);
                setLabelColumns([]);
            }
            setLabelContentLoading(false);
        }).catch((error) => {
            console.error("Error fetching label data:", error);
            setLabelContentLoading(false);
            setParsedLabelData([]);
            setLabelColumns([]);
        });
    };

    const artifactDetailProperties = selectedArtifact
        ? (Array.isArray(selectedArtifact.artifact_properties)
            ? selectedArtifact.artifact_properties
            : (() => {
                try {
                    return JSON.parse(selectedArtifact.artifact_properties || "[]");
                } catch {
                    return [];
                }
            })())
        : [];

    const getArtifactDetailProperty = (name) => {
        const matchedValues = artifactDetailProperties
            .filter((property) => property.name === name)
            .map((property) => property.value);
        return matchedValues.length > 0 ? matchedValues.join(", ") : "N/A";
    };

    const formatArtifactDetailDate = (timestamp) => {
        if (!timestamp || timestamp === "N/A") return "N/A";
        try {
            return new Date(parseInt(timestamp)).toLocaleString();
        } catch {
            return timestamp;
        }
    };

    const artifactDetailSummaryFields = selectedArtifact ? [
        { label: "Type", value: selectedArtifactType, color: "teal" },
        { label: "URI", value: selectedArtifact.uri, color: "blue" },
        { label: "Created", value: formatArtifactDetailDate(selectedArtifact.create_time_since_epoch), color: "indigo" },
        { label: "Git Repo", value: getArtifactDetailProperty("git_repo"), color: "purple" },
        { label: "Commit", value: getArtifactDetailProperty("Commit"), color: "green" },
    ] : [];

    return (
        <>
            <section className="flex flex-col bg-white min-h-screen">
                <DashboardHeader />
                <div className="flex flex-row flex-grow">
                    <div className="sidebar-container min-h-screen bg-gray-50 w-1/5 flex-grow-0 shadow-sm border-r border-gray-200">
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
                    <div className="w-4/5 px-8 py-6 flex-grow bg-white">
                        {selectedPipeline && (
                            <>
                                {/* Header Section */}
                                <div className="mb-8">
                                    <div className="flex items-center justify-between mb-6">
                                        <h2 className="text-2xl font-bold text-gray-900">
                                            Artifacts - {selectedStage ? selectedStage.split('/').pop() || selectedStage : 'All Stages'}
                                        </h2>
                                        <div className="flex gap-6 text-sm bg-gray-50 rounded-lg px-4 py-2.5 border border-gray-200">
                                            <span className="text-gray-600">
                                                Total: <span className="text-gray-900 font-bold text-base">{totalItems}</span>
                                            </span>
                                            <span className="text-gray-300">|</span>
                                            <span className="text-gray-600">
                                                Stages: <span className="text-gray-900 font-bold text-base">{totalStages}</span>
                                            </span>
                                        </div>
                                    </div>

                                    {/* Artifact Type Selection */}
                                    {selectedStage && artifactTypes.length > 0 && (
                                        <div className="mb-6">
                                            <div className="flex gap-3 flex-wrap">
                                                {artifactTypes.map((artifactType) => (
                                                    <button
                                                        key={artifactType}
                                                        onClick={() => handleArtifactTypeClick(artifactType)}
                                                        className={`px-6 py-2.5 rounded-lg font-medium transition-all shadow-sm ${selectedArtifactType === artifactType
                                                            ? 'bg-teal-600 text-white shadow-md'
                                                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-teal-400'
                                                            }`}
                                                    >
                                                        {artifactType}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Sort + Search Row */}
                                    {selectedStage && selectedArtifactType && (
                                        <div className="mb-6 flex items-center gap-3">
                                            <label htmlFor="artifact-sort" className="text-sm font-bold text-gray-700 whitespace-nowrap">Sort by:</label>
                                            <select
                                                id="artifact-sort"
                                                value={`${selectedCol}__${sortOrder}`}
                                                onChange={(e) => {
                                                    const [field, order] = e.target.value.split("__");
                                                    setSelectedCol(field);
                                                    setSortOrder(order);
                                                    setActivePage(1);
                                                }}
                                                className="px-3 py-2 border border-gray-300 rounded-lg text-sm font-bold text-gray-700 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500 cursor-pointer"
                                            >
                                                <option value="name__asc">Name: A → Z ↑</option>
                                                <option value="name__desc">Name: Z → A ↓</option>
                                                <option value="create_time_since_epoch__asc">Time: Oldest First ↑</option>
                                                <option value="create_time_since_epoch__desc">Time: Latest First ↓</option>
                                            </select>

                                            <button
                                                onClick={() => setShowCompareModal(true)}
                                                disabled={selectedArtifacts.length < 2}
                                                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold border transition-all shadow-sm ${selectedArtifacts.length >= 2
                                                    ? 'bg-teal-600 text-white border-teal-600 hover:bg-teal-700'
                                                    : 'bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                                                    }`}
                                                title={selectedArtifacts.length < 2 ? 'Select at least 2 artifacts to compare' : `Compare ${selectedArtifacts.length} artifacts`}
                                            >
                                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                                </svg>
                                                Compare{selectedArtifacts.length >= 2 ? ` (${selectedArtifacts.length})` : ''}
                                            </button>

                                            {selectedArtifacts.length > 0 && (
                                                <span className="text-xs text-gray-500">
                                                    {selectedArtifacts.length}/5 selected
                                                </span>
                                            )}

                                            <div className="relative ml-auto w-64">
                                                <input
                                                    type="text"
                                                    value={filter}
                                                    onChange={(e) => handleFilter(e.target.value)}
                                                    placeholder="Filter by Name/Properties..."
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
                                                        onClick={() => handleFilter('')}
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

                                {/* Artifacts Content */}
                                {selectedStage && selectedArtifactType && (
                                    selectedArtifactType === "Label" ? (
                                        // Resizable split view for Label artifact type
                                        <ResizableSplitPane
                                            initialSplitPercentage={50}
                                            minPercentage={50}
                                            maxPercentage={50}
                                            leftContent={
                                                <div>
                                                    {artifacts !== null && artifacts.length > 0 ? (
                                                        <>
                                                            <ArtifactCardGrid
                                                                artifacts={artifacts}
                                                                artifactType={selectedArtifactType}
                                                                filterValue={filter}
                                                                onLabelClick={handleLabelClick}
                                                                onArtifactClick={handleArtifactCardClick}
                                                                isSplitView={true} selectedItems={selectedArtifacts}
                                                                onToggleItem={handleToggleArtifact} />
                                                            <PaginationControls
                                                                totalItems={totalItems}
                                                                activePage={activePage}
                                                                onPageClick={handlePageClick}
                                                                onPrevClick={handlePrevClick}
                                                                onNextClick={handleNextClick}
                                                                itemsPerPage={6}
                                                            />
                                                        </>
                                                    ) : (
                                                        <div className="text-center py-16">
                                                            <div className="text-gray-400 mb-3">
                                                                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                                                                </svg>
                                                            </div>
                                                            <p className="text-gray-500 text-base font-medium">No artifacts found</p>
                                                        </div>
                                                    )}
                                                </div>
                                            }
                                            rightContent={
                                                <LabelContentPanel
                                                    selectedTableLabel={selectedTableLabel}
                                                    labelContentLoading={labelContentLoading}
                                                    labelData={labelData}
                                                    parsedLabelData={parsedLabelData}
                                                    labelColumns={labelColumns}
                                                    currentPage={labelCurrentPage}
                                                    rowsPerPage={labelRowsPerPage}
                                                    setCurrentPage={setLabelCurrentPage}
                                                    setRowsPerPage={setLabelRowsPerPage}
                                                />
                                            }
                                        />
                                    ) : (
                                        // Standard view for other artifact types
                                        <div>
                                            {artifacts !== null && artifacts.length > 0 ? (
                                                <>
                                                    <ArtifactCardGrid
                                                        artifacts={artifacts}
                                                        artifactType={selectedArtifactType}
                                                        filterValue={filter}
                                                        onArtifactClick={handleArtifactCardClick}
                                                        selectedItems={selectedArtifacts}
                                                        onToggleItem={handleToggleArtifact}
                                                    />
                                                    <PaginationControls
                                                        totalItems={totalItems}
                                                        activePage={activePage}
                                                        onPageClick={handlePageClick}
                                                        onPrevClick={handlePrevClick}
                                                        onNextClick={handleNextClick}
                                                        itemsPerPage={6}
                                                    />
                                                </>
                                            ) : (
                                                <div className="text-center py-16">
                                                    <div className="text-gray-400 mb-3">
                                                        <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                                                        </svg>
                                                    </div>
                                                    <p className="text-gray-500 text-base font-medium">No artifacts found</p>
                                                </div>
                                            )}
                                        </div>
                                    )
                                )}

                                {!selectedStage && (
                                    <div className="text-center py-16">
                                        <p className="text-gray-500 text-base font-medium">Please select a stage to view artifacts</p>
                                    </div>
                                )}

                                {selectedStage && artifactTypes.length === 0 && (
                                    <div className="text-center py-16">
                                        <p className="text-gray-500 text-base font-medium">No artifact types found for this stage</p>
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>
                <Footer />
            </section>

            {/* Artifact detail drawer */}
            {selectedArtifact && (
                <DetailDrawer
                    title="Artifact Details"
                    subtitle={<>ID: <span className="font-mono font-semibold">{selectedArtifact.artifact_id || "—"}</span></>}
                    summaryFields={artifactDetailSummaryFields}
                    allProperties={artifactDetailProperties}
                    onClose={() => setSelectedArtifact(null)}
                />
            )}

            {/* Compare Modal */}
            {showCompareModal && selectedArtifacts.length >= 2 && (
                <CompareModal
                    items={selectedArtifacts}
                    itemType="artifact"
                    onClose={() => setShowCompareModal(false)}
                />
            )}
        </>
    );
};

export default ArtifactsPostgres;
