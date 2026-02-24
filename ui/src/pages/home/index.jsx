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
      <section className="flex flex-col bg-white min-h-screen">
        <DashboardHeader />
        <div className="flex-1 px-8 py-8 bg-gray-50 flex flex-col items-center">
          {/* Page Header */}
          <div className="mb-8 w-full max-w-5xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-1 text-center">Pipelines</h2>
          </div>

          {pipelines.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 w-full max-w-5xl">
              {pipelines.map((pipeline, i) => (
                <div
                  key={i}
                  className="bg-white rounded-lg border-2 border-gray-200 transition-all duration-200 group"
                >
                  {/* Card Header */}
                  <div className="p-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
                    <div className="flex items-center gap-3">
                      <div className="w-9 h-9 rounded-lg bg-teal-100 flex items-center justify-center flex-shrink-0">
                        <svg className="w-5 h-5 text-teal-600" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                        </svg>
                      </div>
                      <h3 className="text-sm font-bold text-gray-900 break-all line-clamp-2" title={pipeline}>
                        {pipeline}
                      </h3>
                    </div>
                  </div>

                  {/* Card Footer removed - cards are display only */}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-24">
              <div className="text-gray-300 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                </svg>
              </div>
              <p className="text-gray-500 text-base font-medium">No pipelines available</p>
              <p className="text-gray-400 text-sm mt-1">Pipelines will appear here once data is ingested.</p>
            </div>
          )}
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Home;

