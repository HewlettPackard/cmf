import React from "react";
import DetailDrawer from "../../DetailDrawer";

/**
 * Artifact-specific detail drawer — reuses the shared DetailDrawer layout.
 *
 * Props:
 *  - artifact      {object}   — the artifact data object
 *  - artifactType  {string}   — e.g. "Dataset", "Model", "Metrics"
 *  - onClose       {function} — called to dismiss the drawer
 */
const ArtifactDetailDrawer = ({ artifact, artifactType, onClose }) => {
    if (!artifact) return null;

    const allProps = Array.isArray(artifact.artifact_properties)
        ? artifact.artifact_properties
        : (() => {
            try {
                return JSON.parse(artifact.artifact_properties || "[]");
            } catch {
                return [];
            }
        })();

    const getProp = (name) => {
        const match = allProps.filter((p) => p.name === name).map((p) => p.value);
        return match.length > 0 ? match.join(", ") : "N/A";
    };

    const formatDate = (timestamp) => {
        if (!timestamp || timestamp === "N/A") return "N/A";
        try {
            return new Date(parseInt(timestamp)).toLocaleString();
        } catch {
            return timestamp;
        }
    };

    const summaryFields = [
        { label: "Type", value: artifactType, color: "teal" },
        { label: "URI", value: artifact.uri, color: "blue" },
        { label: "Created", value: formatDate(artifact.create_time_since_epoch), color: "indigo" },
        { label: "Git Repo", value: getProp("git_repo"), color: "purple" },
        { label: "Commit", value: getProp("Commit"), color: "green" },
    ];

    return (
        <DetailDrawer
            title="Artifact Details"
            subtitle={<>ID: <span className="font-mono font-semibold">{artifact.artifact_id || "—"}</span></>}
            summaryFields={summaryFields}
            allProperties={allProps}
            onClose={onClose}
        />
    );
};

export default ArtifactDetailDrawer;
