#!/usr/bin/env bash
set -e

rm -rf dist/lambda-package || true
mkdir -p dist/lambda-package
cp -r ./hydrocron-api dist/lambda-package/
touch dist/lambda-package/hydrocron-api/__init__.py
