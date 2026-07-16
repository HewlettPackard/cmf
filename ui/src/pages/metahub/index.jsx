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

import { useState } from "react";
import DashboardHeader from "../../components/DashboardHeader";
import Footer from "../../components/Footer";
import RegisteredServers from "../../components/Registration/RegisteredServers";
import RegistrationForm from "../../components/Registration/RegistrationForm";
import FastAPIClient from '../../client';
import config from '../../config';

const client = new FastAPIClient(config);

const Metahub = () => {
  const [showRegistrationForm, setShowRegistrationForm] = useState(true);
  const [showRegisteredServers, setShowRegisteredServers] = useState(false);
  const [serverList, setServerList] = useState([]);
  const [activeButton, setActiveButton] = useState("registration");

  const closeForm = () => {
    setShowRegistrationForm(false);
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
        className="flex flex-col bg-white font-sans min-h-screen"
      >
        <DashboardHeader />
        <div className="flex justify-center items-center py-8">
          <div className="bg-white rounded-lg shadow-md p-6 flex space-x-6">
            <button
              className={`text-lg font-semibold font-sans py-2 px-6 rounded-lg transition-colors duration-200 w-60 ${
                activeButton === "registration" ? "bg-teal-900 text-white" : "bg-teal-600 text-white hover:bg-teal-900"
              }`}
              onClick={() => {
                setShowRegistrationForm(true);
                setShowRegisteredServers(false);
                setActiveButton("registration");
              }}
            >
              Registration
            </button>
            <button
              className={`text-lg font-semibold font-sans py-2 px-6 rounded-lg transition-colors duration-200 w-60 ${
                activeButton === "registered" ? "bg-teal-900 text-white" : "bg-teal-600 text-white hover:bg-teal-900"
              }`}
              onClick={() => {
                setShowRegisteredServers(true);
                getRegistredServers();
                setActiveButton("registered");
              }}
            >
              Registered servers
            </button>
          </div>
        </div>
        <div className="flex flex-col items-center w-full">
          {activeButton === "registration" && showRegistrationForm && <RegistrationForm closeForm={closeForm} />}
          {activeButton === "registered" && showRegisteredServers && <RegisteredServers serverList={serverList}/>} 
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Metahub;
