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
    <div className="dropdown">
      <select
        className="dropdown-select"
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
