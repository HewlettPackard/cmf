# Use python 3.8-slim-buster as base image.
FROM python:3.8-slim-buster

# Create a cmf-server directory.
WORKDIR /cmf-server

# Execute the mkdir command to create a data folder inside the cmf-server directory.
RUN mkdir -p /cmf-server/data

# folder for static files
RUN mkdir -p /cmf-server/data/static

# Copy the requirements.txt file from the server to the cmf-server.
COPY ./server/requirements.txt /cmf-server/requirements.txt

# Install requirements.txt
RUN pip install --no-cache-dir --upgrade -r /cmf-server/requirements.txt

RUN pip uninstall -y uvicorn

RUN pip install uvicorn[standard]

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

RUN cd /cmf-server/data/static

ENV NEO4J_URI=""
ENV NEO4J_USER_NAME=""
ENV NEO4J_PASSWD=""

