import React, { useState, useEffect } from "react";

const ExecutionDropdown = ({ data, exec_type, handleExecutionClick }) => {
  const [selectedExecutionType, setSelectedExecutionType] = useState("");

  useEffect(() => {
    if (exec_type) {
      setSelectedExecutionType(exec_type);
    }
  }, [exec_type]);

  const handleCallExecutionClick = (event) => {
    handleExecutionClick(event.target.value);
  };

  return (
    <div className="relative inline-block mt-0.5 border-2 rounded-sm">
       <select
        className="py-2 px-4 text-sm cursor-pointer border border-solid border-black outline-none 
        transition duration-300 ease-in-out focus:border-blue-500 hover:border-blue-500"
        value={selectedExecutionType}
        onChange={(event) => {
          handleCallExecutionClick(event);
        }}
      >
        {data.map((type, index) => {
          return (
            <option key={index} value={type}>
              {type}
            </option>
          );
        })}
      </select>
    </div>
  );
};

export default ExecutionDropdown;
