install:
	python3 -m pip install -e .

test:
	python3 -m unittest discover -s tests -p "test_*.py"

coverage:
	pytest --cov=document_converter --cov-report=term-missing --cov-report=html

lint:
	python3 -m compileall document_converter tests

audit:
	pip-audit --strict --desc
	pip-licenses --fail-on="AGPL;GPLv3"

specs:
	@echo "Validating OpenSpec changes and specs..."
	openspec validate --all

help:
	document-converter --help
