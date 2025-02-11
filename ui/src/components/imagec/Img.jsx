import React from "react";

const Img = ({ className, src="defaultNodata.png", alt="TestImg", ...restProps }) => {
    return (
        <img src={src} alt={alt} className={className} {...restProps} loading={"lazy"}/>
    );
};

export default Img;