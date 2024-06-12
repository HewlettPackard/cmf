import React from 'react';
import './index.css'; // Optional: For styling the popup

const Popup = ({ show, model_data, onClose }) => {
    if (!show) {
        return null;
    }

    // find the uri value from artifacts
    const findUri = () => {
        const item = model_data[0].find(entry => entry.uri);
        return item ? item.uri : 'default';
    }

    // create filename based on uri
    const createFilename = (uri) => {
        return `model_card_${uri}.json`;
    }
    
    const downloadJSON = () => {
       const uri = findUri();
       const filename = createFilename(uri);

       const jsonString = JSON.stringify(model_data, null, 2);
       const blob = new Blob([jsonString], { type: 'application/json'}); 
    
       const url = URL.createObjectURL(blob);
       const link = document.createElement('a');
       link.href = url;
       link.download = filename;
       document.body.appendChild(link);
       link.click();
       document.body.removeChild(link);
       URL.revokeObjectURL(url);   
    };

    const renderContent = (item, index) => {
      switch (index) {
        case 0:
          return (
            <div>
            <p>Model's Data</p><br/>
            {item.length > 0 && item.map((data, i) => (
                                     <div key={i} className="popup-row">
                                         <div className="popup-labels">
                                            {Object.keys(data).map((key, idx) => (
                                                 <p key={idx}>{key}:</p>
                                            ))}
                                         </div>
                                      <div className="popup-data">
                                         {Object.values(data).map((value, idx) => (
                                            <p key={idx}>{value ? value : "Null"}</p>
                                         ))}
                                      </div>
                                 </div>))}
              <hr/> 
              </div>
          );
        case 1:
          return (
            <div className="table-container">
              <p>List of executions in which model has been used</p><br/>
			<table className="table">
                          <thead className="thead">
                            <tr>
                              <th scope="col">execution_id</th>
                              <th scope="col">Type</th>
                              <th scope="col">pipeline</th>
                              <th scope="col">stage</th>
                            </tr>
                          </thead>
                          <tbody className="tbody">
                            {item.length > 0 && item.map((data, i) => (
                            <tr>
                              <td>{data.execution_id}</td>
                              <td>{data.Type}</td>
                              <td>{data.pipeline}</td>
                              <td>{data.stage}</td>
                            </tr>
                            ))}
                          </tbody>
                        </table>
            <hr/>
            </div>
          );
        case 2:
          return (
            <div className="table-container">
              <p>List of input and output artifacts for the model</p><br/>
                      <table className="table">
                          <thead className="thead">
                            <tr>
                              <th scope="col">id</th>
                              <th scope="col">create_time_since_epoch</th>
                              <th scope="col">custom_properties_avg_prec</th>
                              <th scope="col">custom_properties_original_create_time_since_epoch</th>
                              <th scope="col">custom_properties_roc_auc</th>
                              <th scope="col">event</th>
                              <th scope="col">name</th>
                              <th scope="col">last_update_time_since_epoch</th>
                              <th scope="col">metrics_name</th>
                              <th scope="col">model_framework</th>
                              <th scope="col">model_name</th>
                              <th scope="col">model_type</th>
                              <th scope="col">type</th>
                              <th scope="col">uri</th>
                            </tr>
                          </thead>
                          <tbody className="tbody">
                            {item.length > 0 && item.map((data, i) => (
                            <tr>
                              <td>{data.id}</td>
                              <td>{data.create_time_since_epoch}</td>
                              <td>{data.custom_properties_avg_prec}</td>
                              <td>{data.custom_properties_original_create_time_since_epoch}</td>
                              <td>{data.custom_properties_roc_auc}</td>
                              <td>{data.event}</td>
                              <td>{data.name}</td>
                              <td>{data.last_update_time_since_epoch}</td>
                              <td>{data.metrics_name}</td>
                              <td>{data.model_framework}</td>
                              <td>{data.model_name}</td>
                              <td>{data.model_type}</td>
                              <td>{data.type}</td>
                              <td>{data.uri}</td>
                            </tr>
                            ))}
                          </tbody>
                        </table>
              <hr/>
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
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css" />
        <div className="popup-overlay">
            <div className="popup">
                <button onClick={onClose} className="close-button">X</button>	
                <button className="download-button" onClick={downloadJSON}><i class="fa fa-download"></i></button>
                <div className="popup-content">
                      <div>
                          {model_data.length > 0 ? (
                            model_data.map((item, index) => (
                              <div key={index}>
                                 {renderContent(item, index)}
                              </div>
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

export default Popup;

