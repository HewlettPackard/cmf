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
    setSelectedPipeline(pipeline);
  };

  const handleArtifactTypeClick = (artifactType) => {
    setSelectedArtifactType(artifactType);
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

  const fetchArtifacts = (pipelineName, type, page) => {
    client.getArtifacts(pipelineName, type, page).then((data) => {
      setArtifacts(data.items);
      setTotalItems(data.total_items);
    });
  };

  useEffect(() => {
    if (selectedPipeline && selectedArtifactType) {
      fetchArtifacts(selectedPipeline, selectedArtifactType, activePage);
    }
  }, [selectedPipeline, selectedArtifactType, activePage]);

  const handlePageClick = (page) => {
    setActivePage(page);
    setClickedButton("page");
  };

  const handlePrevClick = () => {
    if (activePage > 1) {
      setActivePage(activePage - 1);
      setClickedButton("prev");
    }
  };

  const handleNextClick = () => {
    if (activePage < Math.ceil(totalItems / 2)) {
      setActivePage(activePage + 1);
      setClickedButton("next");
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
            <div className="flex flex-col">
              {selectedPipeline !== null && (
                <ArtifactTypeSidebar
                  artifactTypes={artifactTypes}
                  handleArtifactTypeClick={handleArtifactTypeClick}
                />
              )}
            </div>
            <div className="container">
              {selectedPipeline !== null && selectedArtifactType !== null && (
                <ArtifactTable artifacts={artifacts} />
              )}
              <div>
                <button
                  onClick={handlePrevClick}
                  disabled={activePage === 1}
                  className={clickedButton === "prev" ? "active" : ""}
                >
                  Previous
                </button>
                {[...Array(Math.ceil(totalItems / 2))].map((_, index) => (
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
                  disabled={activePage === Math.ceil(totalItems / 2)}
                  className={clickedButton === "next" ? "active" : ""}
                >
                  Next
                </button>
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
