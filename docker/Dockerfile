# Define global args
ARG FUNCTION_DIR="/function"

FROM public.ecr.aws/lambda/python:3.12 AS build_image
ARG FUNCTION_DIR
# Pinned Poetry; CI passes build.yml's POETRY_VERSION, default is for local builds
ARG POETRY_VERSION=2.3.2
ENV BUILD_DIR=/hydrocron

RUN curl -sSL https://install.python-poetry.org | python3 - --version ${POETRY_VERSION}

WORKDIR $BUILD_DIR
COPY ./hydrocron ./hydrocron

COPY poetry.lock pyproject.toml README.md ./
# Create the venv without pip: not a runtime dep, and scanners flag its vendored libs
ENV POETRY_VIRTUALENVS_OPTIONS_NO_PIP=true
RUN ~/.local/bin/poetry lock
RUN mkdir -p "${FUNCTION_DIR}" && \
    ~/.local/bin/poetry install --only main --sync && \
    cp -r $(~/.local/bin/poetry env list --full-path | awk '{print $1}')/lib/python*/site-packages/* ${FUNCTION_DIR} && \
    cp -r ./hydrocron ${FUNCTION_DIR} && \
    touch ${FUNCTION_DIR}/hydrocron/__init__.py

COPY docker/docker-entrypoint.sh ${FUNCTION_DIR}/bin/docker-entrypoint.sh
RUN chmod 755 ${FUNCTION_DIR}/bin/docker-entrypoint.sh

FROM public.ecr.aws/lambda/python:3.12
ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

# Apply OS security fixes the AWS base image hasn't picked up yet (repo is locked to the base's release without --releasever)
RUN dnf --releasever=latest upgrade -y && dnf clean all

COPY --from=build_image ${FUNCTION_DIR} ${LAMBDA_TASK_ROOT}
ENV PATH="${PATH}:${LAMBDA_TASK_ROOT}/bin"

CMD [ "hydrocron.api.controllers.timeseries.lambda_handler" ]