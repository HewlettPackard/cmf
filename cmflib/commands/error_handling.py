import sys
ERROR_CODES = {
    0: "Success",                             
    1: "Missing required argument",           
    2: "File not found",                      
    3: "Invalid argument value",              
    4: "Operation failed",                    
    5: "Permission denied",                   
    6: "No executions found.",                       
    7: "Pipeline_name doesnt exist",
    8: "MinioS3 server failed to start!!!",
    9: "Bucket doesn't exists",
    10:"object {temp_object_name} downloaded at {temp_download_loc}.",
    11:"object {object_name} downloaded at {download_loc}.",
    12: "Unknown error",
}     
 
def get_error_message(code):
    return ERROR_CODES.get(code, ERROR_CODES[12])

def handle_error(return_code, **kwargs):
    error_message = get_error_message(return_code)
    if return_code==11:
        temp_object_name=kwargs["temp_object_name"]
        temp_download_loc=kwargs["temp_download_loc"]
        error_message=f"object {temp_object_name} downloaded at {temp_download_loc}."
    
    print(f"Error: {error_message}")
    sys.exit(return_code) 