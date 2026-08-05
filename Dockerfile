FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.6.0-11@sha256:497aa38497e9af1610948012e50d975baa1f99db3b1bba8989bb28b2df57c92c AS base
# keep in sync with pyproject.toml
LABEL konflux.additional-tags="0.3.0"
ENV TERRAFORM_MODULE_SRC_DIR="./module"

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.1@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /bin/uv

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

COPY Makefile Dockerfile ./
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
