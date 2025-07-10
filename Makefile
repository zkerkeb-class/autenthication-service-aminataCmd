.PHONY: run build clean test install format lint

run:
	uvicorn main:app --reload --port 8000

install:
	pip3 freeze > requirements.txt

build:
	docker build . -t volley_api:0.1 

clean:
	rm -rf __pycache__

test:
	pytest tests/ -v 

format:
	black ./app/ ./tests/
	isort ./app/ ./tests/

lint:
	flake8 ./app/ ./tests/
	black --check app/ tests/
	isort --check-only app/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
