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

import React, { useEffect, useState, useCallback, useRef, useMemo } from "react";
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import ArtifactPTable from "../../components/ArtifactPTable";
import Footer from "../../components/Footer";
import "./index.css";
import Sidebar from "../../components/Sidebar";
import ArtifactTypeSidebar from "../../components/ArtifactTypeSidebar";
import Papa from "papaparse";
import Highlight from "../../components/Highlight";

const client = new FastAPIClient(config);

// Memoized ArtifactPTable to prevent unnecessary re-renders
const MemoizedArtifactPTable = React.memo(ArtifactPTable);

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

  // Label-specific state
  const [selectedTableLabel, setSelectedTableLabel] = useState(null);
  const [labelData, setLabelData] = useState("");
  const [parsedLabelData, setParsedLabelData] = useState([]);
  const [labelColumns, setLabelColumns] = useState([]);
  const [labelContentLoading, setLabelContentLoading] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const clearLabelData = () => {
    setLabelData("");
    setParsedLabelData([]);
    setLabelColumns([]);
    setLabelContentLoading(false);
    setCurrentPage(0);
  };

  // Flag to prevent re-fetching artifacts when just loading label content
  const [isLoadingLabelContent, setIsLoadingLabelContent] = useState(false);

  // Ref to immediately block fetchArtifacts calls during label loading
  const isLoadingLabelContentRef = useRef(false);

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

  // Simple memoization
  const stableArtifacts = useMemo(() => artifacts, [artifacts]);

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
      if (isLoadingLabelContent || isLoadingLabelContentRef.current) {
        return;
      }

      // Clear artifacts immediately to show loading state (consistent with other artifact types)
      setArtifacts(null);

      // Handle Label search case
      if (artifactType === "Label" && filter && filter.trim() !== "") {
        try {
          const searchData = await client.searchLabelArtifacts(pipelineName, filter, sortOrder, activePage, 5);

          // Add search context to artifacts while preserving backend search_metadata
          // Use a more efficient approach to avoid unnecessary object creation
          searchData.items.forEach(item => {
            item.isSearchResult = true;
            item.searchFilter = filter;
          });

          setArtifacts(searchData.items);
          setTotalItems(searchData.total_items);
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
    }
  };
  
  const handleArtifactTypeClick = (artifactType) => {
    if (selectedArtifactType !== artifactType) {
      // if same artifact type is not clicked, sets page as null until it retrieves data for that type.
      setArtifacts(null);
    }
    setSelectedArtifactType(artifactType);
    setActivePage(1);

    // Clear label-related state when switching artifact types
    setSelectedTableLabel(null);
    clearLabelData();
  };

  const handlePipelineClick = (pipeline) => {
    if (selectedPipeline !== pipeline) {
      // this condition sets page as null.
      setArtifacts(null);
    }
    setSelectedPipeline(pipeline);
    setActivePage(1);

    // Clear label-related state when switching pipelines
    setSelectedTableLabel(null);
    clearLabelData();
  };

  const handleFilter = useCallback((value) => {
    setFilter(value); // Update the filter string
    setActivePage(1);
  }, []);

  const toggleSortOrder = useCallback((newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("name");
  }, []);

  const toggleSortTime = useCallback((newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("create_time_since_epoch");
  }, []);

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

  // Memoized label content display component
  const LabelContentPanel = useMemo(() => {
    return (
      <div className="p-4">
        {selectedTableLabel ? (
        <div>
          {labelContentLoading ? (
            <div className="flex justify-center items-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              <p className="ml-3 text-gray-600">Loading content...</p>
            </div>
          ) : labelData ? (
            <div className="h-full flex flex-col">
              {/* Header aligned with left table */}
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  {selectedTableLabel.name.split(":")[1] || selectedTableLabel.name}
                </h3>
              </div>

              {/* Fixed size table container */}
              <div className="flex flex-col" style={{ height: '400px' }}>
                <div className="overflow-auto bg-white border border-gray-300 rounded" style={{ height: '320px' }}>
                  <table className="divide-y divide-gray-200 border-4 w-full">
                    <thead className="sticky top-0">
                      <tr className="text-xs font-bold font-sans text-left text-black uppercase">
                        {labelColumns.map((column, index) => (
                          <th
                            key={index}
                            scope="col"
                            className="px-6 py-3"
                          >
                            {column.name}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {parsedLabelData.slice(currentPage * rowsPerPage, (currentPage + 1) * rowsPerPage).map((row, rowIndex) => (
                        <tr key={rowIndex} className="text-sm font-medium text-gray-800">
                          {labelColumns.map((column, colIndex) => (
                            <td key={colIndex} className="px-6 py-4">
                              <Highlight
                                text={String(row[column.name] || '')}
                                highlight={selectedTableLabel?.isSearchResult ? selectedTableLabel.searchFilter : ''}
                              />
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination controls */}
                <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-t border-gray-200">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-700">Rows per page:</span>
                    <select
                      value={rowsPerPage}
                      onChange={(e) => {
                        setRowsPerPage(Number(e.target.value));
                        setCurrentPage(0);
                      }}
                      className="border border-gray-300 rounded px-2 py-1 text-sm"
                    >
                      <option value={10}>10</option>
                      <option value={25}>25</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-700">
                      {currentPage * rowsPerPage + 1}-{Math.min((currentPage + 1) * rowsPerPage, parsedLabelData.length)} of {parsedLabelData.length}
                    </span>
                    <button
                      onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
                      disabled={currentPage === 0}
                      className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
                    >
                      Previous
                    </button>
                    <button
                      onClick={() => setCurrentPage(Math.min(Math.ceil(parsedLabelData.length / rowsPerPage) - 1, currentPage + 1))}
                      disabled={currentPage >= Math.ceil(parsedLabelData.length / rowsPerPage) - 1}
                      className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
                    >
                      Next
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-gray-600">No content available</p>
            </div>
          )}
        </div>
      ) : (
        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <h3 className="text-xl font-medium text-gray-800 mb-2">
              Select a Label
            </h3>
            <p className="text-gray-600">
              Click on a label name in the table to view its content
            </p>
          </div>
        </div>
      )}
    </div>
    );
  }, [selectedTableLabel, labelContentLoading, labelData, parsedLabelData, labelColumns, currentPage, rowsPerPage]);

  // Handle label click from table - memoized to prevent re-renders
  const handleTableLabelClick = useCallback(async (labelName, artifact) => {
    // Set ref IMMEDIATELY to block any fetchArtifacts calls
    isLoadingLabelContentRef.current = true;

    // Set loading flag to prevent fetchArtifacts from running
    setIsLoadingLabelContent(true);

    // Batch state updates to minimize re-renders
    setSelectedTableLabel(artifact);
    setLabelContentLoading(true);
    setCurrentPage(0); // Reset pagination when new label is selected

    // Use the URI from the artifact for getLabelData, not just the label name
    const fileNameForAPI = artifact.uri || `artifacts/labels.csv:${labelName}`;

    try {
      // Clear old data first
      setParsedLabelData([]);
      setLabelColumns([]);

      // Helper function to try different URI formats
      const tryGetLabelData = async (labelName, fileNameForAPI) => {
        const uriFormatsToTry = [
          fileNameForAPI,                           // Original: artifacts/labels.csv:93951bf...
          labelName,                                // Just the label name: 93951bf...
          `artifacts/labels.csv/${labelName}`,      // Alternative format: artifacts/labels.csv/93951bf...
          `labels.csv:${labelName}`,                // Without artifacts prefix: labels.csv:93951bf...
          `${labelName}.csv`                        // As CSV file: 93951bf....csv
        ];

        for (const uriToTry of uriFormatsToTry) {
          try {
            const data = await client.getLabelData(uriToTry);
            return data; // Success - return immediately
          } catch (uriError) {
            continue; // Try next URI format
          }
        }

        throw new Error(`All URI formats failed. Tried: ${uriFormatsToTry.join(', ')}`);
      };

      const labelData = await tryGetLabelData(labelName, fileNameForAPI);

      setLabelData(labelData);

      const parsed = Papa.parse(labelData, { header: true });

      // Check if this is a search result and if the search term was found in CSV content
      if (artifact.isSearchResult && artifact.searchFilter && artifact.search_metadata?.content_match) {
        const searchFilter = artifact.searchFilter;

        // Filter CSV rows to show only those containing the search term
        const matchingRows = parsed.data.filter((row) => {
          const rowValues = Object.values(row);

          const hasMatch = rowValues.some(value => {
            if (value && value.toString().toLowerCase().includes(searchFilter.toLowerCase())) {
              return true;
            }
            return false;
          });

          return hasMatch;
        });

        setParsedLabelData(matchingRows);
      } else {
        // Normal label OR search result with property-only match - show all data
        setParsedLabelData(parsed.data);
      }

      if (parsed.meta.fields) {
        setLabelColumns(
          parsed.meta.fields.map(field => ({
            name: field,
            selector: row => row[field],
            sortable: true,
          }))
        );
      }
    } catch (error) {
      // Clear data on error to prevent showing old content
      setParsedLabelData([]);
      setLabelColumns([]);

      // Show error message to user
      setParsedLabelData([{
        error: "Failed to load label content",
        message: error.message,
        uri: fileNameForAPI
      }]);

    } finally {
      setLabelContentLoading(false);
      setIsLoadingLabelContent(false); // Reset flag to allow normal useEffect behavior
      isLoadingLabelContentRef.current = false; // Reset ref to allow future fetchArtifacts calls
    }
  }, []); // Empty dependency array for useCallback

  // Memoized onLabelClick to prevent prop changes
  const memoizedOnLabelClick = useMemo(() => {
    return selectedArtifactType === "Label" ? handleTableLabelClick : undefined;
  }, [selectedArtifactType, handleTableLabelClick]);

  // Memoized setExpandedRow to prevent prop changes
  const memoizedSetExpandedRow = useCallback((value) => {
    setExpandedRow(value);
  }, [selectedArtifactType, filter]);

  // Memoized Left Panel Component to prevent unnecessary re-renders
  const MemoizedLeftPanel = useMemo(() => {
    return (
      <div className="p-4">
        {stableArtifacts !== null && stableArtifacts?.length > 0 ? (
          <MemoizedArtifactPTable
            artifacts={stableArtifacts}
            artifactType={selectedArtifactType}
            onsortOrder={toggleSortOrder}
            onsortTimeOrder={toggleSortTime}
            filterValue={filter}
            onLabelClick={memoizedOnLabelClick}
            expandedRow={expandedRow}
            setExpandedRow={memoizedSetExpandedRow}
          />
        ) : (
          <div className="text-center py-12">
            <p className="text-gray-600">No label artifacts available</p>
          </div>
        )}
      </div>
    );
  }, [stableArtifacts, selectedArtifactType, filter, toggleSortOrder, toggleSortTime, memoizedOnLabelClick, expandedRow, memoizedSetExpandedRow]); // Include accordion state

  // Resizable Split Pane Component
  const ResizableSplitPane = ({ leftContent, rightContent, initialSplitPercentage = 50 }) => {
    const [splitPercentage, setSplitPercentage] = useState(initialSplitPercentage);
    const [isDragging, setIsDragging] = useState(false);
    const containerRef = useRef(null);

    const handleMouseDown = (e) => {
      setIsDragging(true);
      e.preventDefault();
    };

    const handleMouseMove = useCallback((e) => {
      if (!isDragging || !containerRef.current) return;

      const containerRect = containerRef.current.getBoundingClientRect();
      const newPercentage = ((e.clientX - containerRect.left) / containerRect.width) * 100;

      // Limit between 20% and 80%
      const clampedPercentage = Math.max(20, Math.min(80, newPercentage));
      setSplitPercentage(clampedPercentage);
    }, [isDragging]);

    const handleMouseUp = useCallback(() => {
      setIsDragging(false);
    }, []);

    useEffect(() => {
      if (isDragging) {
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        return () => {
          document.removeEventListener('mousemove', handleMouseMove);
          document.removeEventListener('mouseup', handleMouseUp);
        };
      }
    }, [isDragging, handleMouseMove, handleMouseUp]);

    return (
      <div ref={containerRef} className="flex h-full w-full">
        {/* Left Pane */}
        <div style={{ width: `${splitPercentage}%` }} className="overflow-auto">
          {leftContent}
        </div>

        {/* Resizer */}
        <div
          className={`w-1 bg-gray-300 hover:bg-gray-400 cursor-col-resize flex-shrink-0 ${
            isDragging ? 'bg-gray-400' : ''
          }`}
          onMouseDown={handleMouseDown}
        >
          <div className="w-full h-full flex items-center justify-center">
            <div className="w-0.5 h-8 bg-gray-500"></div>
          </div>
        </div>

        {/* Right Pane */}
        <div style={{ width: `${100 - splitPercentage}%` }} className="overflow-auto">
          {rightContent}
        </div>
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
                  leftContent={MemoizedLeftPanel}
                  rightContent={LabelContentPanel}
                  initialSplitPercentage={50}
                />
              </div>
            ) : (
              <div>
                {artifacts !== null && artifacts.length > 0 ? (
                  <MemoizedArtifactPTable
                    artifacts={artifacts}
                    artifactType={selectedArtifactType}
                    onsortOrder={toggleSortOrder}
                    onsortTimeOrder={toggleSortTime}
                    filterValue={filter}
                    expandedRow={expandedRow}
                    setExpandedRow={memoizedSetExpandedRow}
                    />

                ) : (
                  <div>No data available</div> // Display message when there are no artifacts
                )}
                {artifacts !== null && totalItems > 0 && (
                  <>
                    <button
                      onClick={handlePrevClick}
                      disabled={activePage === 1}
                      className={clickedButton === "prev" ? "active-page" : ""}
                    >
                      Previous
                    </button>
                    {Array.from({ length: Math.ceil(totalItems / 5) }).map(
                      (_, index) => {
                        const pageNumber = index + 1;
                        if (
                          pageNumber === 1 ||
                          pageNumber === Math.ceil(totalItems / 5)
                        ) {
                          return (
                            <button
                              key={pageNumber}
                              onClick={() => handlePageClick(pageNumber)}
                              className={`pagination-button ${
                                activePage === pageNumber &&
                                clickedButton === "page"
                                  ? "active-page"
                                  : ""
                              }`}
                            >
                              {pageNumber}
                            </button>
                          );
                        } else if (
                          (activePage <= 3 && pageNumber <= 6) ||
                          (activePage >= Math.ceil(totalItems / 5) - 2 &&
                            pageNumber >= Math.ceil(totalItems / 5) - 5) ||
                          Math.abs(pageNumber - activePage) <= 2
                        ) {
                          return (
                            <button
                              key={pageNumber}
                              onClick={() => handlePageClick(pageNumber)}
                              className={`pagination-button ${
                                activePage === pageNumber &&
                                clickedButton === "page"
                                  ? "active-page"
                                  : ""
                              }`}
                            >
                              {pageNumber}
                            </button>
                          );
                        } else if (
                          (pageNumber === 2 && activePage > 3) ||
                          (pageNumber === Math.ceil(totalItems / 5) - 1 &&
                            activePage < Math.ceil(totalItems / 5) - 3)
                        ) {
                          return (
                            <span
                              key={`ellipsis-${pageNumber}`}
                              className="ellipsis"
                            >
                              ...
                            </span>
                          );
                        }
                        return null;
                      },
                    )}
                    <button
                      onClick={handleNextClick}
                      disabled={activePage === Math.ceil(totalItems / 5)}
                      className={clickedButton === "next" ? "active-page" : ""}
                    >
                      Next
                    </button>
                  </>
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
