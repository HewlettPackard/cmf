import React from "react";
import DetailDrawer from "../../DetailDrawer";

const ExecutionDetailDrawer = ({ execution, onClose }) => {
    if (!execution) return null;

    const allProps = Array.isArray(execution.execution_properties)
        ? execution.execution_properties
        : (() => {
            try {
                return JSON.parse(execution.execution_properties || "[]");
            } catch {
                return [];
            }
        })();

    const getProp = (name) => {
        const match = allProps.filter((p) => p.name === name).map((p) => p.value);
        return match.length > 0 ? match.join(", ") : "N/A";
    };

    const summaryFields = [
        { label: "Context Type", value: getProp("Context_Type"), color: "teal" },
        { label: "Execution", value: getProp("Execution"), color: "blue" },
        { label: "Pipeline Type", value: getProp("Pipeline_Type"), color: "indigo" },
        { label: "Git Repo", value: getProp("Git_Repo"), color: "purple" },
        { label: "Git Start Commit", value: getProp("Git_Start_Commit"), color: "green" },
    ];

    return (
        <DetailDrawer
            title="Execution Details"
            subtitle={<>ID: <span className="font-mono font-semibold">{execution.execution_id || "—"}</span></>}
            summaryFields={summaryFields}
            allProperties={allProps}
            onClose={onClose}
        />
    );
};

export default ExecutionDetailDrawer;
