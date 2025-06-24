install:
	pip install --upgrade pip \
		&& pip install -r requirements.txt
scrape:
	python scrapper.py

analyze:
	python analysis.py

freeze:
	pip freeze > requirements.txt

test:
	python titles.py

BRANCH = main
COMMIT_MESSAGE = "Some changes"

push:
	git add .
	git commit -m "$(message)"
	git push -u origin $(BRANCH)

run: scrape analyze
