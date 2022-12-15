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
PROGRAM_ARGS="17067127360882943664 d9U5ncX30dQMpn5HHZgmiJGwUJdzTVFwmd2GoW3PFItxW0rHZG9ZKdnusGHi2JMBdXYtIcg0x2n 22005 -891334657 29 true 156 17463 0.7748567219176261 0.0052264333 3846700709 -8381978202322681228 127141204043323331605169645782652571474 13222500411778182476107027075302741592 12121152616079819554"

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
MUTATION2="229"

# return value of panic kills (are these valid bugs? 0 => valid, not 0 => invalid)
PANIC_KILL_RETURN=1

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

    # check successful compilation: exit code 2 if compilation unsuccessful
    [ ! -f $BIN1 ]
    BIN1_EXISTS=$?
    [ ! -f $BIN2 ]
    BIN2_EXISTS=$?
    if [ "$BIN1_EXISTS" -ne "$BIN2_EXISTS" ]; then
        echo "compilation failed for 1 file"
        exit $PANIC_KILL_RETURN
    fi

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