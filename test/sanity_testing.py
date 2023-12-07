import os
import sys
import json
import shutil
import subprocess

if __name__ == "__main__":
    try:
       client_test_suite = 'client_test_suite.py'
       server_test_suite = 'server_api_endpoints_test_suite.py'

       subprocess.run(['python', client_test_suite])
       subprocess.run(['python', server_test_suite])


    except Exception as e:
        print(f"An error occurred: {e}")



