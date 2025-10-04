Dev setup
=========

This project is a small monorepo with a Python backend and a TypeScript frontend. To make the tests reproducible and make it easy to run the full test suite locally, install the dev/test dependencies listed below.

Python (recommended using venv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements-dev.txt
# Optionally install backend runtime dependencies
pip install -e backend
```

Node / Frontend

```bash
cd frontend
npm install
npm run build # or npm run dev for dev server
```

Running tests

```bash
# From project root with venv activated
python3 -m unittest discover -v
# or run pytest if preferred
pytest -q
```

Notes

- The backend package has its dependencies (see `backend/pyproject.toml`). Installing the editable backend package (`pip install -e backend`) will install those runtime requirements into your venv.
- If you are on macOS with M1/arm chips, ensure native dependencies are available (e.g., through Homebrew) before installing some packages.
