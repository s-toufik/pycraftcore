venv:
	uv venv

clean_dependency_cache:
	uv cache clear

clear_dependency_cache:
	uv cache clear

install:
	uv sync

update_dependency:
ifdef PACKAGE
	uv lock --upgrade-package $(PACKAGE)
else
	uv lock --upgrade
endif
	uv sync

install_dev:
	uv sync --group dev

test:
	uv run pytest

lint:
	uv run ruff check .

fix:
	uv run ruff check --fix .

typecheck:
	uv run ty check

format:
	uv run ruff format .

check:
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test

git_init:
	git init
	git add --all
	git commit -m "init project"
	git checkout -b develop

clean:
	rm -rf dist
	rm -rf src/*.egg-info

build:
	rm -rf dist
	rm -rf src/*.egg-info
	uv build

publish_dev:
	export UV_PUBLISH_TOKEN=$$TEST_PYPI_TOKEN && \
	uv publish --publish-url https://test.pypi.org/legacy/

publish:
	@echo "INFO: Make sure that UV_PUBLISH_TOKEN env variable is set"
	export UV_PUBLISH_TOKEN=$$RELEASE_PYPI_TOKEN && \
	uv publish
