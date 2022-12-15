#!/bin/bash

# run rustc for 2 optimisation levels
# compare results. if not equal then output 0. if equal then output 1

# time limit in seconds
TIME_LIMIT=0.50

# cli args
PROGRAM_ARGS="12345 42 25 6 678910 0.21013731 3 7 166 99999 true 0.21013731 -5004714827797697950 9000484929595902425 39665680081982938260247928363693310660 37614 110540297241443669109602386009209940202 0.32055454424241825 sMRpYgzRzcVWSWqEWwqDjSGRZvD2BSSbcT8THvN1IE11N 8128116862839983746 116 180719041 62 30 -1453915729"

# rust compiler verions
RUSTC1="1.61.0"
RUSTC2="1.45.0"

# these two options should result in different code being generated
OPT1="2"
OPT2="2"

run_with_timeout() {
    # arg1: command to run with timeout
    timeout $TIME_LIMIT $1
    local EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "timed out"
    else 
        echo "exited with code $EXIT_CODE"
    fi
    return 0
}

main() {
    # compile with the two optimisation flags
    BIN1="out_${RUSTC1}_O${OPT1}"
    BIN2="out_${RUSTC2}_O${OPT2}"

    echo "Compiling the two files... $BIN1 and $BIN2"
    RUSTUP_TOOLCHAIN=$RUSTC1 rustc -C opt-level=$OPT1 bug.rs -o $BIN1
    RUSTUP_TOOLCHAIN=$RUSTC2 rustc -C opt-level=$OPT2 bug.rs -o $BIN2

    # run the two files and determine if they are equal
    OUT1=$( run_with_timeout "./$BIN1 $PROGRAM_ARGS" )
    echo "output for $BIN1 is: $OUT1"
    OUT2=$( run_with_timeout "./$BIN2 $PROGRAM_ARGS" )
    echo "output for $BIN2 is: $OUT2"

    if [ "$OUT1" != "$OUT2" ]; then
        echo "Bug still exists"
        exit 0 # bug exists still
    else 
        echo "Bug disappeared, oh no!"
        exit 1 # bug no longer exists
    fi
}

main