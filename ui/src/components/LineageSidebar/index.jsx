import React from "react";


const LineageSidebar = ({ pipelines, activeTab, handleClick }) => {
  return (
    <div className="sidebar flex flex-col bg-gray-100 pt-4 pr-4 pb-6 mb-12">
      <h1 className="px-6 pb-6 text-sm font-bold text-center text-gray-500 uppercase">
        List of Pipelines
      </h1>
      {pipelines.map((pipeline, index) => (
        <div key={index}>
          <button
            className={activeTab === index ? "tabs active-tabs" : "tabs"}
            onClick={() => handleClick(index)}
          >
            {pipeline}
          </button>
        </div>
      ))}
    </div>
  );
};

export default LineageSidebar;
