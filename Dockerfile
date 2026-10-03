FROM quay.io/redhat-services-prod/app-sre-tenant/er-base-terraform-main/er-base-terraform-main:0.6.0-20@sha256:96411f9c82c04a05b73de5717a22f2114558622158cf3ad72cc04df4374681f9 AS base
# keep in sync with pyproject.toml
LABEL konflux.additional-tags="0.3.0"
ENV TERRAFORM_MODULE_SRC_DIR="./module"

FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.12.22@sha256:f513a91fc62fe7c17567eee97230dd198e43edb8a9fbecca843714a4358fe1bc /uv /bin/uv

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
