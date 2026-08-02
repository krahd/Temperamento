SOURCE_DATE_EPOCH ?= 1784678400
FORCE_SOURCE_DATE ?= 1
MUSESCORE_FORMATS ?= mscz,pdf,mp3
export SOURCE_DATE_EPOCH FORCE_SOURCE_DATE

.PHONY: examples render-examples example-assets metadata site format-check lint typecheck quality test coverage package package-smoke smoke verify reproducibility release-assets clean

examples:
	python scripts/generate_examples.py
	python scripts/generate_showcase.py
	python scripts/generate_directions.py

render-examples:
	python scripts/render_examples_musescore.py --formats "$(MUSESCORE_FORMATS)"

example-assets: examples
	$(MAKE) render-examples

metadata:
	python scripts/export_metadata.py

site:
	python scripts/build_site.py

format-check:
	python -m ruff format --check src scripts tests

lint:
	python -m ruff check src scripts tests

typecheck:
	python -m mypy

quality: format-check lint typecheck

test:
	python -m pytest

coverage:
	python -m coverage erase
	python -m coverage run --branch -m pytest
	python -m coverage report --fail-under=95

package:
	rm -rf dist
	python -m build

package-smoke: package
	@repo="$$(pwd)"; tmp="$$(mktemp -d)"; trap 'rm -rf "$$tmp"' EXIT; \
		python -m venv "$$tmp/venv"; \
		"$$tmp/venv/bin/python" -m pip install --no-index --no-deps dist/*.whl; \
		cd "$$tmp"; \
		"$$tmp/venv/bin/temperamento" --version; \
		"$$tmp/venv/bin/temperamento" validate "$$repo/examples/arithmetic/add/add.musicxml"; \
		"$$tmp/venv/bin/temperamento" inspect "$$repo/examples/arithmetic/add/add.musicxml" --execute; \
		"$$tmp/venv/bin/temperamento" run "$$repo/examples/showcase/hello-world-prelude/hello-world-prelude.musicxml" --output text

smoke:
	PYTHONPATH=src python -m temperamento.cli --version
	PYTHONPATH=src python -m temperamento.cli doctor --json
	PYTHONPATH=src python -m temperamento.cli validate examples/arithmetic/add/add.musicxml
	PYTHONPATH=src python -m temperamento.cli compile examples/arithmetic/add/add.musicxml
	PYTHONPATH=src python -m temperamento.cli inspect examples/arithmetic/add/add.musicxml --execute
	PYTHONPATH=src python -m temperamento.cli run examples/showcase/hello-world-prelude/hello-world-prelude.musicxml --output text

verify:
	$(MAKE) quality
	$(MAKE) examples
	$(MAKE) coverage
	$(MAKE) metadata
	$(MAKE) site
	$(MAKE) package-smoke
	$(MAKE) smoke

reproducibility: verify
	git diff --exit-code -- examples spec/opcode-table.json _site

release-assets: reproducibility
	python scripts/build_release.py

clean:
	rm -rf .coverage .mypy_cache .pytest_cache .ruff_cache _site build dist release *.egg-info src/*.egg-info
	find src scripts tests -type d -name __pycache__ -prune -exec rm -rf {} +
