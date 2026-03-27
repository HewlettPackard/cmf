FROM tensorflow/tensorflow:latest

RUN pip install --no-cache-dir tensorboard

CMD ["tensorboard", "--logdir=/logs", "--host", "0.0.0.0", "--path_prefix=/tensorboard", "--port", "6006"]
