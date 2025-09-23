
import React, { useState } from 'react';
import FastAPIClient from '../../client';
import config from '../../config';

const client = new FastAPIClient(config);

const RegistrationForm = () => {
    const [formData, setFormData] = useState({
        serverName: '',
        serverUrl: '',
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

    const validateUrl = (url) => {
        // Basic URL validation
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    };

    const callRegistrationAPI = () => {
        const { serverName, serverUrl } = formData;

        if (!serverName.trim()) {
            alert('Server name is required.');
            return;
        }
        if (!validateUrl(serverUrl)) {
            alert('Invalid server URL.');
            return;
        }

        // API expects serverName and serverUrl
        client.getServerRegistration(serverName, serverUrl)
            .then((data) => {
                if (data && typeof data === 'object' && 'message' in data) {
                    alert(data.message);
                } else {
                    alert('Unexpected response from server.');
                }
                setFormData({
                    serverName: '',
                    serverUrl: '',
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
        <form onSubmit={handleSubmit} className="max-w-md mx-auto mt-8 p-8 bg-white rounded-lg shadow-md">
            <h2 className="text-2xl font-bold mb-6 text-center">Register Server</h2>
            <div className="mb-6">
                <label htmlFor="serverName" className="block text-gray-700 font-semibold mb-2">Server Name</label>
                <input
                    type="text"
                    id="serverName"
                    name="serverName"
                    value={formData.serverName}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="Enter server name"
                    required
                />
            </div>
            <div className="mb-6">
                <label htmlFor="serverUrl" className="block text-gray-700 font-semibold mb-2">Server URL</label>
                <input
                    type="text"
                    id="serverUrl"
                    name="serverUrl"
                    value={formData.serverUrl}
                    onChange={handleChange}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
                    placeholder="http://localhost:8080"
                    required
                />
            </div>
            <button
                type="submit"
                className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-2 px-4 rounded-lg transition duration-200"
            >
                Submit
            </button>
        </form>
    );
};

export default RegistrationForm;