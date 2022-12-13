#!/bin/bash

# run rustc for different:
#   - mutation levels
# and compare results. if not equal then output 0. if equal then output 1

################################ ARGUMENTS ################################

# time limit in seconds
TIME_LIMIT={time_limit}

# cli args
PROGRAM_ARGS="{arguments}"

# mutation number
MUTATION="{mutation}"

# should result in different code being generated
OPT="{opt}"

# name of bug file, e.g. bug.rs
FILE="{file}"

###########################################################################

run_with_timeout() {{
    # arg1: command to run with timeout
    timeout $TIME_LIMIT $1
    local EXIT_CODE=$?
    if [ $EXIT_CODE -eq 124 ]; then
        echo "timed out"
    else 
        echo "exited with code $EXIT_CODE"
    fi
    return 0
}}

main() {{
    # compile with the two optimisation flags
    BIN_ORIGINAL="out_${{OPT}}_original"
    BIN_MUTATION="out_${{OPT}}_mutated_${{MUTATION}}"

    echo "Compiling the two files... $BIN_ORIGINAL and $BIN_MUTATION"
    RUSTC_ORIGINAL="RUSTC_MUTATION_NUMBER=0 $COMPILER_PATH"
    RUSTC_MUTATION="RUSTC_MUTATION_NUMBER=$MUTATION $COMPILER_PATH"
    $RUSTC_ORIGINAL -C opt-level=$OPT $FILE -o $BIN_ORIGINAL
    $RUSTC_MUTATION -C opt-level=$OPT $FILE -o $BIN_MUTATION

    # run the two files and determine if they are equal
    OUT1=$( run_with_timeout "./$BIN_ORIGINAL $PROGRAM_ARGS" )
    echo "output for $BIN_ORIGINAL is: $OUT1"
    OUT2=$( run_with_timeout "./$BIN_MUTATION $PROGRAM_ARGS" )
    echo "output for $BIN_MUTATION is: $OUT2"

    if [ "$OUT1" != "$OUT2" ]; then
        echo "Bug still exists"
        exit 0 # bug exists still
    else 
        echo "Bug disappeared, oh no!"
        exit 1 # bug no longer exists
    fi
}}

main