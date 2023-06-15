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
        <div className="container justify-center items-center mx-auto px-50">
          <table className="table-auto">
            <thead className="bg-gray-100">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-xs font-bold text-left text-gray-500 uppercase "
                >
                  List of Pipelines
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {pipelines.map((data, i) => (
                <tr key={i}>
                  <td> {data} </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Footer />
      </section>
    </>
  );
};

export default Home;
