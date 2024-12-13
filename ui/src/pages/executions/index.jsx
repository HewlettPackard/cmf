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
import ExecutionTable from "../../components/ExecutionTable";
import Footer from "../../components/Footer";
import "./index.module.css";
import Sidebar from "../../components/Sidebar";
import Loader from "../../components/Loader";

const client = new FastAPIClient(config);

const Executions = () => {
  const [pipelines, setPipelines] = useState([]);
  const [selectedPipeline, setSelectedPipeline] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [totalItems, setTotalItems] = useState(0);
  const [activePage, setActivePage] = useState(1);
  const [clickedButton, setClickedButton] = useState("page");
  // Default sort field
  const [sortField, setSortField] = useState("Context_Type");
  // Default sort order
  const [sortOrder, setSortOrder] = useState(null);
  // Default filter field
  const [filterBy, setFilterBy] = useState(null);
  // Default filter value
  const [filterValue, setFilterValue] = useState(null);
  // Default value for loader
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = () => {
    setLoading(true);
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
      setLoading(false);
    });
  };

  useEffect(() => {
    if (selectedPipeline) {
      fetchExecutions(
        selectedPipeline,
        activePage,
        sortField,
        sortOrder,
        filterBy,
        filterValue,
      );
    }
  }, [
    selectedPipeline,
    activePage,
    sortField,
    sortOrder,
    filterBy,
    filterValue,
  ]);

  const fetchExecutions = (
    pipelineName,
    page,
    sortField,
    sortOrder,
    filterBy,
    filterValue,
  ) => {
    client
      .getExecutions(
        pipelineName,
        page,
        sortField,
        sortOrder,
        filterBy,
        filterValue,
      )
      .then((data) => {
        setExecutions(data.items);
        setTotalItems(data.total_items);
      });
  };

  const handlePipelineClick = (pipeline) => {
    setSelectedPipeline(pipeline);
    setActivePage(1);
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

  const handleSort = (newSortField, newSortOrder) => {
    setSortField(newSortField);
    setSortOrder(newSortOrder);
    fetchExecutions(
      selectedPipeline,
      activePage,
      newSortField,
      newSortOrder,
      filterBy,
      filterValue,
    );
  };

  const handleFilter = (field, value) => {
    setFilterBy(field);
    setFilterValue(value);
  };

  return (
    <>
      <section
        className="flex flex-col bg-white min-h-screen"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />
        <div className="flex flex-row flex-grow">
          <div className="sidebar-container min-h-140 bg-gray-100 pt-2 pr-2 pb-4 w-1/6 flex-grow-0">
            <Sidebar
              pipelines={pipelines}
              handlePipelineClick={handlePipelineClick}
              className="flex-grow"
            />
          </div>
          <div className="w-5/6 justify-center items-center mx-auto px-4 flex-grow">
            {loading ? (
              <div className="flex-grow flex justify-center items-center">
                <Loader />
              </div>
            ) : (
              <div>
                {selectedPipeline !== null && executions !== null && (
                  <ExecutionTable
                    executions={executions}
                    onSort={handleSort}
                    onFilter={handleFilter}
                  />
                )}
                <div>
                  {executions !== null && totalItems > 0 && (
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
                                className={`pagination-button ${
                                  activePage === pageNumber &&
                                  clickedButton === "page"
                                    ? "active"
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
                                    ? "active"
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
                        className={clickedButton === "next" ? "active" : ""}
                      >
                        Next
                      </button>
                    </>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Executions;
