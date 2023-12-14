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
