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
    if ( selectedPipeline && selectedArtifactType ){
      fetchArtifacts(selectedPipeline, selectedArtifactType, sortOrder, activePage, filter, selectedCol);
    }
  }, [selectedArtifactType, sortOrder, activePage, selectedCol, filter]);

  const fetchArtifacts = (pipelineName, artifactType, sortOrder, activePage, filter="", selectedCol) => {
    client.getArtifacts(pipelineName, artifactType, sortOrder, activePage, filter, selectedCol)
      .then((data) => {
        setArtifacts(data.items);
        setTotalItems(data.total_items);
      });  
  };    
  
  const handleArtifactTypeClick = (artifactType) => {
    if (selectedArtifactType !== artifactType) {
      // if same artifact type is not clicked, sets page as null until it retrieves data for that type.
      setArtifacts(null);
    }  
    setSelectedArtifactType(artifactType);
    setActivePage(1);
  };  

  const handlePipelineClick = (pipeline) => {
    if (selectedPipeline !== pipeline) {
      // this condition sets page as null.
      setArtifacts(null);
    }  
    setSelectedPipeline(pipeline);
    setActivePage(1);
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
                  <ArtifactTypeSidebar
                    artifactTypes={artifactTypes}
                    handleArtifactTypeClick={handleArtifactTypeClick}
                    onFilter={handleFilter}
                  />
                )}
            </div>
            <div>
                {artifacts !== null && artifacts.length > 0 ? (
                  <ArtifactPTable 
                    artifacts={artifacts}
                    artifactType={selectedArtifactType}
                    onsortOrder={toggleSortOrder}
                    onsortTimeOrder={toggleSortTime}
                    filterValue={filter}
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
export default ArtifactsPostgres;
