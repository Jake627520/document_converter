install:
	python3 -m pip install -e .

test:
	python3 -m unittest discover -s tests -p "test_*.py"

lint:
	python3 -m compileall document_converter tests

audit:
	pip-audit --strict --desc
	pip-licenses --fail-on="AGPL;GPLv3"

help:
	document-converter --help
