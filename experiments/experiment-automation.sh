#!/usr/bin/env bash

set -e  # Exit if any command fails

############################################
# 1) Find highest numeric suffix in folders
############################################

largest=0
shopt -s extglob  # Enable extended pattern matching

for d in *; do
  # Only check directories
  if [[ -d "$d" ]]; then
    # If directory name ends with a number, capture it
    if [[ "$d" =~ ([0-9]+)$ ]]; then
      num="${BASH_REMATCH[1]}"
      if (( num > largest )); then
        largest="$num"
      fi
    fi
  fi
done

# The new run index is largest+1
nextNumber=$((largest + 1))

echo "Highest folder suffix found: $largest"
echo "Using next folder suffix:   $nextNumber"
echo

############################################
# 2) Execute Workflows
############################################

# -- With Service Clause workflow --

echo "==> Starting With Service Clause workflow..."
jbr init sparql-custom "default-service-${nextNumber}"
mkdir "default-service-${nextNumber}/input/queries"
python3 query_sort.py sib-swiss-federated-queries.json "default-service-${nextNumber}/" service

cd "default-service-${nextNumber}"
jbr set-hook hookSparqlEndpoint sparql-endpoint-comunica
cd ..

python3 config_permutations.py "default-service-${nextNumber}/"

cd "default-service-${nextNumber}"

npm run jbr -- prepare
nohup npm run jbr -- run > "default-service-${nextNumber}.log" 2>&1 &
cd ..

echo "Workflow complete for: default-service-${nextNumber}"
echo

# -- No-Service Clause workflow --

echo "==> Starting No-Service Clause experiments..."
jbr init -c sparql-custom "no-service-${nextNumber}"
mkdir "no-service-${nextNumber}/input/queries"
python3 query_sort.py sib-swiss-federated-queries.json "no-service-${nextNumber}/" noservice

cp -r ../config "no-service-${nextNumber}/input/config"

cd "no-service-${nextNumber}"
jbr set-hook hookSparqlEndpoint sparql-endpoint-comunica
cd ..

mkdir "no-service-${nextNumber}/input/client-config"
python3 config_permutations.py "no-service-${nextNumber}/input/config/"

cd "no-service-${nextNumber}"
jbr generate-combinations

npm run jbr -- prepare
nohup npm run jbr -- run > "no-service-${nextNumber}.log" 2>&1 &
cd ..

echo "Workflow complete for: no-service-${nextNumber}"