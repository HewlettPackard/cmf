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
      fetchExecutions(selectedPipeline, activePage);
    }
  }, [selectedPipeline, activePage]);

  const fetchExecutions = (pipelineName, page) => {
    client.getExecutions(pipelineName, page).then((data) => {
      setExecutions(data.items);
      setTotalItems(data.total_items);
    });
  };

  const handlePipelineClick = (pipeline) => {
    setSelectedPipeline(pipeline);
    setActivePage(1)
  };

  const handlePageClick = (page) => {
    setActivePage(page);
    setClickedButton("page");
  };

  const handlePrevClick = () => {
    if (activePage > 1) {
      setActivePage(activePage - 1);
      setClickedButton("prev");
      handlePageClick(activePage - 1)
    }
  };

  const handleNextClick = () => {
    if (activePage < Math.ceil(totalItems / 5)) {
      setActivePage(activePage + 1);
      setClickedButton("next");
      handlePageClick(activePage + 1)
    }
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
                <ExecutionTable executions={executions} />
              )}
            </div>
            <div>
              <button
                onClick={handlePrevClick}
                disabled={activePage === 1}
                className={clickedButton === "prev" ? "active" : ""}
              >
                Previous
              </button>
              {[...Array(Math.ceil(totalItems / 5))].map((_, index) => (
                <button
                  key={index + 1}
                  onClick={() => handlePageClick(index + 1)}
                  className={
                    activePage === index + 1 && clickedButton === "page"
                      ? "active"
                      : ""
                  }
                >
                  {index + 1}
                </button>
              ))}
              <button
                onClick={handleNextClick}
                disabled={activePage === Math.ceil(totalItems / 5)}
                className={clickedButton === "next" ? "active" : ""}
              >
                Next
              </button>
            </div>
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Executions;
