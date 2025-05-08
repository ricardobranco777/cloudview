FILES=*/*.py
BIN=cloudview

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
	@pylint --disable=duplicate-code $(FILES)

.PHONY: test
test:
	TZ=Europe/Berlin pytest --capture=sys -v --cov --cov-report term-missing

.PHONY: mypy
mypy:
	@mypy --disable-error-code=attr-defined --exclude tests/ --ignore-missing-imports $(FILES)

.PHONY: shellcheck
shellcheck:
	@shellcheck scripts/$(BIN)

.PHONY: install
install:
	@install -m 0755 scripts/$(BIN) $(HOME)/bin/

.PHONY: uninstall
uninstall:
	@cd $(HOME)/bin ; rm -f $(BIN)
