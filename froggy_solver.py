#!/usr/bin/env python3
"""
Froggy CrackMe solver - reconstructs validation and finds key.
Serial format: XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX (32 hex = 4 x 64-bit).
Name and serial are linked; symmetry: name vs reversed(name) hashes.
"""

M64 = (1 << 64) - 1

def u64(x):
    return x & M64

# FNV-1a style: prime 0x100000001B3, init 0x14650FB0739D0383
FNV_INIT = 0x14650FB0739D0383
FNV_PRIME = 0x100000001B3

def fnv_hash(data: bytes) -> int:
    h = FNV_INIT
    for b in data:
        h = u64(h ^ b) * FNV_PRIME
    return h

# In the binary: intermediate values use fmix_like (no final xor); only final check uses final_mix.
P_MIX = 0x9E3779B185EBCA87
Q_MIX = 0xC2B2AE3D27D4EB4F

def fmix_like(x: int) -> int:
    """State after two muls and xors, WITHOUT final xor (used for v52, v53, v57)."""
    x = u64(x)
    x = u64(x ^ (x >> 33))
    x = u64(x * P_MIX)
    x = u64(x ^ (x >> 29))
    x = u64(x * Q_MIX)
    return u64(x)

def final_mix(x: int) -> int:
    """What is compared to TARGET: fmix_like(x) ^ (fmix_like(x) >> 32)."""
    y = fmix_like(x)
    return u64(y ^ (y >> 32))

def mix(x: int) -> int:
    """Full mix including final xor (legacy; use fmix_like/final_mix to match binary)."""
    return final_mix(x)

def unmix(y: int) -> int:
    """Inverse of mix: recover state such that mix(state) == y."""
    y = u64(y)
    # Step 5
    hi, lo = (y >> 32) & 0xFFFFFFFF, y & 0xFFFFFFFF
    x = u64((hi << 32) | (lo ^ hi))
    # Step 4
    x = u64(x * pow(0xC2B2AE3D27D4EB4F, -1, 1 << 64))
    s3 = x
    # Step 3: s3 = s2 ^ (s2>>29). s2 must be = s1 * 0x9E3779B185EBCA87 (step2 output).
    # So s2 is a multiple of K = 0x9E3779B185EBCA87. Try s2 = k*K for small k.
    K = 0x9E3779B185EBCA87
    # s2 must be multiple of K (output of step2). 2^64/K ≈ 1.6 so try k=0,1,2
    for k in range(0, 4):
        s2_cand = u64(k * K)
        if u64(s2_cand ^ (s2_cand >> 29)) == s3:
            x = s2_cand
            break
    else:
        # Fallback: use recurrence (may give wrong preimage for step2_inv)
        s2 = 0
        for b in range(64):
            if b < 29:
                s2 |= ((s3 >> b) & 1) << b
            elif b >= 35:
                s2 |= ((s3 >> b) & 1) << b
            else:
                s2 |= ((((s3 >> b) ^ ((s2 >> (b - 29)) & 1)) & 1) << b)
            s2 = u64(s2)
        x = s2
    # Step 2
    x = u64(x * pow(K, -1, 1 << 64))
    # Step 1
    s0 = 0
    for b in range(31, 64):
        s0 |= ((x >> b) & 1) << b
    for b in range(30, -1, -1):
        s0 |= ((((x >> b) ^ ((s0 >> (b + 33)) & 1)) & 1) << b)
        s0 = u64(s0)
    return u64(s0)

def compute_final(v29: int, v47: int, v17: int, v18: int) -> int:
    """Matches binary: v52,v53,v57 = fmix_like; final check = final_mix(v58)."""
    v52 = fmix_like(v29)
    v53 = fmix_like(v47)
    v54 = u64(v52 ^ v17 ^ (v52 >> 32))
    v55 = u64(v53 ^ v18 ^ (v53 >> 32) ^ 0x1337F00DCAFEBABE)
    v56 = u64((v55 << 17) ^ (v55 >> 3) ^ v54 ^ 0x2EA07040ACDB444C)
    v57 = fmix_like(v56)
    v58 = u64((v57 ^ (v57 >> 32)) + ((v54 << 7) ^ 0x56E57F5F77891A00) + (v55 >> 5))
    return final_mix(v58)

TARGET = 0xB9229933597558C9

# Empty name path: v29 = 0xB7D49ACC3EB31A82, v47 = 0xD4B5EF4161BE37C6
V29_EMPTY = 0xB7D49ACC3EB31A82
V47_EMPTY = 0xD4B5EF4161BE37C6

