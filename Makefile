install:
	pip install --upgrade pip \
		&& pip install -r requirements.txt
titles:
	python main.py

freeze:
	pip freeze > requirements.txt

test:
	python titles.py

BRANCH = main
COMMIT_MESSAGE = "Some changes"

push:
	git add .
	git commit -m "$(COMMIT_MESSAGE)"
	git push -u origin $(BRANCH)