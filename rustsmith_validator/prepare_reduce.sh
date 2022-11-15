#!/bin/sh

# mkdir tmp + hash
# mkdir inside this folder for the two optimisations
# run rustc for 2 optimisations
# compare results. if not equal then output 0. if equal then output 1

# i.e. if file name is `bug.rs` then this should be `bug`
FILE_PREFIX="" 

HASH="lord_voldemort"

main() {
    # folder to reduce our file in
    ROOT="./$FILE_PREFIX-$HASH"
    [ ! -d $ROOT] && mkdir $ROOT
    FILE_PATH="$ROOT/bug.rs"
    cp "$FILE_PREFIX.rs" "$FILE_PATH"
}

main()