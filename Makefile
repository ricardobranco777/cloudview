test:
	@find -type f -name \*.sh -exec bash -n {} \;
	@docker-compose config -q
	@flake8
	@pylint --disable=invalid-name,raise-missing-from,R0801 $$(find * -name \*.py)
	#@pylint --disable=invalid-name,C0111,R0801 $$(find * -name \*.py)

upload-pypi:
	@python3 setup.py sdist bdist_wheel
	@python3 -m twine upload dist/*

clean:
	@rm -rf dist/ build/ *.egg-info
