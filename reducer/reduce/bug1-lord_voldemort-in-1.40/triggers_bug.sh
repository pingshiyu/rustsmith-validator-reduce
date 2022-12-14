#!/bin/bash

# run rustc for different:
#   - optimisation levels
#   - compiler versions
# compare results. if not equal then output 0. if equal then output 1

################################ ARGUMENTS ################################

# time limit in seconds
TIME_LIMIT=0.10

# cli args
PROGRAM_ARGS=""

# rust compiler verions
RUSTC1="1.45.0"
RUSTC2="1.45.0"

# these two options should result in different code being generated
OPT1="0"
OPT2="2"

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