#!/bin/bash

MEMORY_LIMIT=4194304 # 4GB in KB

DEDUPLICATE="$1"
EXPERIMENTS_DIR="experiments"

echo "Compiling main.cpp..."
g++ -o main.o main.cpp

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

for boat in {2..100}; do
    n=1
    increment=1
    threshold=10
    
    while [ $n -le 2000000000 ]; do
        EXPERIMENT_NAME="n${n}_boat${boat}_d${DEDUPLICATE}"
        EXPERIMENT_DIR="${EXPERIMENTS_DIR}/${EXPERIMENT_NAME}"

        mkdir -p ${EXPERIMENT_DIR}

        /usr/bin/time -v bash -c "ulimit -v ${MEMORY_LIMIT}; ./main.o $n $boat $DEDUPLICATE" > ${EXPERIMENT_DIR}/output.txt 2> ${EXPERIMENT_DIR}/time.txt

        exit_code=$?

        echo $exit_code > ${EXPERIMENT_DIR}/exit_code.txt

        if [ $exit_code -eq 0 ]; then
            echo "n=$n boat=$boat d=$DEDUPLICATE | SUCCESS"
        else
            echo "n=$n boat=$boat d=$DEDUPLICATE | ERROR (exit code: $exit_code)"
            break
        fi

        n=$((n + increment))

        if [ $n -ge $threshold ]; then
            increment=$((increment * 10))
            threshold=$((threshold * 10))
        fi
    done
done

