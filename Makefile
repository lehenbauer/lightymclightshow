


all:
	@echo "woof"

freeze:
	pip freeze > requirements.txt

lightenv:
	python3 -m venv lightenv
	lightenv/bin/pip install wheel
	lightenv/bin/pip install -r requirements.txt
