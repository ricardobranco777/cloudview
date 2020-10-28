test:
	@pylint --disable=invalid-name,raise-missing-from,line-too-long,R0801 $$(find * -name \*.py)
	@flake8 --ignore=E501 setup.py cloudview/
	@find -type f -name \*.sh -exec bash -n {} \;

upload-pypi:
	@python3 setup.py sdist bdist_wheel
	@python3 -m twine upload dist/*

clean:
	@rm -rf dist/ build/ *.egg-info
