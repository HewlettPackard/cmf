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

const client = new FastAPIClient(config);

const Home = () => {
  const [pipelines, setPipelines] = useState([]);
  useEffect(() => {
    fetchPipelines();
  }, []);

  const fetchPipelines = () => {
    client.getPipelines("").then((data) => {
      setPipelines(data);
    });
  };
  return (
    <>
      <section
        className="flex flex-col bg-white"
        style={{ minHeight: "100vh" }}
      >
        <DashboardHeader />
        <div className="container justify-start items-start mx-auto px-50">
          <table className="table-auto">
            <thead className="bg-gray-100 text-center">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-s  font-bold text-black uppercase "
                >
                  List of Pipelines
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {pipelines !== null && pipelines.length > 0 ? (
                pipelines.map((data, i) => (
                  <tr key={i}>
                    <td className="text-center"> {data} </td>
                  </tr>
                ))
                ) : (
                  <div>No pipeline available</div> // Display message when there are no artifacts
                )}
            </tbody>
          </table>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Home;
