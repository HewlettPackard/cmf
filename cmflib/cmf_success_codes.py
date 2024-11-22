class StatusCodes:
    def __init__(self):
        self.codes = {
        0: "Operation completed successfully.",
        2: "object {object_name} downloaded at {download_loc}.",
        10: "File '{filename}' downloaded successfully.",
        20: "Artifact '{artifact_name}' processed successfully.",
        1: "Generic failure.",
        11: "Failed to download file '{filename}'.",
        21: "Failed to process artifact '{artifact_name}'.",
        22: "object {object_name} is not downloaded."
        }

    
    def get_message(self,code, **kwargs):
        """
        Retrieve the message for a given status code, formatting it with dynamic data.
        """
        print(code,"inside status code")
        template = self.codes.get(code, "Unknown status code.")
        print(type(template))
        return code, template.format(**kwargs)