#!/bin/bash

MEMORY_LIMIT=4194304 # 4GB in KB
TIME_LIMIT=30 # seconds

echo "Compiling main.cpp..."
g++ -o main.o main.cpp

if [ $? -ne 0 ]; then
    echo "Compilation failed!"
    exit 1
fi

TMP_TIME=$(mktemp)

for n in {1..3}; do
    for boat in {2..6}; do
        result=$(/usr/bin/time -v timeout ${TIME_LIMIT}s bash -c "ulimit -v ${MEMORY_LIMIT}; ./main.o $n $boat" 2>${TMP_TIME})
        exit_code=$?

        if [ $exit_code -eq 124 ]; then
            echo "n=$n boat=$boat | TIMEOUT (exceeded ${TIME_LIMIT}s)"
        elif [ $exit_code -eq 134 ] || echo "$result" | grep -q "Killed"; then
            echo "n=$n boat=$boat | OUT OF MEMORY (exceeded ${MEMORY_LIMIT}KB)"
        elif [ $exit_code -eq 0 ]; then
            echo "n=$n boat=$boat | $result"
        else
            echo "n=$n boat=$boat | ERROR (exit code: $exit_code) $result"
        fi

        cat ${TMP_TIME}
        echo ""
    done
done

rm ${TMP_TIME}
