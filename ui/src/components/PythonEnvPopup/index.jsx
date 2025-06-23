import React from "react";
import "./index.module.css"; // Optional: For styling the popup

const PythonEnvPopup = ({ show, python_env, onClose }) => {
  if (!show) {
    return null;
  }

  console.log(python_env)
  return (
    <>
      <div className="popup-overlay">
        <div className="popup">
          <div className="popup-border">
            <button onClick={onClose} className="close-button">
              X
            </button>
          </div>
          <h2 className="popup-heading">Environment Configuration</h2>
          <div className="popup-content">
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
