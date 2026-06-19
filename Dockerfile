FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.5.0-10@sha256:a89193c06fa60ab7f0b8f026fcbf8aaf2452ef1b0c494fb7f57e6c3e25dc1ed9 AS base
FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.6.0-1@sha256:f234d99c2970151dc445ecd0870bd320c3ccdb9a9e579f97a84779a640f2f1ee AS base
# keep in sync with pyproject.toml
LABEL konflux.additional-tags="0.2.0"
ENV TERRAFORM_MODULE_SRC_DIR="./module"

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.22@sha256:16b63af0e7342dd372da9ca989ea9fa542fc68f4640972d59a8450a5240fe42e /uv /bin/uv

COPY pyproject.toml uv.lock ./
# Test lock file is up to date
RUN uv lock --locked
# Install dependencies
RUN uv sync --frozen --no-group dev --no-install-project

# Copy source code
COPY README.md ./
COPY er_aws_vpc_endpoint ./er_aws_vpc_endpoint
COPY hooks ./hooks
COPY hooks_lib ./hooks_lib
# Sync the project
RUN uv sync --frozen --no-group dev

COPY --chown=${USER}:root ${TERRAFORM_MODULE_SRC_DIR} ${TERRAFORM_MODULE_SRC_DIR}

# Get the terraform providers
RUN terraform-provider-sync

FROM builder AS test
# install test dependencies
RUN uv sync --frozen

COPY Makefile ./
COPY tests ./tests

RUN make in_container_test

FROM builder AS prod
# get terraform providers
COPY --from=builder ${TF_PLUGIN_CACHE_DIR} ${TF_PLUGIN_CACHE_DIR}
# get our app with the dependencies
COPY --from=builder ${APP} ${APP}

ENV \
    VIRTUAL_ENV="${APP}/.venv" \
    PATH="${APP}/.venv/bin:${PATH}"
