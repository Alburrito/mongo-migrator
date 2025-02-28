run=poetry run

init:
	poetry install

format:
	$(run) black src tests

style:
	$(run) flake8 src tests

test:
	$(run) pytest

test-cov:
	$(run) pytest --cov=src --cov-report=term-missing --cov-report=html

tox:
	$(run) tox -q

check: format style tox
	@echo "All checks passed"

publish:
	poetry build
	poetry publish

.PHONY: init format style test test-cov check tox publish