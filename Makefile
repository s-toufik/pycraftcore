venv:
	uv venv

clear_env_cache:
	uv cache clear

install:
	uv sync

install_dev:
	uv sync --group dev

test:
	uv run pytest

lint:
	uv run ruff check .

link:
	uv run pyright .

typing:
	uv run mypy .

format:
	uv run ruff format .

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
