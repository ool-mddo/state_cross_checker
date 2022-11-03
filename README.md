# state_cross_checker

## Setup

```shell
pip install -r requirements.txt
export PYTHONPATH=./src
```

## Definition

Environment:

* original
* emulated : cLab (container-lab) based environment
* batfish : Batfish-simulated environment

Each environment have networks.
A network have snapshots.
There are several types of snapshot.

original-namespace snapshots (comparable by row/col):

|       | original      | batfish (use orig config) |
|-------|---------------|---------------------------|
| as-is | original_asis | original_asis             |
| to-be | original_tobe | original_asis             |

emulated-namespace snapshots (comparable by row/col):

|       | emulated      | batfish (use emul-config) |
|-------|---------------|---------------------------|
| as-is | emulated_asis | emulated_asis             |
| to-be | emulated_tobe | emulated_tobe             |

Directory structure:

```text
configs/
  + <network>/
    + <snapshot>/
      + configs/    ... config files of network devices (batfish input)
      + batfish/    ... config files for batfish (batfish input)
      + states/     ... state files (for original/emulated)
        + <node>/
          + something-state-data.json

batfish_states/     ... state files (batfish output)
  + <network>/
    + <snapshot>/
      + <node>/
        + something-state-data.json
```

## Run

### Edit config file

[template of config](./config.tmpl.yaml)


The config file have definition of directory path and its snapshot-level rules as jinja2 template,
but doesn't have node-level directory rule. It is implicit rule.

### Environment variable

```shell
export PYTHONPATH=./src
```

### Collect state data from batfish

Run Batfish anyway.

Exec below script to collect node state data from batfish.
The script pushes a snapshot specified in config.yaml
and queries several questions to get simulated state data.

* `-c`/`--config` : (optional) configuration file
* `-n`/`--network` : network name
* `-s`/`--snapshot` : snapshot name

```shell
python bf_state.py -n mddo-ospf -s emulated_asis
```

### Cross-check state data

Specify check targets using options:

* `-d`/`--node`: Target node (device)
* `-n`/`--network`: Target network
* `-t`/`--table`: State table to check `[route,ospf_neighbor]`
* Source snapshot
  * `-se`/`--src-env`: Source environment
  * `-ss`/`--src-ss`: Source snapshot
* Destination snapshot
  * `-de`/`--dst-env`: Destination environment
  * `-ds`/`--dst-ss`: Destination snapshot

other options:

* `-c`/`--config` : (optional) configuration file
* `--debug`: (optional) debug print

```shell
python diff_state.py -t route -d rt1 -n mddo-ospf \
  -se batfish -ss emulated_asis -de emulated -ds emulated_asis
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
