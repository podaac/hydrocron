#!/bin/sh
if [ -z "${AWS_LAMBDA_RUNTIME_API}" ]; then
    exec /home/dockeruser/.local/bin/aws-lambda-rie /usr/bin/python -m awslambdaric $1
else
    exec /usr/bin/python -m awslambdaric $1
fi