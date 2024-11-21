class StatusCodes:
    codes = {
        0: "Operation completed successfully.",
        10: "File '{filename}' downloaded successfully.",
        20: "Artifact '{artifact_name}' processed successfully.",
        1: "Generic failure.",
        11: "Failed to download file '{filename}'.",
        21: "Failed to process artifact '{artifact_name}'.",
    }

    @staticmethod
    def get_message(code, **kwargs):
        """
        Retrieve the message for a given status code, formatting it with dynamic data.
        """
        template = StatusCodes.codes.get(code, "Unknown status code.")
        return template.format(**kwargs)