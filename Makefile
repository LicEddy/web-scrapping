install:
	pip install --upgrade pip \
		&& pip install -r requirements.txt
titles:
	python main.py

freeze:
	pip freeze > requirements.txt

test:
	python titles.py