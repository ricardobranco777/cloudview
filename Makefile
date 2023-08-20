FILES=*.py */*.py

.PHONY: all
all: flake8 pylint test mypy

.PHONY: flake8
flake8:
	@flake8 --ignore=E501 $(FILES) tests/*.py

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
