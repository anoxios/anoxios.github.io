#!/usr/bin/env python3
"""
Froggy CrackMe - Z3 keygen.
Generates a valid serial for a given name by reconstructing the exact formula from the binary.
"""
from z3 import *

# =============================================================================
# STEP 0: Constants extracted from the binary (decompiled)
# =============================================================================
# The value the final result is compared against; we need to reach it.
TARGET = 0xB9229933597558C9

# FNV-1a parameters (hash for name and reversed name)
FNV_INIT  = 0x14650FB0739D0383
FNV_PRIME = 0x100000001B3

# XOR constants used in the formula (from the binary)
XOR_REV   = 0xC0D0E0F112233445   # applied to reversed-name hash -> v47
XOR_V29   = 0xA3B1957C4D2E1901   # applied to name hash -> v29
XOR_V55   = 0x1337F00DCAFEBABE   # in v55 computation
XOR_V56   = 0x2EA07040ACDB444C   # in v56 computation
XOR_V54S  = 0x56E57F5F77891A00   # in the (v54<<7)^... term

# Constants for "fmix" (splitmix64-style, used in the binary)
P = 0x9E3779B185EBCA87
Q = 0xC2B2AE3D27D4EB4F

MASK64 = (1 << 64) - 1   # all computations are 64-bit


# =============================================================================
# STEP 1: 64-bit FNV-1a hash
# =============================================================================
def fnv1a64(data: bytes) -> int:
    """
    FNV-1a hash: for each byte, xor with h then h = h * FNV_PRIME (mod 2^64).
    In the binary: name and reversed name are hashed separately.
    """
    h = FNV_INIT
    for b in data:
        h ^= b
        h = (h * FNV_PRIME) & MASK64
    return h


def bv64(x: int) -> BitVecRef:
    """Turn a Python int into a 64-bit Z3 constant."""
    return BitVecVal(x & MASK64, 64)


# =============================================================================
# STEP 2: "fmix" function from the binary (without the final xor with >>32)
# =============================================================================
def fmix_like(x: BitVecRef) -> BitVecRef:
    """
    Reproduce the exact steps from the binary:
      t = x ^ (x >> 33)
      a = P * t
      b = a ^ (a >> 29)
      return Q * b
    Used for v52, v53, v57. Does NOT include the final xor (that is only at the final comparison).
    """
    t = x ^ LShR(x, 33)
    a = bv64(P) * t
    b = a ^ LShR(a, 29)
    return bv64(Q) * b


def final_mix(x: BitVecRef) -> BitVecRef:
    """
    What is compared to TARGET: fmix_like(x) then result ^ (result >> 32).
    """
    y = fmix_like(x)
    return y ^ LShR(y, 32)


# =============================================================================
# STEP 3: Reconstruct the formula from the binary and solve with Z3
# =============================================================================
def solve_for_name(name: bytes, per_seed_timeout_ms: int = 15000):
    """
    For a given name:
      1) Compute v29 and v47 from the name (hash + xor).
      2) v52, v53 are fmix_like(v29), fmix_like(v47).
      3) Serial = 4 groups of 8 hex = 4 numbers of 32 bits -> p0, p1, p2, p3.
      4) From them we form v17 = (p0<<32)|p1 and v18 = (p2<<32)|p3.
      5) Apply the rest of the formula from the binary up to final_mix(v58).
      6) Ask Z3 to find p0,p1,p2,p3 such that final_mix(v58) == TARGET.
    """

    # --- 3.1 From the name we get the fixed values v29 and v47 ---
    h_fwd = fnv1a64(name)           # hash of name (e.g. "Froggy")
    h_rev = fnv1a64(name[::-1])     # hash of reversed name ("yggorF")

    v29 = (h_fwd ^ XOR_V29) & MASK64
    v47 = (h_rev ^ XOR_REV) & MASK64

    # --- 3.2 v52 and v53 are "fmix" applied to v29 and v47 (Z3 constants) ---
    v52 = fmix_like(bv64(v29))
    v53 = fmix_like(bv64(v47))

    # --- 3.3 Unknowns: the 4 parts of the serial (32 bits each) ---
    # Serial: XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX  =>  p0, p1, p2, p3
    p0, p1, p2, p3 = BitVecs("p0 p1 p2 p3", 32)

    # In the binary: v17 = first two groups (p0 high part, p1 low part), same for v18
    v17 = (ZeroExt(32, p0) << 32) | ZeroExt(32, p1)
    v18 = (ZeroExt(32, p2) << 32) | ZeroExt(32, p3)

    # --- 3.4 Rest of the formula (copied from decompiled code) ---
    v54 = v52 ^ v17 ^ LShR(v52, 32)
    v55 = v53 ^ v18 ^ LShR(v53, 32) ^ bv64(XOR_V55)
    v56 = (v55 << 17) ^ LShR(v55, 3) ^ v54 ^ bv64(XOR_V56)
    v57 = fmix_like(v56)
    v58 = (v57 ^ LShR(v57, 32)) + ((v54 << 7) ^ bv64(XOR_V54S)) + LShR(v55, 5)

    # --- 3.5 Validation condition: final result must equal TARGET ---
    constraint = (final_mix(v58) == bv64(TARGET))

    # --- 3.6 Z3 finds a solution; search is heuristic, so we try multiple seeds ---
    seeds = [
        1,2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,
        53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,
        127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199
    ]

    for seed in seeds:
        s = SolverFor("QF_BV")   # solver for bit-vector formulas
        s.set("timeout", per_seed_timeout_ms)
        s.set("random_seed", seed)

        s.add(constraint)

        r = s.check()
        if r == sat:
            m = s.model()
            a0 = m[p0].as_long()
            a1 = m[p1].as_long()
            a2 = m[p2].as_long()
            a3 = m[p3].as_long()
            serial = f"{a0:08X}-{a1:08X}-{a2:08X}-{a3:08X}"
            return (seed, serial)

    return (None, None)


# =============================================================================
# STEP 4: Main program
# =============================================================================
def main():
    name_str = input("Name / Handle: ")
    name = name_str.encode("utf-8")

    # First attempt: 15 second timeout
    seed, serial = solve_for_name(name, per_seed_timeout_ms=15000)
    if serial:
        print(f"Serial: {serial}")
        return

    # If not found: retry with longer timeout (60 seconds)
    print("[!] First pass did not find a solution. Trying longer timeouts...")
    seed, serial = solve_for_name(name, per_seed_timeout_ms=60000)
    if serial:
        print(f"Serial: {serial}")
        return

    print("[!] No solution found in the tested seeds/timeouts.")
    print("    Try a different Name/Handle, or increase timeouts / add more seeds.")


if __name__ == "__main__":
    main()
