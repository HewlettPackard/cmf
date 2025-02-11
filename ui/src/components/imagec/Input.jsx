import React from "react";
import ProtoTypes from "prop-types";

const Input = React.forwardRef(
    (
        { 
             className="",
             name="",
             placeholder="",
             type="text",
             label="",
             onChange,
             prefix,
             suffix,

             ...restProps 
        },
        ref,
    ) => {
        return(
            <label className={`${className} undefined `}>
                {!!label && label}
                {!!prefix && prefix}
                <input ref={ref} name={name} placeholder={placeholder} type={type} onChange={onChange} {...restProps} />
                {!!suffix && suffix}
            </label>
        );
    },
);
    
Input.propTypes = {
    className: ProtoTypes.string,
    name: ProtoTypes.string,
    placeholder: ProtoTypes.string,
    type: ProtoTypes.string,
    label: ProtoTypes.string,
    prefix: ProtoTypes.node,
    suffix: ProtoTypes.node,
};


export default Input;