def serial_to_v17_v18(serial_hex: str) -> tuple:
    """Serial 'XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX' -> (v17, v18)."""
    s = serial_hex.replace("-", "")
    assert len(s) == 32
    parts = [int(s[i:i+16], 16) for i in (0, 16)]
    # v17 = (parts[0] << 32) | parts[1], v18 = (parts[2] << 32) | parts[3]
    # Actually stored as 4 x 8 hex = 4 QWORDs: groups 1,2,3,4
    g1 = int(s[0:8], 16)
    g2 = int(s[8:16], 16)
    g3 = int(s[16:24], 16)
    g4 = int(s[24:32], 16)
    v17 = (g1 << 32) | g2
    v18 = (g3 << 32) | g4
    return (v17, v18)

def v17_v18_to_serial(v17: int, v18: int) -> str:
    g1 = (v17 >> 32) & 0xFFFFFFFF
    g2 = v17 & 0xFFFFFFFF
    g3 = (v18 >> 32) & 0xFFFFFFFF
    g4 = v18 & 0xFFFFFFFF
    return f"{g1:08X}-{g2:08X}-{g3:08X}-{g4:08X}"

def name_to_v29_v47(name: str) -> tuple:
    data = name.encode("utf-8")
    if len(data) == 0:
        return (V29_EMPTY, V47_EMPTY)
    h = fnv_hash(data)
    v29 = u64(h ^ 0xA3B1957C4D2E1901)
    rev = bytes(reversed(data))
    h_rev = fnv_hash(rev)
    v47 = u64(h_rev ^ 0xC0D0E0F112233445)
    return (v29, v47)

# Key for empty name (correct logic: fmix_like intermediates, final_mix for check)
KEY_EMPTY_NAME = "93D8A8AB-9ABCABD9-FFA34899-79D69257"

def find_key_for_name(name: str) -> str:
    """Use Z3 to find a valid serial (same logic as key.py: fmix_like for intermediates, final_mix for check)."""
    try:
        from z3 import BitVec, BitVecVal, Solver, sat, LShR
        def fmix_like_z3(x):
            t = x ^ LShR(x, 33)
            a = BitVecVal(P_MIX, 64) * t
            b = a ^ LShR(a, 29)
            return BitVecVal(Q_MIX, 64) * b
        def final_mix_z3(x):
            y = fmix_like_z3(x)
            return y ^ LShR(y, 32)
        v29, v47 = name_to_v29_v47(name)
        v17 = BitVec("v17", 64)
        v18 = BitVec("v18", 64)
        v52 = fmix_like_z3(BitVecVal(v29, 64))
        v53 = fmix_like_z3(BitVecVal(v47, 64))
        v54 = v52 ^ v17 ^ LShR(v52, 32)
        v55 = v53 ^ v18 ^ LShR(v53, 32) ^ BitVecVal(0x1337F00DCAFEBABE, 64)
        v56 = (v55 << 17) ^ LShR(v55, 3) ^ v54 ^ BitVecVal(0x2EA07040ACDB444C, 64)
        v57 = fmix_like_z3(v56)
        v58 = (v57 ^ LShR(v57, 32)) + ((v54 << 7) ^ BitVecVal(0x56E57F5F77891A00, 64)) + LShR(v55, 5)
        s = Solver()
        s.add(final_mix_z3(v58) == BitVecVal(TARGET, 64))
        if s.check() == sat:
            m = s.model()
            return v17_v18_to_serial(m[v17].as_long(), m[v18].as_long())
    except ImportError:
        pass
    return None

