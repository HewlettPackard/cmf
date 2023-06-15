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

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
    });
  };


   useEffect(() => {
     fetchPipelines();
   }, []);


  useEffect(() => {
    if(selectedPipeline) {
      fetchArtifactTypes(selectedPipeline);
    }
    // eslint-disable-next-line  
  }, [selectedPipeline]);


  useEffect(() => {
    if(selectedPipeline && selectedArtifactType) {
      fetchArtifacts(selectedPipeline, selectedArtifactType);
      console.log(selectedPipeline, selectedArtifactType);
    }

  }, [selectedPipeline, selectedArtifactType]);


  const fetchArtifactTypes = (pipelineName) => {
    client.getArtifacts(pipelineName, "artifact_type").then((types) => {
      setArtifactTypes(types);
      if(selectedArtifactType === null)
        setSelectedArtifactType(types[0]);
    });
  };


  const handlePipelineClick = (pipeline) => {
    setSelectedPipeline(pipeline)
  };

  const handleArtifactTypeClick = (artifactType) => {
    setSelectedArtifactType(artifactType);
  };


  const fetchArtifacts = (pipelineName, type) => {
    client.getArtifacts(pipelineName, type).then((data) => {
      console.log(data);
      setArtifacts(data);
    });
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
           <div className="flex flex-col">
              {selectedPipeline !== null && (
                <ArtifactTypeSidebar artifactTypes={artifactTypes} handleArtifactTypeClick={handleArtifactTypeClick} />
              )}
            </div>
            <div className="container">
              {selectedPipeline !== null && selectedArtifactType !== null && (
                  <ArtifactTable artifacts={artifacts} />
              )}
            </div>
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};
export default Artifacts;
