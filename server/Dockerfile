# Use python 3.8-slim-buster as base image.
FROM python:3.8-slim-buster

# Create cmf-server directory.
WORKDIR /cmf-server

# Execute mkdir command to create data folder inside cmf-server directory.
RUN mkdir -p /cmf-server/data

# Copy the requirements.txt file from server to cmf-server.
COPY ./server/requirements.txt /cmf-server/requirements.txt

# Install requirements.txt
RUN pip install --no-cache-dir --upgrade -r /cmf-server/requirements.txt

# Copy the setup.py file to cmf-server
COPY ./setup.py  /cmf-server/setup.py

# Copy the cmflib file to cmf-server
COPY ./cmflib /cmf-server/cmflib

# Install cmflib
RUN python /cmf-server/setup.py bdist_wheel

#
RUN pip install /cmf-server/dist/*
 
# Copy the app file from server to cmf-server/server
COPY ./server/app /cmf-server/server/app

# Run the server with uvicorn
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "80"]

