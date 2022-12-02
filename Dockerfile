#Change as necessary: https://jupyter-docker-stacks.readthedocs.io/en/latest/using/selecting.html
#FROM jupyter/datascience-notebook
FROM jupyter/tensorflow-notebook
#FROM jupyter/all-spark-notebook
#FROM jupyter/pyspark-notebook

#FROM nvcr.io/nvidia/tensorflow:21.02-tf1-py3
#FROM nvcr.io/nvidia/pytorch:21.02-py3
#FROM nvcr.io/nvidia/mxnet:21.02-py3
#FROM nvcr.io/nvidia/theano:18.08
#FROM nvcr.io/partners/paddlepaddle:0.11-alpha
#FROM nvcr.io/partners/chainer:4.0.0b1

#Following: https://jupyter-docker-stacks.readthedocs.io/en/latest/using/recipes.html#
ARG NB_USER
ARG NB_UID
ARG NB_GID


# name your environment and choose the python version
#ARG conda_env=python37
#ARG py_ver=3.7

# you can add additional libraries you want mamba to install by listing them below the first line and ending with "&& \"
#RUN mamba create --quiet --yes -p "${CONDA_DIR}/envs/${conda_env}" python=${py_ver} ipython ipykernel && \
#    mamba clean --all -f -y

# create Python kernel and link it to jupyter
#RUN "${CONDA_DIR}/envs/${conda_env}/bin/python" -m ipykernel install --user --name="${conda_env}" && \
#    fix-permissions "${CONDA_DIR}" && \
#    fix-permissions "/home/${NB_USER}"

# any additional pip installs can be added by uncommenting the following line
#RUN "${CONDA_DIR}/envs/${conda_env}/bin/pip" install --quiet --no-cache-dir

# if you want this environment to be the default one, uncomment the following line:

#RUN apt-get update; apt-get install -y build-essential

USER ${NB_USER}

#RUN "${CONDA_DIR}/envs/${conda_env}/bin/pip" install --quiet --no-cache-dir 'flake8==3.9.2' && \

#    fix-permissions "${CONDA_DIR}" && \
#    fix-permissions "/home/${NB_USER}" && \
RUN   mkdir /home/${NB_USER}/cmflib/

COPY --chown=${NB_UID}:${NB_GID} Requirements.txt /home/${NB_USER}/cmflib/
RUN "${CONDA_DIR}/bin/pip" install --no-cache-dir --requirement /home/${NB_USER}/cmflib/Requirements.txt && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

COPY --chown=${NB_UID}:${NB_GID} cmflib /home/${NB_USER}/cmflib/cmflib
COPY --chown=${NB_UID}:${NB_GID} setup.py /home/${NB_USER}/cmflib/setup.py
RUN cd /home/${NB_USER}/cmflib && "${CONDA_DIR}/bin/pip" install --no-cache . && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

#ENV PYTHONPATH "${PYTHONPATH}:/home/${NB_USER}/cmflib"

COPY --chown=${NB_UID}:${NB_GID} examples/example-get-started /home/${NB_USER}/example-get-started


# if you want this environment to be the default one, uncomment the following line:
#RUN echo "conda activate ${conda_env}" >> "${HOME}/.bashrc"

