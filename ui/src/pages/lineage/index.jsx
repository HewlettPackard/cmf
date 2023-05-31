import React, { useEffect, useState } from "react";
import FastAPIClient from "../../client";
import config from "../../config";
import DashboardHeader from "../../components/DashboardHeader";
import Footer from "../../components/Footer";
import LineageSidebar from "../../components/LineageSidebar";
import LineageImage from "../../components/LineageImage";

const client = new FastAPIClient(config);

const Lineage = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [pipelines, setPipelines] = useState([]);
  const [imageSrc, setImageSrc] = useState("");
  const [selectedPipeline, setSelectedPipeline] = useState(null);

  useEffect(() => {
    fetchPipelines();
  }, []);

  useEffect(() => {
    fetchImage(selectedPipeline);
  }, [selectedPipeline]);

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
      setSelectedPipeline(data[0]);
    });
  };

  async function fetchImage(pipeline){
    const objectURL = await client.getImage(pipeline);
    setImageSrc(objectURL);
  }

  const handleClick = (index) => {
    setActiveTab(index);
    fetchImage(pipelines[index]);
  };

  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />

        <div className="container">
          <div className="flex flex-row">
            <LineageSidebar
              pipelines={pipelines}
              activeTab={activeTab}
              handleClick={handleClick}
            />
            <LineageImage imageSrc={imageSrc} activeTab={activeTab} />
          </div>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Lineage;
