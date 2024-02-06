import React, { useState } from "react";

const ExecutionDropdown = ({data}) => {
   const [selectedExecutionType, setSelectedExecutionType] = useState(null);
   const [execTypes,setExecTypes]= useState([]);
   console.log(data,"inside exec_drop");
   const handleExecutionTypeSelect = (executionType) => {
       setSelectedExecutionType(executionType);
   };
   return (
     <div className= "dropdown">  
      <select 
        className= "dropdown-select"
        value={selectedExecutionType}
        onChange={(e) => handleExecutionTypeSelect(e.target.value) }
      >
        <option value="" disabled>
            choose an execution type
        </option>
        {data.map((type) => (
         <option key={type} value={type}> 
             {type}
         </option>
         ))}
       </select>
      </div>

  );
};

export default ExecutionDropdown;
