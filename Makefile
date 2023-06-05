test:
	@pylint --disable=line-too-long,R0801 cloudview/*.py
	@flake8 --ignore=E501 cloudview/*.py
	@find -type f -name \*.sh -exec bash -n {} \;

pypi:
	@python3 -m build --sdist --wheel --outdir dist/

clean:
	@rm -rf dist/ build/ *.egg-info
