# state_cross_checker

## Setup

```shell
pip install -r requirements.txt
export PYTHONPATH=./src
```

## Run
### Edit config file

[config.json](./config.json)

### Collect state data from batfish
Run Batfish anyway.

Exec below script to collect node state data from batfish.

```shell
python get_sim_env_table.py
```

### Cross-check state data

```shell
python main.py
```

## Development

Format

```shell
black **/*.py
```

Lint

```shell
flake8 --config .config/flake8 **/*.py
pylint --rcfile .config/pylintrc **/*.py
```
