#!/usr/bin/env bash

export PYTHONPATH="./src"
ANSWER_DIR="./check_answer"
NODES="rt1 rt2 rt3 rt4"
RT_ANS_SUFFIX="_route_answer.json"
OSPFNEIGH_ANS_SUFFIX="_ospfneigh_answer.json"

mkdir -p "$ANSWER_DIR"

for node in $NODES
do
  echo "# Node: $node" 1>&2
  config_file="${ANSWER_DIR}/${node}_config.json"
  sed -e "s/#{node_name}/$node/g" config.json.template > "$config_file"
  # routing table check
  python main.py -t route -c "$config_file" | jq . > "${ANSWER_DIR}/${node}${RT_ANS_SUFFIX}"
  # ospf neighbor table check
  python main.py -t ospfneigh -c "$config_file" | jq . > "${ANSWER_DIR}/${node}${OSPFNEIGH_ANS_SUFFIX}"
done

# check answer stats (route)
for answer_file in "$ANSWER_DIR"/*"$RT_ANS_SUFFIX"
do
  found_count=$(jq ".found | length" < "$answer_file")
  only_bf_count=$(jq ".only_bf_rt | length" < "$answer_file")
  only_crpd_count=$(jq ".only_crpd_rt | length" < "$answer_file")
  node_name=${answer_file##.*/}
  node_name=${node_name%$RT_ANS_SUFFIX}
  echo "Node: $node_name, Found: $found_count, Only_cRPD: $only_crpd_count, Only_BF: $only_bf_count"
done

# check answer stats (ospfneigh)
for answer_file in "$ANSWER_DIR"/*"$OSPFNEIGH_ANS_SUFFIX"
do
  found_count=$(jq ".found | length" < "$answer_file")
  only_bf_count=$(jq ".only_bf_ospfneigh | length" < "$answer_file")
  only_crpd_count=$(jq ".only_crpd_ospfneigh | length" < "$answer_file")
  node_name=${answer_file##.*/}
  node_name=${node_name%$OSPFNEIGH_ANS_SUFFIX}
  echo "Node: $node_name, Found: $found_count, Only_cRPD: $only_crpd_count, Only_BF: $only_bf_count"
done
