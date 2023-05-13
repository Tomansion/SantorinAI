# SantorinAI tests

## How to run tests

### Install dependencies

```bash
pip install coverage
```

### Run tests

From the root of the project, run:

```bash
python -m coverage run -m unittest 
```

### Generate coverage report

```bash
python -m coverage report
python -m coverage html
firefox htmlcov/index.html
```


### One liner

```bash
python -m coverage run -m unittest && python -m coverage report && python -m coverage html && firefox htmlcov/index.html
```