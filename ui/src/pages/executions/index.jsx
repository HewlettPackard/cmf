import React, { useEffect, useState } from "react";
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import ExecutionTable from "../../components/ExecutionTable";
import Footer from "../../components/Footer";
import "./index.css";
import Sidebar from "../../components/Sidebar";

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
  const [sortOrder, setSortOrder] = useState("asc");
  // Default filter field
  const [filterBy, setFilterBy] = useState(null);
  // Default filter value
  const [filterValue, setFilterValue] = useState(null);

  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
    });
  };

  useEffect(() => {
    if (selectedPipeline) {
      fetchExecutions(selectedPipeline, activePage, sortField, sortOrder, filterBy, filterValue);
    }
  }, [selectedPipeline, activePage, sortField, sortOrder, filterBy, filterValue]);

  const fetchExecutions = (pipelineName, page, sortField, sortOrder, filterBy, filterValue) => {
    client.getExecutions(pipelineName, page, sortField, sortOrder, filterBy, filterValue).then((data) => {
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
            <div className="container">
              {selectedPipeline !== null && (
                <ExecutionTable executions={executions} onSort={handleSort} onFilter={handleFilter}/>
              )}
            </div>
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
        <Footer />
      </section>
    </>
  );
};

export default Executions;
