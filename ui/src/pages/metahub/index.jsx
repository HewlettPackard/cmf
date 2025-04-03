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

import React, { useState } from "react";
import DashboardHeader from "../../components/DashboardHeader";
import Footer from "../../components/Footer";
import RegisteredServers from "../../components/Registration/RegisteredServers";
import DataSync from "../../components/DataSync";
import RegistrationForm from "../../components/Registration/RegistrationForm";
import FastAPIClient from '../../client';
import config from '../../config';

const client = new FastAPIClient(config);

const Metahub = () => {
  const [showRegistrationForm, setShowRegistrationForm] = useState(false);
  const [showRegisteredServers, setShowRegisteredServers] = useState(false);
  const [showDataSync, setShowDataSync] = useState(false);
  const [serverList, setServerList] = useState([]);

  const closeForm = () => {
    setShowRegistrationForm(false);
  };

  const clearScreen = () => {
    setShowRegistrationForm(false);
    setShowRegisteredServers(false);
    setShowDataSync(false);
  };

  const getRegistredServers = () =>{
    client.getRegistredServerList()
    .then((data) => {
        console.log(data);
        setServerList(data);
    })
    .catch((error) => {
        console.error('Error:', error);
        alert('Failed to fetch server list. Please try again.');
    });
  }

  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />
        <div className="flex flex-row">
          <div className="container justify-center items-center mx-auto px-4">
            <button
              className="bg-blue-500 text-white font-bold py-2 px-4 rounded m-2"
              onClick={() => {
                setShowRegistrationForm(true);
                setShowRegisteredServers(false);
                setShowDataSync(false);
              }}
            >
              Registration
            </button>
            <button
              className="bg-green-500 text-white font-bold py-2 px-4 rounded m-2"
              onClick={() => {
                clearScreen();
                setShowDataSync(true);
                getRegistredServers();
              }}
            >
              Sync server
            </button>
            <button
              className="bg-cyan-500 text-white font-bold py-2 px-4 rounded m-2"
              onClick={() => {
                setShowRegisteredServers(true);
                getRegistredServers();
              }}
            >
              Registered server
            </button>
          </div>
        </div>
        {showRegistrationForm && <RegistrationForm closeForm={closeForm} />}
        {showRegisteredServers && <RegisteredServers serverList={serverList}/>}
        {showDataSync && <DataSync servers={serverList} onClearScreen={clearScreen} />}
        <Footer />
      </section>
    </>
  );
};

export default Metahub;
