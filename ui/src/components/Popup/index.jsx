import React from 'react';
import './index.css'; // Optional: For styling the popup

const Popup = ({ show, artifacts, onClose }) => {
    if (!show) {
        return null;
    }

    // find the uri value from artifacts
    const findUri = () => {
        const item = artifacts.find(entry => entry.uri);
        return item ? item.uri : 'default';
    }

    // create filename based on uri
    const createFilename = (uri) => {
        return `model_card_${uri}.json`;
    }
    
    const downloadJSON = () => {
       const uri = findUri();
       const filename = createFilename(uri);

       const jsonString = JSON.stringify(artifacts, null, 2);
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

    return (
        <>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css" />
        <div className="popup-overlay">
            <div className="popup">
                <button onClick={onClose} className="close-button">X</button>	
                <button className="download-button" onClick={downloadJSON}><i class="fa fa-download"></i></button>
                <div className="popup-content">
                   {artifacts.length > 0 && artifacts.map((data, index) => (
                      <div key={index} className="popup-row">
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
                   </div>
                    ))} 
                </div>
            </div>
        </div>
	</>
    );
};

export default Popup;
