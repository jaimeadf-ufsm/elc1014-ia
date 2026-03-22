#!/bin/bash

MEMORY_LIMIT=$((4 * 1024 * 1024 * 1024)) # 4GB in bytes

DEDUPLICATE="$1"
EXPERIMENTS_DIR="experiments"

echo "Compiling main.cpp..."
g++ -O3 -march=native -flto -o main.o main.cpp

mkdir -p ${EXPERIMENTS_DIR}

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

for k in {2..128}; do
    n=1
    threshold=256
    
    while [ $n -le 2000000000 ]; do
        experiment_file="${EXPERIMENTS_DIR}/n${n}_k${k}_d${DEDUPLICATE}.txt"

        ./main.o $n $k $DEDUPLICATE $MEMORY_LIMIT > ${experiment_file}
        exit_code=$?

        if [ $exit_code -eq 0 ]; then
            solution=$(grep "solution:" ${experiment_file})
            echo "n: $n, k: $k, d: $DEDUPLICATE | SUCCESS ($solution)"

            if [[ $solution == *"memory limit"* ]]; then
                break
            fi
        else
            echo "n: $n, k: $k, d: $DEDUPLICATE | ERROR (exit code: $exit_code)"
        fi

        if [ $n -lt $threshold ]; then
            n=$((n + 1))
        else
            n=$((n * 2))
        fi
    done
done

