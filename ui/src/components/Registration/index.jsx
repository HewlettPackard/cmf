import React, { useState } from 'react';
import FastAPIClient from '../../client';
import config from '../../config';

const client = new FastAPIClient(config);

const RegistrationForm = () => {
    const [formData, setFormData] = useState({
        serverName: '',
        ipAddress: '',
    });

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData({
            ...formData,
            [name]: value,
        });
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        console.log('Form Data Submitted:', formData);
        // Add your form submission logic here
    };

    const validateIPAddress = (ip) => {
        const ipRegex = /^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    };

    const callRegistrationAPI = () => {
        if (!validateIPAddress(formData.ipAddress)) {
            alert('Invalid IP Address');
            return;
        }
        
        // Add API call logic here
        client.getServerRegistration(formData.serverName, formData.ipAddress)
        .then((data) => {
            console.log("data:",data);
            alert(data.message);
        });
    };

    return (
        <form 
            onSubmit={handleSubmit} 
        >
            <div style={{ marginBottom: '16px' }}>
                <label htmlFor="serverName">Server Name: </label>
                <input
                    type="text"
                    id="serverName"
                    name="serverName"
                    value={formData.serverName}
                    onChange={handleChange}
                    style={{ border: '1px solid #ccc', borderRadius: '8px' }}
                    required
                />
            </div>
            <div style={{ marginBottom: '16px' }}>
                <label htmlFor="ipAddress">IP Address: </label>
                <input
                    type="text"
                    id="ipAddress"
                    name="ipAddress"
                    value={formData.ipAddress}
                    onChange={handleChange}
                    style={{ border: '1px solid #ccc', borderRadius: '8px' }}
                    required
                />
            </div>
            <button 
            type="submit" 
            onClick={callRegistrationAPI}
            className="bg-violet-500 text-white font-bold py-2 px-4 rounded m-2"
            >Submit</button>
        </form>
    );
};

export default RegistrationForm;