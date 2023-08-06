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
  const [page, setPage] = useState(1);

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
    if(selectedPipeline) {
      fetchExecutions(selectedPipeline, page);
    }

  }, [selectedPipeline, page]);

  const fetchExecutions = (pipelineName, page) => {
    client.getExecutions(pipelineName, page).then((data) => {
      setExecutions(data);
      setTotalItems(data.total_items);
    });
  };

  const handlePipelineClick = (pipeline) => {
    setSelectedPipeline(pipeline)
  };

  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />
        <div className="flex flex-row">
          <Sidebar pipelines={pipelines} handlePipelineClick={handlePipelineClick} />
          <div className="container justify-center items-center mx-auto px-4">
            <div className="container">
              {selectedPipeline !== null && (
                  <ExecutionTable executions={executions} />
              )}
            </div>
            <div>
        <button
          className={`pagination-button ${currentPage === 1 ? 'active' : ''}`}
          onClick={() => setPage((prevPage) => Math.max(prevPage - 1, 1))}
          disabled={page === 1}
        >
          Previous
        </button>
        <span>{page}</span>
        <button
          onClick={() =>
            setPage((prevPage) =>
              Math.min(prevPage + 1, Math.ceil(totalItems / 10))
            )
          }
          disabled={page === Math.ceil(totalItems / 10)}
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
