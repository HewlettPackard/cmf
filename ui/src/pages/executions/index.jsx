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
      fetchExecutions(selectedPipeline);
    }

  }, [selectedPipeline]);

  const fetchExecutions = (pipelineName) => {
    client.getExecutions(pipelineName).then((data) => {
      setExecutions(data);
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
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Executions;
