[![License](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)
[![Release CI](https://github.com/rustsmith/rustsmith-validator/actions/workflows/release.yml/badge.svg)](https://github.com/rustsmith/rustsmith-validator/actions/workflows/release.yml)
![Version](https://img.shields.io/github/v/release/rustsmith/rustsmith-validator?label=version)

## RustSmith Validator

RustSmith validator is a small tool to accompany the main [rustsmith](https://github.com/rustsmith/rustsmith) project so that files
generated can be efficiently tested across optimisation levels in parallel.

Run by `rsmith-validator`

## Contributing

Contributions are all welcome! If you would like to contribute, please see the
corresponding [guidelines][contributing]. By contributing, you are agreeing to
our [code of conduct][code-of-conduct].

[contributing]: https://github.com/rustsmith/rustsmith-validator/blob/master/CONTRIBUTING.md

[code-of-conduct]: https://github.com/rustsmith/rustsmith-validator/blob/master/CODE_OF_CONDUCT.md


## Bugs
- Bug 1: seems like all optimisation levels trigger the bug. Even 0 (no opt)
- Bug 2: bug confirmed and can be reduced 3500 -> 65 lines by `CReduce`.
- Bug 3: not reproducible with script just yet (can't compile between different versions)