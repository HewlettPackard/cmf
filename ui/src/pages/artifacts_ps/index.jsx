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
import ArtifactPsTable from "../../components/ArtifactPsTable";
import Footer from "../../components/Footer";
import "./index.css";
import Sidebar from "../../components/Sidebar";
import ArtifactPsTypeSidebar from "../../components/ArtifactPsTypeSidebar";

const client = new FastAPIClient(config);

const Artifacts_ps = () => {
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
  const [customPropKey, setCustomPropKey] = useState("");
  const [customPropValue, setCustomPropValue] = useState("");
  const [selectedCol, setSelectedCol] = useState("name");

  // Fetch pipelines on component mount
  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      const defaultPipeline = data[0];
      setSelectedPipeline(defaultPipeline); // Set the first pipeline as default
      fetchArtifactTypes(defaultPipeline); // Fetch artifact types once the pipeline is selected
    });
  };

  const fetchArtifactTypes = (pipeline) => {
    client.getArtifactTypes().then((types) => {
      setArtifactTypes(types);
      const defaultArtifactType = types[0];
      setSelectedArtifactType(defaultArtifactType); // Set the first artifact type as default
      fetchArtifacts(pipeline, defaultArtifactType, filter, sortOrder, activePage, customPropKey, customPropValue, selectedCol); // Fetch artifacts for the first artifact type and default pipeline
    });
  };

  const fetchArtifacts = (pipelineName, artifactType, filter="", sortOrder, activePage, customPropKey="", customPropValue="", selectedCol) => {
    client.getArtifact(pipelineName, artifactType, filter, sortOrder, activePage, customPropKey, customPropValue, selectedCol)
      .then((data) => {
        console.log(data);
        console.log(data.items);
        console.log(data.total_items);
        setArtifacts(data.items);
        setTotalItems(data.total_items);
      });
  };

  const handleArtifactTypeClick = (artifactType) => {
    setSelectedArtifactType(artifactType); // Set the selected artifact type
    setArtifacts(null); // Reset artifacts to null to indicate a new fetch
    if (selectedPipeline) {
      fetchArtifacts(selectedPipeline, artifactType, filter, sortOrder, activePage, customPropKey, customPropValue, selectedCol); // Fetch artifacts based on the selected artifact type and pipeline
    }
    setActivePage(1);
  };

  const handlePipelineClick = (pipeline) => {
    setSelectedPipeline(pipeline); // Set the selected pipeline
    setArtifacts(null); // Reset artifacts to null to indicate a new fetch
    fetchArtifacts(pipeline, selectedArtifactType, filter, sortOrder, activePage, customPropKey, customPropValue, selectedCol); // Fetch artifacts based on the selected pipeline and artifact type
    setActivePage(1);
  };

  const handleFilter = (value) => {
    setFilter(value); // Update the filter string
    // console.log("value",value)
  };

  const toggleSortOrder = (newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("name");
    if (selectedPipeline && selectedArtifactType) {
      fetchArtifacts(selectedPipeline, selectedArtifactType, filter, newSortOrder, activePage, customPropKey, customPropValue, "name");
    }
  };

  const toggleSortTime = (newSortOrder) => {
    setSortOrder(newSortOrder);
    setSelectedCol("create_time_since_epoch");
    if (selectedPipeline && selectedArtifactType) {
      fetchArtifacts(selectedPipeline, selectedArtifactType, filter, newSortOrder, activePage, customPropKey, customPropValue, "create_time_since_epoch");
    }
  };

  const handlePageClick = (page) => {
    setActivePage(page);
    fetchArtifacts(selectedPipeline, selectedArtifactType, filter, sortOrder, page, customPropKey, customPropValue, selectedCol);
    setClickedButton("page");
  };

  const handlePrevClick = () => {
    if (activePage > 1) {
      setActivePage(activePage - 1);
      setClickedButton("prev");
      handlePageClick(activePage - 1);
      fetchArtifacts(selectedPipeline, selectedArtifactType, filter, sortOrder, activePage, customPropKey, customPropValue, selectedCol);
    }
  };

  const handleNextClick = () => {
    if (activePage < Math.ceil(totalItems / 5)) {
      setActivePage(activePage + 1);
      setClickedButton("next");
      handlePageClick(activePage + 1);
      fetchArtifacts(selectedPipeline, selectedArtifactType, filter, sortOrder, activePage, selectedCol);
    }
  };

  const handleCustomPropKey = (value) => {
    setCustomPropKey(value); // Update the filter string
    // console.log("value",value)
  };

  const handleCustomPropValue = (value) => {
    setCustomPropValue(value); // Update the filter string
    // console.log("value",value)
  };
  

  useEffect(() => {
    fetchPipelines(); // Fetch pipelines and artifact types when the component mounts
  }, [filter, customPropKey, customPropValue]);

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
          <div className="w-5/6 justify-center items-center mx-auto px-4 flex-grow">
            <div className="flex flex-col w-full">
                {selectedPipeline !== null && (
                  <ArtifactPsTypeSidebar
                    artifactTypes={artifactTypes}
                    handleArtifactTypeClick={handleArtifactTypeClick}
                    onFilter={handleFilter}
                    onCustomPropKey={handleCustomPropKey}
                    onCustomPropValue={handleCustomPropValue}
                  />
                )}
            </div>
            <div>
                {artifacts !== null && artifacts.length > 0 ? (
                  <ArtifactPsTable 
                    artifacts={artifacts}
                    onsortOrder={toggleSortOrder}
                    onsortTimeOrder={toggleSortTime}
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
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};
export default Artifacts_ps;
