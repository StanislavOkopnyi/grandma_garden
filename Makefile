- install:
	uv pip install -r requirements.txt

- lock:
	uv pip compile pyproject.toml -o requirements.txt
