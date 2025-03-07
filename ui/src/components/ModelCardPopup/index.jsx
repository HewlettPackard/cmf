import React from "react";

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
            <p className="font-bold my-2.5">Model's Data</p>
            <br />
            {item.length > 0 &&
              item.map((data, i) => (
                <div key={i} className="flex justify-between mb-2.5 text-left">
                  <div className="flex-1 font-bold bg-gray-200 p-2.5 rounded-l-md flex flex-col ">
                    {Object.keys(data)
                      .filter((key) => !excludeColumns.includes(key))
                      .map((key, idx) => (
                        <p className="font-bold my-2.5" key={idx}>{renameKey(key)}:</p>
                      ))}
                  </div>
                  <div className="flex-2 bg-custom-light-blue p-2.5 rounded-l-md text-left flex flex-col ">
                    {Object.entries(data)
                      .filter(([key]) => !excludeColumns.includes(key))
                      .map(([key, value], idx) => (
                        <p className="font-bold my-2.5" key={idx}>{value ? value : "Null"}</p>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        );
      case 1:
        const exe_headers = item.length > 0 ? Object.keys(item[0]) : [];
        return (
          <div className="max-h-[400px] mt-5 max-w-full overflow-y-auto overflow-x-auto ">
            <hr className="my-5"/>
            <p className="font-bold my-2.5">List of executions in which model has been used</p>
            <br />
            <table className="w-full border-collapse overflow-auto bg-custome-light-blue">
              <thead>
                <tr>
                  {exe_headers.map((header, index) => (
                    <th scope="col" key={index} className="border border-solid border-gray-300 p-2 text-left bg-gray-200 font-bold">
                      {renameKey(header)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {item.length > 0 &&
                  item.map((data, i) => (
                    <tr key={i} className="even:bg-gray-100 hover:bg-gray-200">
                      {exe_headers.map((header, index) => (
                        <td key={index} className="border border-solid border-gray-300 p-2 text-left">{data[header]}</td>
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
            <hr className="my-5"/>
            <p className="font-bold my-2.5">List of input artifacts for the model</p>
            <br />
            {item.length > 0 &&
              item.map((data, i) => (
                <div key={i} className="flex justify-between mb-2.5 text-left">
                  <div className="flex-1 font-bold bg-gray-200 p-2.5 rounded-l-md flex flex-col ">
                    {Object.keys(data)
                      .filter((key) => !excludeColumns.includes(key))
                      .map((key, idx) => (
                        <p className="font-bold my-2.5" key={idx}>{renameKey(key)}:</p>
                      ))}
                  </div>
                  <div className="flex-2 bg-custom-light-blue p-2.5 rounded-l-md text-left flex flex-col ">
                    {Object.entries(data)
                      .filter(([key]) => !excludeColumns.includes(key))
                      .map(([key, value], idx) => (
                        <p className="font-bold my-2.5" key={idx}>{value ? value : "Null"}</p>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        );
      case 3:
        return (
          <div>
            <hr className="my-5"/>
            <p className="font-bold my-2.5">List of output artifacts for the model</p>
            <br />
            {item.length > 0 &&
              item.map((data, i) => (
                <div key={i} className="flex justify-between mb-2.5 text-left">
                  <div className="flex-1 font-bold bg-gray-200 p-2.5 rounded-l-md flex flex-col ">
                    {Object.keys(data)
                      .filter((key) => !excludeColumns.includes(key))
                      .map((key, idx) => (
                        <p className="font-bold my-2.5" key={idx}>{renameKey(key)}:</p>
                      ))}
                  </div>
                  <div className="flex-2 bg-custom-light-blue p-2.5 rounded-l-md text-left flex flex-col ">
                    {Object.entries(data)
                      .filter(([key]) => !excludeColumns.includes(key))
                      .map(([key, value], idx) => (
                        <p className="font-bold my-2.5" key={idx}>{value ? value : "Null"}</p>
                      ))}
                  </div>
                </div>
              ))}
          </div>
        );
      default:
        return (
          <div>
            <p className="font-bold my-2.5">Unknown item</p>
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
      <div className="fixed top-0 left-0 w-full h-full bg-black bg-opacity-50 flex justify-center items-center"> 
        <div className="relative bg-white p-5 rounded-lg w-11/12 max-w-3xl max-h-[90vh] shadow-md overflow-y-auto">
          {/* Close Button */}
          <button 
            onClick={onClose} 
            className="absolute top-2 right-2 bg-gray-500 text-white border-2 border-black rounded-full px-2.5 py-1 text-xs cursor-pointer">
            X
          </button>
          {/* Download Button */}
          <button 
            className="absolute top-2 right-10 bg-white text-gray-600 border-none cursor-pointer w-[40px] h-[40px] flex items-center justify-center" 
            onClick={downloadJSON}>
            <i className="fa fa-download"></i>
          </button>
          <div className="mt-5">
            <div>
              {model_data.length > 0 ? (
                model_data.map((item, index) => (
                  <div key={index}>{renderContent(item, index)}</div>
                ))
              ) : (
                <p className="font-bold my-2.5">No items available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ModelCardPopup;
