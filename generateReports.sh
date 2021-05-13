#!/bin/bash
names=$(awk -F "=" '/names/ {print $2}' config.ini)

rm logfile.log

echo "Generating reports ..."

# python3 updateProtocols.py

echo "Running dev.py ..."
for name in $names; do
    python3 dev.py $name
done

echo "Running contr.py ..."
for name in $names; do
    python3 contr.py protocols/$name.toml 1
done

echo "Running visualizer ..."
python3 vis.py