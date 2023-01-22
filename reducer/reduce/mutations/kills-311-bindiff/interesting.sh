#!/bin/bash

# run rustc for different:
#   - optimisation levels
#   - compiler versions
#   - mutation levels
# and compare results.

################################ ARGUMENTS ################################

# time limit for compiling / running binary
TIME_LIMIT_COMPILE=30.0
TIME_LIMIT_BIN=1.0

# cli args
PROGRAM_ARGS="1506257858 58053955060907978228413323271309395765 1982260988248642477 41296 8310774606426645764 0.43024325 false 1133 s 1593717469 0.5784685659415231 51515699338345771867337661935203564098 187 15981183682437742247 119"

# rust compiler verions
RUSTC_V1=""
RUSTC_V2=""

# these two options should result in different code being generated
FLAGS1="-Zmir-opt-level=4"
FLAGS2="-Zmir-opt-level=4"

# custom rustc binary
RUSTC="/home/jacob/projects/rustsmith/rust-mutcov/build/x86_64-unknown-linux-gnu/stage1/bin/rustc"

# mutations (only works with binary that accepts mutations)
MUTATION1="0"
MUTATION2="311"

# are these valid bugs? 0 => valid, not 0 => invalid
# return value if undetected
UNDETECTED_RETURN=1
# return value of panic kills 
COMPILE_PANIC_RETURN=2
# return value of panic kills 
COMPILE_TIMEOUT_RETURN=3
# return value of binary difference
BINARY_DIFFERENCE_RETURN=0
# return value if running binary times out 
OUTPUT_TIMEOUT_RETURN=5
# return value if running binary errors
OUTPUT_ERR_RETURN=0
# reutrn value if running binary gives different outputs
OUTPUT_DIFFERENCE_RETURN=0

###########################################################################

run_with_timeout() {
    # arg1: time limit
    # arg1: command to run with timeout
    timeout $1 $2
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
    run_with_timeout $TIME_LIMIT_COMPILE "env RUSTUP_TOOLCHAIN=$RUSTC_V1 RUSTC_MUTATION_NUMBER=$MUTATION1 $RUSTC $FLAGS1 test-case.rs -o $BIN1"
    COMPILE_CODE1=$?
    run_with_timeout $TIME_LIMIT_COMPILE "env RUSTUP_TOOLCHAIN=$RUSTC_V2 RUSTC_MUTATION_NUMBER=$MUTATION2 $RUSTC $FLAGS2 test-case.rs -o $BIN2"
    COMPILE_CODE2=$?
    
    # exit code different => panic / timeout kill
    if [ "$COMPILE_CODE1" -ne "$COMPILE_CODE2" ]; then
        echo "compilation failed for at least one of the files"
        if [ $COMPILE_CODE2 -eq 124 ]; then 
            # mutant timed out
            exit $COMPILE_TIMEOUT_RETURN
        else
            exit $COMPILE_PANIC_RETURN
        fi
    fi

    # here: exit code is the same. thus both produced a file or both didn't.
    # both didn't produce file => no difference possible
    if [ ! -f $BIN1 ] || [ ! -f $BIN2 ]; then
        echo "both exited with the same error. mutant not killed."
        exit $UNDETECTED_RETURN
    fi

    # check binary equal or not. If equal then we can stop here
    if cmp --silent -- "$BIN1" "$BIN2"; then
        echo "binaries identical. mutant not killed."
        exit $UNDETECTED_RETURN
    fi

    # now we know mutant is killed with strength at minimum $BINARY_DIFFERENCE
    # run the two files 
    OUT1=$( run_with_timeout $TIME_LIMIT_BIN "./$BIN1 $PROGRAM_ARGS" )
    OUT1_EXIT_CODE=$?
    echo "output for $BIN1 is: $OUT1"

    OUT2=$( run_with_timeout $TIME_LIMIT_BIN "./$BIN2 $PROGRAM_ARGS" )
    OUT2_EXIT_CODE=$?
    echo "output for $BIN2 is: $OUT2"

    # compare the exit codes, indicating if the binary managed to run
    if [ "$OUT1_EXIT_CODE" != "$OUT2_EXIT_CODE" ]; then
        # check if exit was due to a timeout
        if [ "$OUT2_EXIT_CODE" == 124 ] || [ "$OUT1_EXIT_CODE" == 124 ] ; then
            echo "One of the binary timed out (infinite loop?)"
            exit $OUTPUT_TIMEOUT_RETURN
        fi
        echo "One of the binary errored"
        exit $OUTPUT_ERR_RETURN
    fi

    # determine if the binary produced same results
    if [ "$OUT1" != "$OUT2" ]; then
        echo "Output different, mutant killed."
        exit $OUTPUT_DIFFERENCE_RETURN 
    else 
        echo "Same output produced but binaries different, mutant weakly killed."
        exit $BINARY_DIFFERENCE_RETURN
    fi
}

main