def main():
    print("=== Froggy CrackMe Key ===\n")
    print("For empty name (just press Enter at Name):")
    print("  Serial:", KEY_EMPTY_NAME)
    print("  Verify:", compute_final(V29_EMPTY, V47_EMPTY, *serial_to_v17_v18(KEY_EMPTY_NAME)) == TARGET)
    key_frog = find_key_for_name("Froggy")
    if key_frog:
        print("\nFor name 'Froggy':")
        print("  Serial:", key_frog)
    print()

    # Try empty name and see what (v17, v18) we need
    v29, v47 = V29_EMPTY, V47_EMPTY
    # We have: final = mix(v58(v54(v17), v55(v18))) == TARGET
    # So we need to find (v17, v18). One equation, two unknowns - pick v18=0 and solve for v17?
    # Actually we can't easily invert mix. Brute force small space or use Z3.

    # Try v17=0, v18=0 with empty name
    f = compute_final(v29, v47, 0, 0)
    print(f"Empty name, serial 0,0 -> final = {hex(f)} (target {hex(TARGET)})")

    # For palindrome name, v29 and v47 are related (same hash h, different xor)
    # name = "a" -> h = fnv(b'a'), v29 = h^0xA3..., v47 = h^0xC0...
    for trial_name in ["", "a", "aa", "aba", "frog", "Frog"]:
        v29, v47 = name_to_v29_v47(trial_name)
        f = compute_final(v29, v47, 0, 0)
        print(f"Name {repr(trial_name)}: v29={v29:016x} v47={v47:016x} final(0,0)={f:016x}")

    # Use z3 to find (v17, v18) for empty name
    try:
        from z3 import BitVec, URem, sat, Solver
        v17_bv = BitVec("v17", 64)
        v18_bv = BitVec("v18", 64)
        # We need to model mix and the chain - complex. Instead brute force v17 and solve v18?
        # Or: fix v18=0 and search v17 (2^64 too big). So we need algebraic approach or small search.
    except ImportError:
        pass

    # Elegant weakness: maybe when name is a palindrome, v29 and v47 have a relation that
    # forces a simple serial? Or maybe the "sigil" is derived from the name directly?
    print("\n--- Checking if serial can be derived from name ---")
    for name in ["Froggy", "froggy", "swamp", "Libertas"]:
        v29, v47 = name_to_v29_v47(name)
        f = compute_final(v29, v47, v29, v47)
        print(f"Name {repr(name)}: serial=v29,v47 -> final={hex(f)}")
        if f == TARGET:
            ser = v17_v18_to_serial(v29, v47)
            print(f"  KEY FOUND: {ser}")

    # Solve for serial: we need mix(v58)=TARGET => v58 = unmix(TARGET)
    print("\n--- Solving for serial (empty name) ---")
    target_v58 = unmix(TARGET)
    print(f"unmix(TARGET) = v58 = {hex(target_v58)}")
    # Verify unmix
    target_v58 = unmix(TARGET)
    if mix(target_v58) != TARGET:
        # Try alternative: v58 might be found by brute over low 32 bits
        for low in range(1 << 20):
            if mix(low) == TARGET:
                target_v58 = low
                break
        else:
            target_v58 = unmix(TARGET)  # use anyway for equation
    v29, v47 = V29_EMPTY, V47_EMPTY
    v52, v53 = mix(v29), mix(v47)
    # Fix v18 so that v55 = 0: v55 = v53^v18^(v53>>32)^0x1337... = 0 => v18 = v53^(v53>>32)^0x1337F00DCAFEBABE
    v18_zero = u64(v53 ^ (v53 >> 32) ^ 0x1337F00DCAFEBABE)
    v55 = 0
    # Now we need v54 such that: (v57^(v57>>32)) + ((v54<<7)^0x56E57F5F77891A00) + 0 = target_v58
    # v56 = (v55<<17)^(v55>>3)^v54^0x2EA07040ACDB444C = v54^0x2EA07040ACDB444C
    # v57 = mix(v56). So we need to find v54 by search (v54 is 64-bit; try iterative or Z3).
    const56 = u64(0x2EA07040ACDB444C)
    add_const = u64((v55 << 7) ^ 0x56E57F5F77891A00)  # 0 when v55=0: 0^0x56E57F5F77891A00
    add_const = u64(0x56E57F5F77891A00)
    # v58 = (v57 ^ (v57>>32)) + ((v54<<7)^0x56E57F5F77891A00) + (v55>>5)
    # So (v57^(v57>>32)) = target_v58 - ((v54<<7)^0x56E57F5F77891A00) - 0.
    # For each v54 we get v56 = v54^const56, v57 = mix(v56), LHS = v57^(v57>>32).
    # We need LHS + ((v54<<7)^0x56E57F5F77891A00) = target_v58.
    # Try v54 = 0: v56 = const56, v57 = mix(const56), LHS = v57^(v57>>32), RHS = target_v58 - add_const.
    def compute_v58_from_v54(v54: int) -> int:
        v56 = u64(v54 ^ const56)
        v57 = mix(v56)
        return u64((v57 ^ (v57 >> 32)) + u64((v54 << 7) ^ 0x56E57F5F77891A00) + (v55 >> 5))

    # Brute force v54 in a small range? Or try v54 = v52 ^ (v52>>32) (i.e. v17=0) and see
    v54_try = u64(v52 ^ (v52 >> 32))
    v58_try = compute_v58_from_v54(v54_try)
    print(f"v54=v52^(v52>>32) (v17=0): v58={hex(v58_try)} (target {hex(target_v58)})")

    # Use Z3 to find v54
    try:
        from z3 import BitVec, Solver, sat, unsat
        v54_bv = BitVec("v54", 64)
        # We need to model: v56 = v54 ^ const56, then mix(v56), then v58 = ...
        # Z3 can't easily model mix (multiplication + xor). So try numerical search.
        # Instead: fix v54 and search. Or use the fact that we have one equation in v54.
        # Simple approach: random search or iterate v54 from 0 to 2^24 and see if any hit.
        pass
    except ImportError:
        pass

    # Numerical search: try v54 in [0, 2^20) and see if any v58 matches (unlikely to hit exact)
    # Better: we have v58 = target_v58. So (v57^(v57>>32)) = target_v58 - ((v54<<7)^0x56E57F5F77891A00).
    # So we need to find v54 such that mix(v54^const56)^(mix(...)>>32) = target_v58 - ((v54<<7)^0x56...).
    # Brute force over v54: 2^64 is too big. Try structured: v54 = 0, 1, v52, v52^(v52>>32), etc.
    for v54_cand in [0, 1, v52, u64(v52 ^ (v52 >> 32)), 0x1337, 0xCAFEBABE]:
        v58_cand = compute_v58_from_v54(v54_cand)
        if v58_cand == target_v58:
            v17_cand = u64(v54_cand ^ v52 ^ (v52 >> 32))
            serial = v17_v18_to_serial(v17_cand, v18_zero)
            print(f"FOUND: v54={hex(v54_cand)} v17={hex(v17_cand)} v18={hex(v18_zero)}")
            print(f"Serial (empty name): {serial}")
            break
    else:
        # Try solving: fix v55=0, so v18 = v18_zero. Then we need v54. Do a sparse search.
        found = False
        for seed in range(0, 100000):
            v54_cand = u64(seed * 0x9E3779B1 + 0x6C078965)
            v58_cand = compute_v58_from_v54(v54_cand)
            if v58_cand == target_v58:
                v17_cand = u64(v54_cand ^ v52 ^ (v52 >> 32))
                serial = v17_v18_to_serial(v17_cand, v18_zero)
                print(f"FOUND (seed {seed}): serial = {serial}")
                found = True
                break
        if not found:
            print("No solution in sparse search; need full solver or different name.")

    # Fixed-point iteration: v58 = target_v58 => (v54<<7)^0x56... = target_v58 - (v57^(v57>>32))
    # So v54 = ((target_v58 - (v57^(v57>>32)))^0x56...) >> 7  (v57 = mix(v54^const56))
    # Iterate: v54_{n+1} = ((target_v58 - R(v54_n)) ^ 0x56...) >> 7
    print("\n--- Fixed-point iteration for v54 ---")
    v54_fp = 0
    for _ in range(100):
        v56 = u64(v54_fp ^ const56)
        v57 = mix(v56)
        R = u64(v57 ^ (v57 >> 32))
        rhs = u64(target_v58 - R) ^ 0x56E57F5F77891A00
        if rhs & 0x7F != (0x56E57F5F77891A00 & 0x7F):
            v54_next = rhs >> 7  # try anyway
        else:
            v54_next = rhs >> 7
        v54_next = u64(v54_next)
        if v54_next == v54_fp:
            v58_check = compute_v58_from_v54(v54_fp)
            if v58_check == target_v58:
                v17_sol = u64(v54_fp ^ v52 ^ (v52 >> 32))
                serial_sol = v17_v18_to_serial(v17_sol, v18_zero)
                print(f"Fixed-point converged: v54={hex(v54_fp)} -> Serial (empty name): {serial_sol}")
                assert compute_final(V29_EMPTY, V47_EMPTY, v17_sol, v18_zero) == TARGET
                break
        v54_fp = v54_next
    else:
        # Try varying low 7 bits of v54 (since (v54<<7) loses them)
        for low7 in range(0, 128):
            v54_cand = u64((v54_fp << 7) | low7)
            if compute_v58_from_v54(v54_cand) == target_v58:
                v17_sol = u64(v54_cand ^ v52 ^ (v52 >> 32))
                serial_sol = v17_v18_to_serial(v17_sol, v18_zero)
                print(f"Found with low7={low7}: Serial (empty name): {serial_sol}")
                break
        else:
            print("Fixed-point did not converge to solution.")

if __name__ == "__main__":
    main()
