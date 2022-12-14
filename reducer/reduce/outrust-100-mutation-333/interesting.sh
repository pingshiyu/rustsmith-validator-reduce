#!/bin/bash

# run rustc for different:
#   - optimisation levels
#   - compiler versions
#   - mutation levels
# and compare results. if not equal then output 0. if equal then output 1

################################ ARGUMENTS ################################

# time limit in seconds
TIME_LIMIT=0.1

# cli args
PROGRAM_ARGS="false 4209980218407563548 1142099019 190 15840669008024663812 28335 0.25136049501893565 23253800213989771479694642028891444436 gZZvy18jpLEcshrYWuHPoglqvnjyZxRV8h6ZPFRfxYRIs6vKaMsqxKJTXVm340hubBlyo 16 0.6478225 41651 133953822569802778374065482358682831051 456613277 13725244528585302958"

# rust compiler verions
RUSTC_V1=""
RUSTC_V2=""

# these two options should result in different code being generated
OPT1="0"
OPT2="0"

# custom rustc binary
RUSTC="/home/jacob/projects/rustsmith/rust-mutcov/rust-build/bin/rustc"

# mutations (only works with binary that accepts mutations)
MUTATION1="0"
MUTATION2="333"

###########################################################################

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
    BIN1="out_${RUSTC_V1}_O${OPT1}_MUT${MUTATION1}"
    BIN2="out_${RUSTC_V2}_O${OPT2}_MUT${MUTATION2}"

    echo "Compiling the two files... $BIN1 and $BIN2"
    RUSTUP_TOOLCHAIN=$RUSTC_V1 RUSTC_MUTATION_NUMBER=$MUTATION1 $RUSTC -C opt-level=$OPT1 test-case.rs -o $BIN1
    RUSTUP_TOOLCHAIN=$RUSTC_V2 RUSTC_MUTATION_NUMBER=$MUTATION2 $RUSTC -C opt-level=$OPT2 test-case.rs -o $BIN2

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