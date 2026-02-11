#!/usr/bin/env python3
"""
Froggy CrackMe - keygen cu Z3.
Generăm un serial valid pentru un nume dat, refăcând exact formula din binar.
"""
from z3 import *

# =============================================================================
# PASUL 0: Constante extrase din binar (decompile)
# =============================================================================
# Valoarea cu care se compară rezultatul final; trebuie să o atingem.
TARGET = 0xB9229933597558C9

# Parametri FNV-1a (hash pentru nume și nume inversat)
FNV_INIT  = 0x14650FB0739D0383
FNV_PRIME = 0x100000001B3

# Constante XOR folosite în formulă (din binar)
XOR_REV   = 0xC0D0E0F112233445   # aplicat pe hash-ul numelui inversat -> v47
XOR_V29   = 0xA3B1957C4D2E1901   # aplicat pe hash-ul numelui -> v29
XOR_V55   = 0x1337F00DCAFEBABE   # în calculul v55
XOR_V56   = 0x2EA07040ACDB444C   # în calculul v56
XOR_V54S  = 0x56E57F5F77891A00   # în termenul (v54<<7)^...

# Constante pentru „fmix” (tip splitmix64, folosit în binar)
P = 0x9E3779B185EBCA87
Q = 0xC2B2AE3D27D4EB4F

MASK64 = (1 << 64) - 1   # toate calculele sunt pe 64 de biți


# =============================================================================
# PASUL 1: Hash FNV-1a pe 64 de biți
# =============================================================================
def fnv1a64(data: bytes) -> int:
    """
    Hash FNV-1a: pentru fiecare octet, xor cu h apoi h = h * FNV_PRIME (mod 2^64).
    În binar: numele și numele inversat sunt hash-uite separat.
    """
    h = FNV_INIT
    for b in data:
        h ^= b
        h = (h * FNV_PRIME) & MASK64
    return h


def bv64(x: int) -> BitVecRef:
    """Transformă un întreg Python într-o constantă Z3 pe 64 de biți."""
    return BitVecVal(x & MASK64, 64)


# =============================================================================
# PASUL 2: Funcția „fmix” din binar (fără ultimul xor cu >>32)
# =============================================================================
def fmix_like(x: BitVecRef) -> BitVecRef:
    """
    Reproduce exact pașii din binar:
      t = x ^ (x >> 33)
      a = P * t
      b = a ^ (a >> 29)
      return Q * b
    Folosit pentru v52, v53, v57. NU include ultimul xor (acela e doar la comparația finală).
    """
    t = x ^ LShR(x, 33)
    a = bv64(P) * t
    b = a ^ LShR(a, 29)
    return bv64(Q) * b


def final_mix(x: BitVecRef) -> BitVecRef:
    """
    Ce este comparat cu TARGET: fmix_like(x) apoi rezultat ^ (rezultat >> 32).
    """
    y = fmix_like(x)
    return y ^ LShR(y, 32)


# =============================================================================
# PASUL 3: Reconstruim formula din binar și rezolvăm cu Z3
# =============================================================================
def solve_for_name(name: bytes, per_seed_timeout_ms: int = 15000):
    """
    Pentru un nume dat:
      1) Calculăm v29 și v47 din nume (hash + xor).
      2) v52, v53 sunt fmix_like(v29), fmix_like(v47).
      3) Serialul = 4 grupuri de 8 hex = 4 numere de 32 biți -> p0, p1, p2, p3.
      4) Din ele formăm v17 = (p0<<32)|p1 și v18 = (p2<<32)|p3.
      5) Aplicăm restul formulei din binar până la final_mix(v58).
      6) Cerem Z3 să găsească p0,p1,p2,p3 astfel încât final_mix(v58) == TARGET.
    """

    # --- 3.1 Din nume obținem valorile fixe v29 și v47 ---
    h_fwd = fnv1a64(name)           # hash pe nume (ex: "Froggy")
    h_rev = fnv1a64(name[::-1])      # hash pe nume inversat ("yggorF")

    v29 = (h_fwd ^ XOR_V29) & MASK64
    v47 = (h_rev ^ XOR_REV) & MASK64

    # --- 3.2 v52 și v53 sunt „fmix” aplicat pe v29 și v47 (constante Z3) ---
    v52 = fmix_like(bv64(v29))
    v53 = fmix_like(bv64(v47))

    # --- 3.3 Necunoscutele: cele 4 părți ale serialului (32 biți fiecare) ---
    # Serial: XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX  =>  p0, p1, p2, p3
    p0, p1, p2, p3 = BitVecs("p0 p1 p2 p3", 32)

    # În binar: v17 = primele două grupuri (p0 partea high, p1 partea low), idem v18
    v17 = (ZeroExt(32, p0) << 32) | ZeroExt(32, p1)
    v18 = (ZeroExt(32, p2) << 32) | ZeroExt(32, p3)

    # --- 3.4 Restul formulei (copiat din decompile) ---
    v54 = v52 ^ v17 ^ LShR(v52, 32)
    v55 = v53 ^ v18 ^ LShR(v53, 32) ^ bv64(XOR_V55)
    v56 = (v55 << 17) ^ LShR(v55, 3) ^ v54 ^ bv64(XOR_V56)
    v57 = fmix_like(v56)
    v58 = (v57 ^ LShR(v57, 32)) + ((v54 << 7) ^ bv64(XOR_V54S)) + LShR(v55, 5)

    # --- 3.5 Condiția de validare: rezultatul final trebuie să fie TARGET ---
    constraint = (final_mix(v58) == bv64(TARGET))

    # --- 3.6 Z3 găsește o soluție; căutarea e euristică, deci încercăm mai multe seeds ---
    seeds = [
        1,2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,
        53,59,61,67,71,73,79,83,89,97,101,103,107,109,113,
        127,131,137,139,149,151,157,163,167,173,179,181,191,193,197,199
    ]

    for seed in seeds:
        s = SolverFor("QF_BV")   # solver pentru formule pe bit-vectori
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
# PASUL 4: Program principal
# =============================================================================
def main():
    name_str = input("Name / Handle: ")
    name = name_str.encode("utf-8")

    # Prima încercare: timeout 15 secunde
    seed, serial = solve_for_name(name, per_seed_timeout_ms=15000)
    if serial:
        print(f"Serial: {serial}")
        return

    # Dacă nu găsește: retry cu timeout mai mare (60 secunde)
    print("[!] First pass did not find a solution. Trying longer timeouts...")
    seed, serial = solve_for_name(name, per_seed_timeout_ms=60000)
    if serial:
        print(f"Serial: {serial}")
        return

    print("[!] No solution found in the tested seeds/timeouts.")
    print("    Try a different Name/Handle, or increase timeouts / add more seeds.")


if __name__ == "__main__":
    main()
