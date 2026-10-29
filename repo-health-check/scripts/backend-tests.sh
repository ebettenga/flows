#!/usr/bin/env bash
# Runs the backend unit suite the way CI does (make ci-test-unit), from the repo root.
#
# CI gives the tests a memcached service and KH_MEMCACHED_HOST=memcached
# (ci/ci.env). Locally the app falls back to localhost, which has no memcached
# inside the api container, so start the compose memcached and point the tests
# at it. Once develop drops memcached (the Redis move), the first command finds
# no such service and is skipped.
set -uo pipefail

docker compose up -d memcached 2>/dev/null || echo "No memcached service in docker-compose.yml; not starting one."

make ci-test-unit \
  CI_EXEC='docker compose exec -T -e KH_SQLALCHEMY_DATABASE_URI=$(CI_TEST_DB_URI) -e KH_TEST_DATABASE=$(CI_TEST_DB) -e KH_MEMCACHED_HOST=memcached api'
