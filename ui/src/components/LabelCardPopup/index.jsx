import React from "react";
import "./index.css"; // Optional: For styling the popup
import DataTable from "react-data-table-component";
import Papa from "papaparse";
import { useEffect, useState } from "react";

const LabelCardPopup = ({ show, label_data, onClose}) => {  
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  
  useEffect(() => {
    const parsed = Papa.parse(label_data, { header: true });
    setData(parsed.data);
    console.log(parsed.data);
    if (parsed.meta.fields) {
      setColumns(
        parsed.meta.fields.map(field => ({
          name: field,
          selector: row => row[field],
        }))
      );
    }
  }, [label_data]);
  
  if (!show) {
    return null;
  }
  
  return (
    <>
      <link
        rel="stylesheet"
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css"
      />
      <div className="popup-overlay">
        <div className="popup">
          <div className="popup-border">
            <button onClick={onClose} className="close-button">
              X
            </button>
          </div>
          <div className="popup-content">
            <div className="table-container">
              {label_data.length > 0 ? (
                <DataTable columns={columns} data={data} />  
              ) : (
                <p>No items available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default LabelCardPopup;
