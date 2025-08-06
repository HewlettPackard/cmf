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
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import Footer from "../../components/Footer";
import Sidebar from "../../components/Sidebar";
import ArtifactTypeSidebar from "../../components/ArtifactTypeSidebar";
import ArtifactsMainContent from "./components/ArtifactsMainContent";
import useArtifactsState from "./hooks/useArtifactsState";
import useArtifactsData from "./hooks/useArtifactsData";
import useArtifactsHandlers from "./hooks/useArtifactsHandlers";
import "./index.css";

const client = new FastAPIClient(config);

const ArtifactsPostgres = () => {
  // Get all state from custom hook
  const state = useArtifactsState();

  // // Get data fetching functions
  const { fetchPipelines, fetchArtifactTypes, fetchArtifacts } = useArtifactsData(client, state);

  // Get event handlers
  const handlers = useArtifactsHandlers(client, state);

  const {
    selectedPipeline,
    pipelines,
    artifacts,
    artifactTypes,
    selectedArtifactType,
    filter,
    loading,
    totalItems,
    activePage,
    clickedButton,
    expandedRow,
    setExpandedRow,
    // Label-specific state
    selectedTableLabel,
    labelContentLoading,
    labelData,
    parsedLabelData,
    labelColumns,
    currentPage,
    rowsPerPage,
    setCurrentPage,
    setRowsPerPage
  } = state;

  const {
    handleArtifactTypeClick,
    handlePipelineClick,
    handleFilter,
    toggleSortOrder,
    toggleSortTime,
    handlePageClick,
    handlePrevClick,
    handleNextClick,
    handleLabelClick
  } = handlers;

  return (
    <section
      className="flex flex-col bg-white min-h-screen"
      style={{ minHeight: "100vh" }}
    >
      <DashboardHeader />
      <div className="flex flex-grow" style={{ padding: "1px" }}>
        <div className="sidebar-container min-h-140 bg-gray-100 pt-2 pr-2 pb-4 w-1/6 flex-grow-0">
          <Sidebar
            pipelines={pipelines}
            handlePipelineClick={handlePipelineClick}
            className="flex-grow"
          />
        </div>

        <div className="justify-center items-center mx-auto px-4 flex-grow w-5/6">
          <div className="flex flex-col w-full">
            {selectedPipeline !== null && (
              <ArtifactTypeSidebar
                artifactTypes={artifactTypes}
                handleArtifactTypeClick={handleArtifactTypeClick}
                onFilter={handleFilter}
              />
            )}
          </div>

          <ArtifactsMainContent
            selectedArtifactType={selectedArtifactType}
            loading={loading}
            artifacts={artifacts}
            toggleSortOrder={toggleSortOrder}
            toggleSortTime={toggleSortTime}
            filter={filter}
            expandedRow={expandedRow}
            setExpandedRow={setExpandedRow}
            onLabelClick={handleLabelClick}
            // Label-specific props
            selectedTableLabel={selectedTableLabel}
            labelContentLoading={labelContentLoading}
            labelData={labelData}
            parsedLabelData={parsedLabelData}
            labelColumns={labelColumns}
            currentPage={currentPage}
            rowsPerPage={rowsPerPage}
            setCurrentPage={setCurrentPage}
            setRowsPerPage={setRowsPerPage}
            // Pagination props
            totalItems={totalItems}
            activePage={activePage}
            clickedButton={clickedButton}
            onPageClick={handlePageClick}
            onPrevClick={handlePrevClick}
            onNextClick={handleNextClick}
          />
        </div>
      </div>
      <Footer />
    </section>
  );
};
export default ArtifactsPostgres;
