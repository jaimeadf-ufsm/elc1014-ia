#!/bin/bash

MEMORY_LIMIT=4194304 # 4GB in KB
TIME_LIMIT=30 # seconds

EXPERIMENTS_DIR="experiments"

echo "Compiling main.cpp..."
g++ -o main.o main.cpp

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

for n in {1..6}; do
    for boat in {2..6}; do
        EXPERIMENT_NAME="n${n}_boat${boat}"
        EXPERIMENT_DIR="${EXPERIMENTS_DIR}/${EXPERIMENT_NAME}"

        mkdir -p ${EXPERIMENT_DIR}

        /usr/bin/time -v timeout ${TIME_LIMIT}s bash -c "ulimit -v ${MEMORY_LIMIT}; ./main.o $n $boat" > ${EXPERIMENT_DIR}/output.txt 2> ${EXPERIMENT_DIR}/time.txt

        exit_code=$?

        echo $exit_code > ${EXPERIMENT_DIR}/exit_code.txt

        if [ $exit_code -eq 0 ]; then
            echo "n=$n boat=$boat | SUCCESS"
        else
            echo "n=$n boat=$boat | ERROR (exit code: $exit_code)"
        fi
    done
done

