import os
import json

UNCOMPILED = "uncompiled"
COMPILE_TIMEOUT = "compile timeout"
COMPILER_CRASHED = "compiler crashed"
RUNTIME_TIMEOUT = "runtime timeout"
RUNTIME_CRASHED = "runtime crashed"

with open("config.json", "r") as f:
    MAIL_CONFIG = json.load(f)

CSMITH_HOME = os.environ["CSMITH_HOME"]

SIMPLE_OPTS = (
    "-O0", "-O1", "-O2", "-O3", "-Os", "-Ofast", "-Og"
)

COMPLEX_OPTS_GCC = tuple(
"""
-fauto-inc-dec
-fbranch-count-reg
-fcombine-stack-adjustments
-fcompare-elim
-fcprop-registers
-fdce
-fdefer-pop
-fdelayed-branch
-fdse
-fforward-propagate
-fguess-branch-probability
-fif-conversion
-fif-conversion2
-finline-functions-called-once
-fipa-modref
-fipa-profile
-fipa-pure-const
-fipa-reference
-fipa-reference-addressable
-fmerge-constants
-fmove-loop-invariants
-fmove-loop-stores
-fomit-frame-pointer
-freorder-blocks
-fshrink-wrap
-fshrink-wrap-separate
-fsplit-wide-types
-fssa-backprop
-fssa-phiopt
-ftree-bit-ccp
-ftree-ccp
-ftree-ch
-ftree-coalesce-vars
-ftree-copy-prop
-ftree-dce
-ftree-dominator-opts
-ftree-dse
-ftree-forwprop
-ftree-fre
-ftree-phiprop
-ftree-pta
-ftree-scev-cprop
-ftree-sink
-ftree-slsr
-ftree-sra
-ftree-ter
-funit-at-a-time
-falign-functions  -falign-jumps
-falign-labels  -falign-loops
-fcaller-saves
-fcode-hoisting
-fcrossjumping
-fcse-follow-jumps  -fcse-skip-blocks
-fdelete-null-pointer-checks
-fdevirtualize  -fdevirtualize-speculatively
-fexpensive-optimizations
-fgcse  -fgcse-lm
-fhoist-adjacent-loads
-finline-functions
-finline-small-functions
-findirect-inlining
-fipa-bit-cp  -fipa-cp  -fipa-icf
-fipa-ra  -fipa-sra  -fipa-vrp
-fisolate-erroneous-paths-dereference
-flra-remat
-foptimize-sibling-calls
-foptimize-strlen
-fpartial-inlining
-fpeephole2
-freorder-blocks-algorithm=stc
-freorder-blocks-and-partition  -freorder-functions
-frerun-cse-after-loop
-fschedule-insns  -fschedule-insns2
-fsched-interblock  -fsched-spec
-fstore-merging
-fstrict-aliasing
-fthread-jumps
-ftree-builtin-call-dce
-ftree-loop-vectorize
-ftree-pre
-ftree-slp-vectorize
-ftree-switch-conversion  -ftree-tail-merge
-ftree-vrp
-fvect-cost-model=very-cheap
-fgcse-after-reload
-fipa-cp-clone
-floop-interchange
-floop-unroll-and-jam
-fpeel-loops
-fpredictive-commoning
-fsplit-loops
-fsplit-paths
-ftree-loop-distribution
-ftree-partial-pre
-funswitch-loops
-fvect-cost-model=dynamic
-fversion-loops-for-strides
""".strip().split("\n")
)

AGGRESIVE_OPTS = tuple(
"""
-ffinite-loops
""".strip().split('\n')
)

PREFIX_TEXT = "/\* --- FORWARD DECLARATIONS --- \*/"
SUFFIX_TEXT = "/\* --- FUNCTIONS --- \*/"
OPT_FORMAT = '__attribute__((optimize("{}")))'


SCRIPT = """#!/bin/bash
cd {} 
echo $PWD > pwd
python3 {}/reduce.py {} >> error 
exit_code=$?
echo $exit_code > exit_code

exit $exit_code
"""


FENCE = '#define FENCE __asm__ __volatile__("" ::: "memory")\n'