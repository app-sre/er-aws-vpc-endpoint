CONTAINER_ENGINE ?= $(shell which podman >/dev/null 2>&1 && echo podman || echo docker)

.PHONY: format
format:
	uv run ruff check
	uv run ruff format
	terraform fmt module/

.PHONY: image_tests
image_tests:
	# hooks and hooks_lib must be copied
	[ -d "hooks" ]
	[ -d "hooks_lib" ]

	# sources must be copied
	[ -d "$$TERRAFORM_MODULE_SRC_DIR" ]

	# test the terraform providers are downloaded
	[ -d "$$TF_PLUGIN_CACHE_DIR/registry.terraform.io/hashicorp/aws" ]

	# test all files in ./hooks are executable
	[ -z "$(shell for f in hooks/*; do [ ! -x "$$f" ] && [ "$$f" != "hooks/__init__.py" ] && echo not-executable; done)" ]

.PHONY: code_tests
code_tests:
	uv run ruff check --no-fix
	uv run ruff format --check
	uv run mypy
	uv run pytest -vv --cov=er_aws_vpc_endpoint --cov=hooks --cov=hooks_lib --cov-report=term-missing --cov-report xml

.PHONY: terraform_tests
terraform_tests:
	terraform fmt -check -diff "$$TERRAFORM_MODULE_SRC_DIR"

.PHONY: version_test
version_test:
	@pyproject_version="$$(grep -m1 '^version = ' pyproject.toml | cut -d'"' -f2)"; \
	dockerfile_version="$$(grep -m1 'konflux.additional-tags' Dockerfile | cut -d'"' -f2)"; \
	if [ "$$pyproject_version" != "$$dockerfile_version" ]; then \
		echo "version mismatch: pyproject.toml version is '$$pyproject_version' but Dockerfile LABEL konflux.additional-tags is '$$dockerfile_version'. Keep them in sync."; \
		exit 1; \
	fi

.PHONY: test
test: code_tests terraform_tests version_test

.PHONY: in_container_test
in_container_test: image_tests test

.PHONY: build_test
build_test:
	$(CONTAINER_ENGINE) build --progress plain --target test -t er-aws-vpc-endpoint:test .

.PHONY: build
build:
	$(CONTAINER_ENGINE) build --progress plain --target prod -t er-aws-vpc-endpoint:prod .

.PHONY: dev
dev:
	uv sync

.PHONY: generate-variables-tf
generate-variables-tf:
	uv run external-resources-io tf generate-variables-tf er_aws_vpc_endpoint.input.AppInterfaceInput --output module/variables.tf

.PHONY: providers-lock
providers-lock:
	terraform -chdir=module providers lock -platform=linux_amd64 -platform=linux_arm64 -platform=darwin_amd64 -platform=darwin_arm64
