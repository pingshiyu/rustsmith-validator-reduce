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
PROGRAM_ARGS="13261570157581078759114001864422411866 0.38331497 34974307 3684050912 zpFPadjtM2A7foYZDCmivvy 37537 7644 6938339077394126244 4494344778086113386 0.6038438928398585 true 157206999992205892160125692815689010061 127 25 15886894502111892626"

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
MUTATION2="43"

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