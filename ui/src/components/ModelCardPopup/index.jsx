import React from "react";
import "./index.css"; // Optional: For styling the popup

const ModelCardPopup = ({ show, model_data, onClose }) => {
  if (!show) {
    return null;
  }

  // find the uri value from artifacts
  const findUri = () => {
    const item = model_data[0].find((entry) => entry.uri);
    return item ? item.uri : "default";
  };

  // create filename based on uri
  const createFilename = (uri) => {
    return `model_card_${uri}.json`;
  };

  const downloadJSON = () => {
    const uri = findUri();
    const filename = createFilename(uri);

    const jsonString = JSON.stringify(model_data, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const excludeColumns = ["create_time_since_epoch"];

  const renameKey = (key) => {
    const prefix = "custom_properties_";
    if (key.startsWith(prefix)) {
      return key.slice(prefix.length);
    }
    return key;
  };

  const renderContent = (item, index) => {
    switch (index) {
      case 0:
        return (
          <div>
            <p>Model's Data</p>
            <br />
            {item.length > 0 &&
              item.map((data, i) => (
                <div key={i} className="popup-row">
                  <div className="popup-labels">
                    {Object.keys(data)
                      .filter((key) => !excludeColumns.includes(key))
                      .map((key, idx) => (
                        <p key={idx}>{renameKey(key)}:</p>
                      ))}
                  </div>
                  <div className="popup-data">
                    {Object.entries(data)
                      .filter(([key]) => !excludeColumns.includes(key))
                      .map(([key, value], idx) => (
                        <p key={idx}>{value ? value : "Null"}</p>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        );
      case 1:
        const exe_headers = item.length > 0 ? Object.keys(item[0]) : [];
        return (
          <div className="table-container">
            <hr />
            <p>List of executions in which model has been used</p>
            <br />
            <table className="table">
              <thead className="thead">
                <tr>
                  {exe_headers.map((header, index) => (
                    <th scope="col" key={index}>
                      {renameKey(header)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="tbody">
                {item.length > 0 &&
                  item.map((data, i) => (
                    <tr key={i}>
                      {exe_headers.map((header, index) => (
                        <td key={index}>{data[header]}</td>
                      ))}
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        );
      case 2:
        return (
          <div>
            <hr />
            <p>List of input artifacts for the model</p>
            <br />
            {item.length > 0 &&
              item.map((data, i) => (
                <div key={i} className="popup-row">
                  <div className="popup-labels">
                    {Object.keys(data)
                      .filter((key) => !excludeColumns.includes(key))
                      .map((key, idx) => (
                        <p key={idx}>{renameKey(key)}:</p>
                      ))}
                  </div>
                  <div className="popup-data">
                    {Object.entries(data)
                      .filter(([key]) => !excludeColumns.includes(key))
                      .map(([key, value], idx) => (
                        <p key={idx}>{value ? value : "Null"}</p>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        );
      case 3:
        return (
          <div>
            <hr />
            <p>List of output artifacts for the model</p>
            <br />
            {item.length > 0 &&
              item.map((data, i) => (
                <div key={i} className="popup-row">
                  <div className="popup-labels">
                    {Object.keys(data)
                      .filter((key) => !excludeColumns.includes(key))
                      .map((key, idx) => (
                        <p key={idx}>{renameKey(key)}:</p>
                      ))}
                  </div>
                  <div className="popup-data">
                    {Object.entries(data)
                      .filter(([key]) => !excludeColumns.includes(key))
                      .map(([key, value], idx) => (
                        <p key={idx}>{value ? value : "Null"}</p>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        );
      default:
        return (
          <div>
            <p>Unknown item</p>
          </div>
        );
    }
  };

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
          <button className="download-button" onClick={downloadJSON}>
            <i className="fa fa-download"></i>
          </button>
          <div className="popup-content">
            <div>
              {model_data.length > 0 ? (
                model_data.map((item, index) => (
                  <div key={index}>{renderContent(item, index)}</div>
                ))
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

export default ModelCardPopup;
