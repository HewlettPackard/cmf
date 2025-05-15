import React from "react";
import "./index.css"; // Optional: For styling the popup

const LabelCardPopup = ({ show, label_data, onClose}) => {  
  if (!show) {
    return null;
  }

  // Function to parse CSV string into an array of objects
  const parseCsv = (csvString) => {
    const rows = csvString.split("\n"); // Split by newlines
    const headers = rows[0].split(","); // Extract headers from the first row
    const data = rows.slice(1).map((row) => {
      const values = row.split(",");
      // Create an object for each row with header-value pairs 
      return headers.reduce((acc, header, index) => {
        acc[header] = values[index];
        return acc;
      }, {});
    });
    return data;
  };

  const tableData = parseCsv(label_data);
  
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
              {tableData.length > 0 ? (
                <table border="1" className="table">
                  <thead className="thead">
                    <tr>
                      {Object.keys(tableData[0]).map((header, index) => (
                        <th key={index} scope="col">{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="tbody">
                    {tableData.map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {Object.values(row).map((value, colIndex) => (
                          <td key={colIndex}>{value}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
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
