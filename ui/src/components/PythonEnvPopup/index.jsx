import React from "react";

const PythonEnvPopup = ({ show, python_env, onClose }) => {
  if (!show) {
    return null;
  }

  console.log(python_env)
  return (
    <>
      <div className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 flex justify-center items-center"> 
        <div className="relative bg-white p-5 rounded-lg w-11/12 max-w-3xl max-h-[90vh] shadow-md overflow-y-auto">
            <button 
              onClick={onClose} 
              className="absolute top-2 right-2 bg-gray-500 text-white border-2 border-black rounded-full px-2.5 py-1 text-xs cursor-pointer">
              X
            </button>
            <h2 className="text-xl font-bold text-center text-gray-800 m-0 py-2.5 bg-gray-100 border-b border-gray-300">Environment Configuration</h2>
          <div className="mt-5 p-4 font-mono text-sm bg-gray-100 text-gray-800 border border-gray-300 rounded max-h-[400px] overflow-y-auto whitespace-pre-wrap">
            <pre>
              <code className="language-yaml">{python_env}</code>
            </pre>
          </div>
        </div>
      </div>
    </>
  );
};

export default PythonEnvPopup;
