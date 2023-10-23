# Define global args
ARG FUNCTION_DIR="/home/dockeruser/app"
ARG GDAL_VERSION="3.6.3"

FROM osgeo/gdal:ubuntu-small-${GDAL_VERSION} as build-image

# Include global arg in this stage of the build
ARG FUNCTION_DIR

# Install aws-lambda-cpp build dependencies
RUN apt-get update && \
  apt-get install -y \
  python3-pip \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev

RUN adduser --quiet --disabled-password --shell /bin/sh --home /home/dockeruser --gecos "" --uid 1000 dockeruser
USER dockeruser
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /home/dockeruser
COPY ./hydrocron_api ./hydrocron_api

COPY --chown=dockeruser poetry.lock pyproject.toml README.md ./
RUN /home/dockeruser/.local/bin/poetry lock --no-update
RUN mkdir -p "${FUNCTION_DIR}" && \
    /home/dockeruser/.local/bin/poetry install --only main --sync && \
    cp -r $(/home/dockeruser/.local/bin/poetry env list --full-path | awk '{print $1}')/lib/python*/site-packages/* ${FUNCTION_DIR} && \
    cp -r ./hydrocron_api ${FUNCTION_DIR} && \
    touch ${FUNCTION_DIR}/hydrocron_api/__init__.py && \
    pip install --target ${FUNCTION_DIR} awslambdaric


FROM osgeo/gdal:ubuntu-small-${GDAL_VERSION}
ARG FUNCTION_DIR
RUN adduser --quiet --disabled-password --shell /bin/sh --home /home/dockeruser --gecos "" --uid 1000 dockeruser
USER dockeruser
ENV HOME /home/dockeruser
WORKDIR ${FUNCTION_DIR}

COPY --chown=1000:1000 --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}
# (Optional) Add Lambda Runtime Interface Emulator and use a script in the ENTRYPOINT for simpler local runs
ADD --chown=1000:1000 https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /home/dockeruser/.local/bin/aws-lambda-rie
COPY --chown=1000:1000 docker/docker-entrypoint.sh /home/dockeruser/.local/bin/
RUN chmod 755 /home/dockeruser/.local/bin/aws-lambda-rie /home/dockeruser/.local/bin/docker-entrypoint.sh && \
    touch hydrocron_api/__init__.py
ENTRYPOINT [ "/home/dockeruser/.local/bin/docker-entrypoint.sh" ]
CMD [ "hydrocron_api.controllers.timeseries.lambda_handler" ]