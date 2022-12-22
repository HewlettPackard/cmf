#
FROM python:3.8

#
WORKDIR /cmf-server

RUN mkdir -p /cmf-server/data

#
COPY ./server/requirements.txt /cmf-server/requirements.txt


#
COPY ./Requirements.txt /cmf-server/Requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /cmf-server/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /cmf-server/Requirements.txt

#
COPY ./setup.py  /cmf-server/setup.py

COPY ./cmflib /cmf-server/cmflib
# Install cmflib
RUN python /cmf-server/setup.py bdist_wheel

#
RUN pip install /cmf-server/dist/*
 
#
COPY ./server/app /cmf-server/server/app

#

#
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "80"]
