FILES=*.py */*.py

.PHONY: all
all: black flake8 pylint test mypy

.PHONY: black
black:
	@black --check .

.PHONY: flake8
flake8:
	@flake8 --ignore=E501,W503 $(FILES) tests/*.py

.PHONY: pylint
pylint:
	@pylint --disable=line-too-long,duplicate-code,too-few-public-methods $(FILES) tests/*.py

.PHONY: test
test:
	@pytest -v

.PHONY: mypy
mypy:
	@mypy --disable-error-code=attr-defined --exclude tests/ --ignore-missing-imports $(FILES)

.PHONY: clean
clean:
	@rm -rf dist/ build/ *.egg-info
