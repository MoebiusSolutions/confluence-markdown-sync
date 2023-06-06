ARG BASE_DOCKER_REGISTRY=
ARG BASE_DOCKER_IMAGE=python:3.8
FROM ${BASE_DOCKER_REGISTRY}${BASE_DOCKER_IMAGE}

ENV PYTHON_HOME=/opt/confluence-sync

# Install prereqs to python dependency pull
RUN install -o root -g root -m 0755 -d "$PYTHON_HOME" && \
    # The existence of this dir causes pipenv to install libs to a local dir
    install -o root -g root -m 0755 -d "$PYTHON_HOME/.venv" && \
    pip3 install pipenv
WORKDIR "$PYTHON_HOME"
COPY Pipfile.lock .
COPY Pipfile .

# Pull python dependencies
RUN pipenv install

# Load source code
COPY main.py .

# Update PATH
#ENV PATH="$PYTHON_HOME/bin:${PATH}"

ENTRYPOINT [ "pipenv", "run", "python3", "main.py" ]
