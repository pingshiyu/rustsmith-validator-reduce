#!/bin/bash

# run rustc for different:
#   - optimisation levels
#   - compiler versions
#   - mutation levels
# and compare results.

################################ ARGUMENTS ################################

# time limit in seconds
TIME_LIMIT=0.1

# cli args
PROGRAM_ARGS="66352453952895258124660834408826127178 59 false 0.9509875137936153 -409616457684654530 0.88254267 1058911319 SqHBjUwDHeZ1Ccxy1iSRY3yRvAOnv1mHxgCkRz6r 15269 52315538 15130577115341375330 6432014971220020165 158316308367995743307947188949847064189 20481 1"

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
MUTATION2="48"

# are these valid bugs? 0 => valid, not 0 => invalid
# return value of panic kills 
PANIC_KILL_RETURN=2
# return value if binary times out 
BINARY_TIMEOUT_RETURN=0
# return value of binary errors (compiled binary, but binary errors)
BINARY_ERR_RETURN=0

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
    return $EXIT_CODE
}

main() {
    # compile with the two optimisation flags
    BIN1="out_${RUSTC_V1}_O${OPT1}_MUT${MUTATION1}"
    BIN2="out_${RUSTC_V2}_O${OPT2}_MUT${MUTATION2}"

    echo "Compiling the two files... $BIN1 and $BIN2"
    RUSTUP_TOOLCHAIN=$RUSTC_V1 RUSTC_MUTATION_NUMBER=$MUTATION1 $RUSTC -C opt-level=$OPT1 test-case.rs -o $BIN1
    RUSTUP_TOOLCHAIN=$RUSTC_V2 RUSTC_MUTATION_NUMBER=$MUTATION2 $RUSTC -C opt-level=$OPT2 test-case.rs -o $BIN2

    # check successful compilation: exit code 2 if compilation unsuccessful
    [ ! -f $BIN1 ]
    BIN1_EXISTS=$?
    [ ! -f $BIN2 ]
    BIN2_EXISTS=$?
    if [ "$BIN1_EXISTS" -ne "$BIN2_EXISTS" ]; then
        echo "compilation failed for one of the files"
        exit $PANIC_KILL_RETURN
    fi

    # run the two files 
    OUT1=$( run_with_timeout "./$BIN1 $PROGRAM_ARGS" )
    EXIT_CODE1=$?
    echo "output for $BIN1 is: $OUT1"

    OUT2=$( run_with_timeout "./$BIN2 $PROGRAM_ARGS" )
    EXIT_CODE2=$?
    echo "output for $BIN2 is: $OUT2"

    # compare the exit codes, indicating if the binary managed to run
    if [ "$EXIT_CODE1" != "$EXIT_CODE2" ]; then
        # check if exit was due to a timeout
        if [ "$EXIT_CODE2" == 124 ]; then
            echo "Second binary timed out (infinite loop?)"
            exit $BINARY_TIMEOUT_RETURN
        fi
        echo "One of the binary errored"
        exit $BINARY_ERR_RETURN
    fi

    # determine if the binary produced same results
    if [ "$OUT1" != "$OUT2" ]; then
        echo "Bug still exists"
        exit 0 # bug exists still
    else 
        echo "Bug disappeared, oh no!"
        exit 1 # bug no longer exists
    fi
}

main