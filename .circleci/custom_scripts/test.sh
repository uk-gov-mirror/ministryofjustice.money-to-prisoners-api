#!/usr/bin/env sh

. ${CIRCLE_WORKING_DIRECTORY}/.circleci/custom_scripts/common.sh
. ${CIRCLE_WORKING_DIRECTORY}/.circleci/custom_scripts/start_db_container.sh

docker load -i "${CIRCLE_WORKING_DIRECTORY}/imagedump/${tag}.tar.gz"

TESTMODULES=$(circleci tests glob "mtp_api/apps/**/tests/test_*.py" | circleci tests split --split-by=timings | tr "/" "." | sed 's/.py//g')

docker run \
  --name ${app} \
  -e DJANGO_SETTINGS_MODULE=mtp_api.settings.ci \
  -e DB_PASSWORD=postgres \
  -e DB_USERNAME=postgres \
  -e DB_HOST=postgres \
  -e TESTMODULES="$TESTMODULES" \
  --link postgres \
  ${tag} \
  /bin/bash -cx '/app/venv/bin/pip install -r requirements/ci.txt && cd /app && venv/bin/python manage.py test ${TESTMODULES[*]} --verbosity=2'
