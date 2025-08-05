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
import ArtifactPTable from "../../components/ArtifactPTable";
import Footer from "../../components/Footer";
import "./index.css";
import Sidebar from "../../components/Sidebar";
import ArtifactTypeSidebar from "../../components/ArtifactTypeSidebar";
import LabelContentPanel from "./components/LabelContentPanel";
import ResizableSplitPane from "./components/ResizableSplitPane";
import PaginationControls from "./components/PaginationControls";
import { handleTableLabelClick, clearLabelData } from "./utils/labelHandlers";
import Loader from "../../components/Loader";

const client = new FastAPIClient(config);

const ArtifactsPostgres = () => {
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  // undefined state is to check whether artifacts data is set
  // null state of artifacts we display No Data
  const [artifacts, setArtifacts] = useState([]);
  const [artifactTypes, setArtifactTypes] = useState([]);
  const [selectedArtifactType, setSelectedArtifactType] = useState(null);
  const [filter, setFilter] = useState("");
  const [sortOrder, setSortOrder] = useState("asc");
  const [totalItems, setTotalItems] = useState(0);
  const [activePage, setActivePage] = useState(1);
  const [clickedButton, setClickedButton] = useState("page");
  const [selectedCol, setSelectedCol] = useState("name");
  const [loading, setLoading] = useState(true);

  // Label-specific state
  const [selectedTableLabel, setSelectedTableLabel] = useState(null);
  const [labelData, setLabelData] = useState("");
  const [parsedLabelData, setParsedLabelData] = useState([]);
  const [labelColumns, setLabelColumns] = useState([]);
  const [labelContentLoading, setLabelContentLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Flag to prevent re-fetching artifacts when just loading label content
  const [isLoadingLabelContent, setIsLoadingLabelContent] = useState(false);

  // Lift accordion state to parent to preserve it across re-renders
  const [expandedRow, setExpandedRow] = useState(null);

  // Reset accordion state when artifact type changes
  useEffect(() => {
    setExpandedRow(null);
  }, [selectedArtifactType]);

  // Handle accordion auto-expansion for search filters at parent level
  useEffect(() => {
    if (selectedArtifactType === "Label") {
      if (filter && filter.trim() !== "") {
        setExpandedRow("all");
      }
    }
  }, [filter, selectedArtifactType]);

  useEffect(() => {
    fetchPipelines(); // Fetch pipelines and artifact types when the component mounts
  },[]);

  // Fetch pipelines on component mount
  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      const defaultPipeline = data[0];
      setSelectedPipeline(defaultPipeline); // Set the first pipeline as default
    });
  };  
  
  useEffect(() => {
    if (selectedPipeline){
      fetchArtifactTypes(selectedPipeline);
    }
  },[selectedPipeline]);
  
  const fetchArtifactTypes = () => {
    client.getArtifactTypes().then((types) => {
      setArtifactTypes(types);
      const defaultArtifactType = types[0];
      setSelectedArtifactType(defaultArtifactType); // Set the first artifact type as default
      fetchArtifacts(selectedPipeline, defaultArtifactType, sortOrder, activePage, filter, selectedCol); // Fetch artifacts for the first artifact type and default pipeline
    });  
  };  
 
  useEffect(() => {
    // Fetch artifacts when these dependencies change (but not when loading label content)
    if ( selectedPipeline && selectedArtifactType ){
      fetchArtifacts(selectedPipeline, selectedArtifactType, sortOrder, activePage, filter, selectedCol);
    }
  }, [selectedPipeline, selectedArtifactType, sortOrder, activePage, selectedCol, filter]);

  const fetchArtifacts = async (pipelineName, artifactType, sortOrder, activePage, filter="", selectedCol) => {
    try {
      // Don't fetch if we're currently loading label content (prevents left panel reload)
      if (isLoadingLabelContent) {
        return;
      }

      // Set loading state and clear artifacts
      setLoading(true);
      setArtifacts(null);

      // Handle Label search case
      if (artifactType === "Label" && filter && filter.trim() !== "") {
        try {
          const searchData = await client.searchLabelArtifacts(pipelineName, filter, sortOrder, activePage, 5);

          // Add search context to artifacts while preserving backend search_metadata
          searchData.items.forEach(item => {
            item.isSearchResult = true;
            item.searchFilter = filter;
          });

          setArtifacts(searchData.items);
          setTotalItems(searchData.total_items);
          setLoading(false);
          return; // Early return
        } catch (searchError) {
          console.warn('Label search failed, falling back to regular fetch:', searchError);
          // Fall through to regular fetch
        }
      }

      // Regular artifact fetching
      const regularData = await client.getArtifacts(pipelineName, artifactType, sortOrder, activePage, filter, selectedCol);
      setArtifacts(regularData.items);
      setTotalItems(regularData.total_items);

    } catch (error) {
      console.error('Failed to fetch artifacts:', error);
      setArtifacts([]);
      setTotalItems(0);
    } finally {
      setLoading(false);
    }
  };
  
  const handleArtifactTypeClick = (artifactType) => {
    if (selectedArtifactType !== artifactType) {
      // if same artifact type is not clicked, sets page as null until it retrieves data for that type.
      setLoading(true);
      setArtifacts(null);
    }
    setSelectedArtifactType(artifactType);
    setActivePage(1);

    // Clear label-related state when switching artifact types
    setSelectedTableLabel(null);
    clearLabelData({
      setLabelData,
      setParsedLabelData,
      setLabelColumns,
      setLabelContentLoading,
      setCurrentPage
    });
  };

  const handlePipelineClick = (pipeline) => {
    if (selectedPipeline !== pipeline) {
      // this condition sets page as null.
      setLoading(true);
      setArtifacts(null);
    }
    setSelectedPipeline(pipeline);
    setActivePage(1);

    // Clear label-related state when switching pipelines
    setSelectedTableLabel(null);
    clearLabelData({
      setLabelData,
      setParsedLabelData,
      setLabelColumns,
      setLabelContentLoading,
      setCurrentPage
    });
  };

  const handleFilter = (value) => {
    setFilter(value); // Update the filter string
    setActivePage(1);
  };

  const toggleSortOrder = (newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("name");
  };

  const toggleSortTime = (newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("create_time_since_epoch");
  };

  const handlePageClick = (page) => {
    setActivePage(page);
    setClickedButton("page");
  };  

  const handlePrevClick = () => {
    if (activePage > 1) {
      setActivePage(activePage - 1);
      setClickedButton("prev");
      handlePageClick(activePage - 1);
    }  
  };  

  const handleNextClick = () => {
    if (activePage < Math.ceil(totalItems / 5)) {
      setActivePage(activePage + 1);
      setClickedButton("next");
      handlePageClick(activePage + 1);
    }  
  };

  // Handle label click from table
  const handleLabelClick = async (labelName, artifact) => {
    await handleTableLabelClick(labelName, artifact, client, {
      setIsLoadingLabelContent,
      setSelectedTableLabel,
      setLabelContentLoading,
      setCurrentPage,
      setParsedLabelData,
      setLabelColumns,
      setLabelData
    });
  };

  // Left Panel Component
  const renderLeftPanel = () => {
    return (
      <div className="p-4">
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Loader />
          </div>
        ) : artifacts !== null && artifacts?.length > 0 ? (
          <ArtifactPTable
            artifacts={artifacts}
            artifactType={selectedArtifactType}
            onsortOrder={toggleSortOrder}
            onsortTimeOrder={toggleSortTime}
            filterValue={filter}
            onLabelClick={selectedArtifactType === "Label" ? handleLabelClick : undefined}
            expandedRow={expandedRow}
            setExpandedRow={setExpandedRow}
          />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600">No label artifacts available</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <>
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
            {selectedArtifactType === "Label" ? (
              <div className="flex-grow" style={{ height: 'calc(100vh - 200px)' }}>
                <ResizableSplitPane
                  leftContent={renderLeftPanel()}
                  rightContent={
                    <LabelContentPanel
                      selectedTableLabel={selectedTableLabel}
                      labelContentLoading={labelContentLoading}
                      labelData={labelData}
                      parsedLabelData={parsedLabelData}
                      labelColumns={labelColumns}
                      currentPage={currentPage}
                      rowsPerPage={rowsPerPage}
                      setCurrentPage={setCurrentPage}
                      setRowsPerPage={setRowsPerPage}
                    />
                  }
                  initialSplitPercentage={50}
                />
              </div>
            ) : (
              <div>
                {loading ? (
                  <div className="flex justify-center items-center py-12">
                    <Loader />
                  </div>
                ) : artifacts !== null && artifacts.length > 0 ? (
                  <ArtifactPTable
                    artifacts={artifacts}
                    artifactType={selectedArtifactType}
                    onsortOrder={toggleSortOrder}
                    onsortTimeOrder={toggleSortTime}
                    filterValue={filter}
                    expandedRow={expandedRow}
                    setExpandedRow={setExpandedRow}
                    />

                ) : (
                  <div>No data available</div> // Display message when there are no artifacts
                )}
                {!loading && (
                  <PaginationControls
                    totalItems={totalItems}
                    activePage={activePage}
                    clickedButton={clickedButton}
                    onPageClick={handlePageClick}
                    onPrevClick={handlePrevClick}
                    onNextClick={handleNextClick}
                  />
                )}
              </div>
            )}
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};
export default ArtifactsPostgres;
