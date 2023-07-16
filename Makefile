.PHONY: all
all: flake8 pylint test

.PHONY: flake8
flake8:
	@flake8 --ignore=E501 cloudview/*.py

.PHONY: pylint
pylint:
	@pylint --disable=line-too-long,R0801 cloudview/*.py

.PHONY: test
test:
	@pytest -v

clean:
	@rm -rf dist/ build/ *.egg-info
