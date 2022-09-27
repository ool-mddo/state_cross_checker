#!/usr/bin/env bash

export PYTHONPATH="./src"
ANSWER_DIR="./check_answer"
NODES="rt1 rt2 rt3 rt4"

function answer_file_suffix() {
  table=$1
  echo "_${table}_answer.json"
}

function answer_file() {
  node=$1
  table=$2
  suffix=$(answer_file_suffix "$table")
  echo "${ANSWER_DIR}/${node}${suffix}"
}

mkdir -p "$ANSWER_DIR"

for table in route ospfneigh
do
  echo "* Check table: $table"

  # generate check result
  echo "  * Generate cross-check result"
  for node in $NODES
  do
    answer_file=$(answer_file "$node" "$table")
    echo "    * Node: $node, Result: $answer_file"

    # config file
    config_file="${ANSWER_DIR}/${node}_config.json"
    sed -e "s/#{node_name}/$node/g" config.json.template > "$config_file"

    # state table check
    python main.py -t "$table" -c "$config_file" | jq . > "$answer_file"
  done

  # check stats of the result
  echo "  * Check stats"
  for node in $NODES
  do
    answer_file=$(answer_file "$node" "$table")
    both_count=$(jq ".both | length" "$answer_file")
    only_crpd_count=$(jq ".only_crpd | length" "$answer_file")
    only_bf_count=$(jq ".only_bf | length" "$answer_file")
    echo "    * Node: $node, both: $both_count, only_crpd: $only_crpd_count, only_bf: $only_bf_count"
  done
done
