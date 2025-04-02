import React from 'react';

const RegisteredServers = ({ servers }) => {
    return (
        <div>
            <h2 className="text-lg font-bold mb-4">Registered Servers</h2>
            <ul className="list-disc pl-5">
                {servers.map((server, index) => (
                    <li key={index}>
                        <strong>{server.name}</strong> - {server.ip}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default RegisteredServers;
