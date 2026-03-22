#!/bin/bash

MEMORY_LIMIT=1073741824 # 1GB in bytes

DEDUPLICATE="$1"
EXPERIMENTS_DIR="experiments"

echo "Compiling main.cpp..."
# g++ -O3 -march=native -flto -o main.o main.cpp

mkdir -p ${EXPERIMENTS_DIR}

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

for boat in {2..128}; do
    n=1
    threshold=256
    
    while [ $n -le 2000000000 ]; do
        EXPERIMENT_FILE="${EXPERIMENTS_DIR}/n${n}_boat${boat}_d${DEDUPLICATE}.txt"

        ./main.o $n $boat $DEDUPLICATE $MEMORY_LIMIT > ${EXPERIMENT_FILE}
        exit_code=$?

        if [ $exit_code -eq 0 ]; then
            solution=$(grep "solution:" ${EXPERIMENT_FILE})
            echo "n=$n boat=$boat d=$DEDUPLICATE | SUCCESS ($solution)"

            if [[ $solution == *"memory limit"* ]]; then
                break
            fi
        else
            echo "n=$n boat=$boat d=$DEDUPLICATE | ERROR (exit code: $exit_code)"
        fi

        if [ $n -lt $threshold ]; then
            n=$((n + 1))
        else
            n=$((n * 2))
        fi
    done
done

