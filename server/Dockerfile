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

# COPY cmflib
COPY ./cmflib /code/cmflib

#
COPY ./server/app /code/app

#
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
