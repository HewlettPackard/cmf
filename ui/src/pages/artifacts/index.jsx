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
import ArtifactTable from "../../components/ArtifactTable";
import Footer from "../../components/Footer";
import "./index.css";
import Sidebar from "../../components/Sidebar";
import ArtifactTypeSidebar from "./ArtifactTypeSidebar";

const client = new FastAPIClient(config);

const Artifacts = () => {
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [pipelines, setPipelines] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [artifactTypes, setArtifactTypes] = useState([]);
  const [selectedArtifactType, setSelectedArtifactType] = useState(null);
  const [totalItems, setTotalItems] = useState(0);
  const [activePage, setActivePage] = useState(1);
  const [clickedButton, setClickedButton] = useState("page");
  // Default sort field
  const [sortField, setSortField] = useState("name");
  // Default sort order
  const [sortOrder, setSortOrder] = useState("asc");
  // Default filter field
  const [filterBy, setFilterBy] = useState(null);
  // Default filter value
  const [filterValue, setFilterValue] = useState(null);

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
    });
  };

  useEffect(() => {
    fetchPipelines();
  }, []);

  const handlePipelineClick = (pipeline) => {
    setArtifacts(null);
    setSelectedPipeline(pipeline);
    setActivePage(1);
  };

  const handleArtifactTypeClick = (artifactType) => {
    setArtifacts(null);
    setSelectedArtifactType(artifactType);
    setActivePage(1);
  };

  const fetchArtifactTypes = () => {
    client.getArtifactTypes().then((types) => {
      setArtifactTypes(types);
      handleArtifactTypeClick(types[0]);
    });
  };

  useEffect(() => {
    if (selectedPipeline) {
      fetchArtifactTypes(selectedPipeline);
    }
    // eslint-disable-next-line
  }, [selectedPipeline]);

  const fetchArtifacts = (pipelineName, type, page, sortField, sortOrder, filterBy, filterValue) => {
    client.getArtifacts(pipelineName, type, page, sortField, sortOrder, filterBy, filterValue).then((data) => {
      setArtifacts(data.items);
      setTotalItems(data.total_items);
    });
  };

  useEffect(() => {
    if (selectedPipeline && selectedArtifactType) {
      fetchArtifacts(selectedPipeline, selectedArtifactType, activePage, sortField, sortOrder, filterBy, filterValue);
    }
  }, [selectedPipeline, selectedArtifactType, activePage, sortField, sortOrder, filterBy, filterValue]);

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

  const handleSort = (newSortField, newSortOrder) => {
    setSortField(newSortField);
    setSortOrder(newSortOrder);
  };

  const handleFilter = (field, value) => {
    setFilterBy(field);
    setFilterValue(value);
  };


  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />
        <div className="flex flex-row">
          <Sidebar
            pipelines={pipelines}
            handlePipelineClick={handlePipelineClick}
          />
          <div className="container justify-center items-center mx-auto px-4">
            <div className="flex flex-col">
              {selectedPipeline !== null && (
                <ArtifactTypeSidebar
                  artifactTypes={artifactTypes}
                  handleArtifactTypeClick={handleArtifactTypeClick}
                />
              )}
            </div>
            <div className="container">
              {selectedPipeline !== null && selectedArtifactType !== null && artifacts !== null && artifacts !== {} && (
                <ArtifactTable artifacts={artifacts} ArtifactType={selectedArtifactType} onSort={handleSort} onFilter={handleFilter}/>
              )}
              <div>
                {artifacts !== null && totalItems > 0 && (
                  <>
                    <button
                      onClick={handlePrevClick}
                      disabled={activePage === 1}
                      className={clickedButton === "prev" ? "active" : ""}
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
                              className={
                                activePage === pageNumber &&
                                clickedButton === "page"
                                  ? "active"
                                  : ""
                              }
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
                              className={
                                activePage === pageNumber &&
                                clickedButton === "page"
                                  ? "active"
                                  : ""
                              }
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
                      }
                    )}
                    <button
                      onClick={handleNextClick}
                      disabled={activePage === Math.ceil(totalItems / 5)}
                      className={clickedButton === "next" ? "active" : ""}
                    >
                      Next
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};
export default Artifacts;
