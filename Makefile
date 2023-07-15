.PHONY: all
all: flake8 pylint

.PHONY: flake8
flake8:
	@flake8 --ignore=E501 cloudview/*.py

.PHONY: pylint
pylint:
	@pylint --disable=line-too-long,R0801 cloudview/*.py

clean:
	@rm -rf dist/ build/ *.egg-info
