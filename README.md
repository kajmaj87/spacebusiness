[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)
[![code linting: flake8](https://img.shields.io/badge/lint-flake8-blue.svg)](http://flake8.pycqa.org/)
[![code quality: pytest](https://img.shields.io/badge/test-pytest-yellow.svg)](https://docs.pytest.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
# spacebusiness
A space simulation showing how cruel the capitalism is.

# Installation
First create a python virtual environment:
```bash
$ python -m venv .env
```

Activate and install dependencies
```bash
$ source .env/bin/activate
$ pip install -r requirements.txt

```
Run the project with
```bash
$ ./main.py
```

Normally the game runs in ticks every second. You can change this to manual (press enter) if you uncomment the input() line in main.py.

Game will create ticker.log where you can see how the prices of different goods changed over time.
Currently the ticker shows entries like this:
| Resource type | Avg. price | Total moneyflow | # of transactions |
| ------| ---- | ---- | --- |
| WATER | 0.52 | 0.84 | 3   |

It's a good idea to tail this log during the simulation is running, you can use other tools to graph it etc.
