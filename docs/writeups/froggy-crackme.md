# Froggy CrackMe – Solution

**Category:** Reverse / CrackMe  
**Tools:** IDA Pro, Python, Z3

## Summary

- **Serial format:** `XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX` (32 hex digits, 3 dashes).
- **Validation:** Name and serial are combined via FNV-1a hashing and a splitmix64-style mix; a single final comparison decides success.
- **Elegant weakness:** One conditional jump controls the outcome. Patching that jump makes the program accept any valid-format input.

- **Challenge archive:** [Download froggy_crackme.zip](froggy_crackme.zip)
- **Solver script:** [froggy_solver.py](froggy_solver.py) (view or download the keygen source)

---

## 1. Validation flow (from reversing)

1. **Anti-debug:** Reads `/proc/self/status`, checks `TracerPid:`. If non-zero → "Debugger detected. The swamp rejects you."
2. **Input:** Prompts for **Name** and **Serial** (format above).
3. **Serial parsing:** 4 groups of 8 hex digits → two 64-bit values:
   - `v17 = (group1 << 32) | group2`
   - `v18 = (group3 << 32) | group4`
4. **Name hashes (FNV-1a, prime 0x100000001B3):**
   - Name → hash → `v29 = hash ^ 0xA3B1957C4D2E1901`
   - Reversed name → hash → `v47 = hash ^ 0xC0D0E0F112233445`
   - Empty name: `v29 = 0xB7D49ACC3EB31A82`, `v47 = 0xD4B5EF4161BE37C6`
5. **Final check:** A chain of splitmix64-style mix and XOR/add uses `v29`, `v47`, `v17`, `v18` and compares the result to **`0xB9229933597558C9`**.
   - In the binary: **`cmp rcx, rax`** at **0x2731** (rax = 0xB9229933597558C9), then a **conditional jump** (failure path).

---

## 2. Single path / elegant weakness

Success is decided by **one** comparison and **one** conditional jump:

- **0x2731:** `cmp rcx, rax` (computed value vs 0xB9229933597558C9)
- **0x2734:** conditional jump (e.g. `jnz` to "Wrong incantation" at 0x27ac)

If the jump is **never taken**, execution always reaches **"The Swamp Gate opens."**

### Patch (elegant crack)

- **File:** `froggy_crackme` (or your copy).
- **Location:** the **2-byte** instruction immediately after `cmp rcx, rax` (the conditional jump at **0x2734**).
- **Original:** conditional jump (e.g. `75 xx` = `jnz`).
- **Patch:** replace those 2 bytes with **`90 90`** (two NOPs).

Then:

- Run without a debugger (or with TracerPid cleared).
- Enter any non-empty name and any serial in the correct format, e.g.  
  **Name:** `Froggy`  
  **Serial:** `00000000-00000000-00000000-00000000`

The program will always open the gate.

---

## 3. Finding a valid key (no patch) – Z3 keygen

To get a **real** name+serial pair that passes the check without patching we model the check in Z3 and solve for the four 32-bit serial parts.

The solver **`froggy_solver.py`** does the following:

1. **From the name:** Compute FNV-1a hashes for name and reversed name, then apply the known XORs to get `v29` and `v47`.
2. **fmix-like:** Reconstruct the binary’s mix (without the final `^ (x >> 32)` where applicable) for intermediate values; the final comparison uses `final_mix(x) = fmix_like(x) ^ (fmix_like(x) >> 32)` compared to `TARGET`.
3. **Serial as unknowns:** The serial is 4 groups of 8 hex digits → four 32-bit values `p0, p1, p2, p3` with:
   - `v17 = (p0 << 32) | p1`
   - `v18 = (p2 << 32) | p3`
4. **Formula:** Build the rest of the binary’s formula (v54, v55, v56, v57, v58) from the decompiled logic and add the constraint `final_mix(v58) == TARGET`.
5. **Z3:** Use bit-vector solver (`QF_BV`) with multiple random seeds and timeouts to find a satisfying assignment for `p0..p3`, then format the serial as `XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX`.

### Usage

Download the solver: [froggy_solver.py](froggy_solver.py), then:

```bash
python3 froggy_solver.py
```

Enter a name when prompted (e.g. `Froggy`). The script prints a valid serial. It tries a 15s timeout first, then 60s if needed.

**Dependencies:** `z3-solver` (`pip install z3-solver`).

### Relevant code (excerpt)

Constants are taken from the binary (TARGET, FNV init/prime, XOR constants, fmix P/Q). The core is:

- `fnv1a64(data)` – FNV-1a 64-bit hash.
- `fmix_like(x)` – mix used for v52, v53, v57 (no final xor with >>32).
- `final_mix(x)` – value compared to TARGET: `fmix_like(x) ^ (fmix_like(x) >> 32)`.
- `solve_for_name(name, per_seed_timeout_ms)` – builds the Z3 model and returns a serial string or `(None, None)`.

---

## 4. Quick reference

| Item            | Value / Location                          |
|-----------------|-------------------------------------------|
| Target constant | `0xB9229933597558C9`                      |
| Comparison      | `cmp rcx, rax` at **0x2731**              |
| Patch           | Replace conditional jump at **0x2734** with `90 90` |
| Success message | "The Swamp Gate opens." / "Froggy approves." |
