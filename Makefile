FILES=*/*.py

.PHONY: all
all: flake8 pylint test mypy black

.PHONY: black
black:
	@black --check .

.PHONY: flake8
flake8:
	@flake8 --ignore=E501,W503 $(FILES)

.PHONY: pylint
pylint:
	@pylint --disable=line-too-long,duplicate-code,too-few-public-methods $(FILES)

.PHONY: test
test:
	@pytest --capture=sys -v --cov --cov-report term-missing

.PHONY: mypy
mypy:
	@mypy --disable-error-code=attr-defined --exclude tests/ --ignore-missing-imports $(FILES)
