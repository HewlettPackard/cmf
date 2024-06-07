import React from 'react';
import './index.css'; // Optional: For styling the popup

const Popup = ({ show, data, onClose }) => {
    if (!show) {
        return null;
    }

    return (
        <div className="popup-overlay">
            <div className="popup">
                <button onClick={onClose} className="close-button">Close</button>
                <div className="popup-content">
                    {data}
                </div>
            </div>
        </div>
    );
};

export default Popup;
