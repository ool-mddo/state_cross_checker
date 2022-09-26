#!/usr/bin/env bash

ANSWER_DIR="./check_answer"
NODES="rt1 rt2 rt3 rt4"

mkdir -p "$ANSWER_DIR"

for node in $NODES
do
  echo "# Node: $node" 1>&2
  config_file="${ANSWER_DIR}/${node}_config.json"
  sed -e "s/#{node_name}/$node/g" config.json.template > "$config_file"
  python main.py -c "$config_file" | jq . > "${ANSWER_DIR}/${node}_answer.json"
done

# check answer stats
for answer_file in "$ANSWER_DIR"/*_answer.json
do
  found_count=$(jq ".found | length" < "$answer_file")
  only_bf_rt_count=$(jq ".only_bf_rt | length" < "$answer_file")
  only_crpd_rt_count=$(jq ".only_crpd_rt | length" < "$answer_file")
  node_name=${answer_file##.*/}
  node_name=${node_name%_answer.json}
  echo "Node: $node_name, Found: $found_count, Only_cRPD: $only_crpd_rt_count, Only_BF: $only_bf_rt_count"
done
