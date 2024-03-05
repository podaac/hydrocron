# Define global args
ARG FUNCTION_DIR="/function"

FROM public.ecr.aws/lambda/python:3.10 as build_image
ARG FUNCTION_DIR
ENV BUILD_DIR=/hydrocron

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $BUILD_DIR
COPY ./hydrocron ./hydrocron

COPY poetry.lock pyproject.toml README.md ./
RUN ~/.local/bin/poetry lock --no-update
RUN mkdir -p "${FUNCTION_DIR}" && \
    ~/.local/bin/poetry install --only main --sync && \
    cp -r $(~/.local/bin/poetry env list --full-path | awk '{print $1}')/lib/python*/site-packages/* ${FUNCTION_DIR} && \
    cp -r ./hydrocron ${FUNCTION_DIR} && \
    touch ${FUNCTION_DIR}/hydrocron/__init__.py

COPY docker/docker-entrypoint.sh ${FUNCTION_DIR}/bin/docker-entrypoint.sh
RUN chmod 755 ${FUNCTION_DIR}/bin/docker-entrypoint.sh

FROM public.ecr.aws/lambda/python:3.10
ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

COPY --from=build_image ${FUNCTION_DIR} ${LAMBDA_TASK_ROOT}
ENV PATH="${PATH}:${LAMBDA_TASK_ROOT}/bin"

CMD [ "hydrocron.api.controllers.timeseries.lambda_handler" ]