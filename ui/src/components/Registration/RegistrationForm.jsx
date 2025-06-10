import React, { useState } from 'react';
import FastAPIClient from '../../client';
import config from '../../config';

const client = new FastAPIClient(config);

const RegistrationForm = () => {
    const [formData, setFormData] = useState({
        serverName: '',
        addressType: 'ipAddress', // Default to IP Address
        ipAddress: '',
        hostName: '',
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
        callRegistrationAPI();
    };

    const validateIPAddress = (ip) => {
        const ipRegex = /^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    };

    const callRegistrationAPI = () => {
        const { serverName, addressType, ipAddress, hostName } = formData;

        if (addressType === 'ipAddress' && !validateIPAddress(ipAddress)) {
            alert('Invalid IP Address');
            return;
        }

        const addressValue = addressType === 'ipAddress' ? ipAddress : hostName;

        client.getServerRegistration(serverName, addressValue)
            .then((data) => {
                if (data && typeof data === 'object' && 'message' in data) {
                    alert(data.message);
                } else {
                    alert('Unexpected response from server.');
                }

                // Reset form fields
                setFormData({
                    serverName: '',
                    addressType: 'ipAddress',
                    ipAddress: '',
                    hostName: '',
                });
            })
            .catch((error) => {
                console.error('Error while registering server:', error);

                if (error.response?.data?.detail) {
                    alert(`Error: ${error.response.data.detail}`);
                } else {
                    alert('Failed to register server. Please try again.');
                }
            });
    };

    return (
        <form onSubmit={handleSubmit}>
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
                <label>
                    <input
                        type="radio"
                        name="addressType"
                        value="ipAddress"
                        checked={formData.addressType === 'ipAddress'}
                        onChange={handleChange}
                    />
                    IP Address
                </label>
                <label style={{ marginLeft: '16px' }}>
                    <input
                        type="radio"
                        name="addressType"
                        value="hostName"
                        checked={formData.addressType === 'hostName'}
                        onChange={handleChange}
                    />
                    Host Name
                </label>
            </div>
            <div style={{ marginBottom: '16px' }}>
                <label htmlFor={formData.addressType}>
                    {formData.addressType === 'ipAddress' ? 'IP Address: ' : 'Host Name: '}
                </label>
                <input
                    type="text"
                    id={formData.addressType}
                    name={formData.addressType}
                    value={formData[formData.addressType]}
                    onChange={handleChange}
                    style={{ border: '1px solid #ccc', borderRadius: '8px' }}
                    required
                />
            </div>
            <button
                type="submit"
                className="bg-gray-300 hover:bg-gray-400 text-black font-bold py-2 px-4 rounded m-2 border-5">
                Submit
            </button>
        </form>
    );
};

export default RegistrationForm;