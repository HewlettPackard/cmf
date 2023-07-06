import React from "react";

const LineageImage = ({ imageSrc, activeTab }) => {
  return (
    <div className="container justify-center items-center mx-auto px-4">
      <div className="image-container">
        {imageSrc ? (
          <img src={imageSrc} alt={`Pipeline ${activeTab + 1}`} />
        ) : (
          <div>No image selected</div>
        )}
      </div>
    </div>
  );
};

export default LineageImage;
