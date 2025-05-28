pip-compile --output-file=requirements.txt pyproject.toml
pip-compile --extra=speedups --output-file=requirements_full.txt pyproject.toml
