#
FROM python:3.7

#
WORKDIR /code

#
COPY ./server/requirements.txt /code/requirements.txt


#
COPY ./Requirements.txt /code/Requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#
RUN pip install --no-cache-dir --upgrade -r /code/Requirements.txt

#
COPY ./setup.py  /code/setup.py

# Install cmflib
RUN python /code/setup.py bdist_wheel

#
RUN pip install /code/dist/*
 
#
COPY ./server/app /code/server/app

#
COPY ./cmflib /code/cmflib

#
CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "80"]
