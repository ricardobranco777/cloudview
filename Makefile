test:
	@pylint --disable=line-too-long,R0801 cloudview/*.py
	@flake8 --ignore=E501 cloudview/*.py
	@find -type f -name \*.sh -exec bash -n {} \;

upload-pypi:
	@python3 setup.py sdist bdist_wheel
	@python3 -m twine upload dist/*

clean:
	@rm -rf dist/ build/ *.egg-info
