#!/bin/bash
set -e

if test -f "logging.ini"; then
    echo "Applying user-provided logging.ini"
else
    echo "Using default logging.ini included with hydrocron. This can be overridden by mounting a python logging configuration file at $(pwd)/logging.ini"
    python - <<'END'
import pkgutil
logging_conf = pkgutil.get_data('hydrocron', 'conf/logging.ini').decode("utf-8")
with open('logging.ini', 'w') as logging_ini:
   logging_ini.write(logging_conf)
END
fi

uvicorn hydrocron.api:app --proxy-headers --host 0.0.0.0 --port 80 --log-config logging.ini