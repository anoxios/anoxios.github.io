# Froggy CrackMe – Solution

## Summary

- **Serial format:** `XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX` (32 hex digits, 3 dashes).
- **Validation:** Name and serial are mixed (FNV hash + splitmix64-style) and must satisfy one final comparison.
- **Elegant weakness:** A single conditional jump controls success. Patching that jump makes the program always accept.

---

## 1. Validation flow (from reversing)

1. **Anti-debug:** Reads `/proc/self/status`, looks for `TracerPid:`. If non-zero → "Debugger detected. The swamp rejects you."
2. **Input:** Prompts for **Name** and **Serial** (format above).
3. **Serial parsing:** 4 groups of 8 hex digits → two 64-bit values:
   - `v17 = (group1 << 32) | group2`
   - `v18 = (group3 << 32) | group4`
4. **Name hashes (FNV-1a, prime 0x100000001B3):**
   - Name → hash → `v29 = hash ^ 0xA3B1957C4D2E1901`
   - Reversed name → hash → `v47 = hash ^ 0xC0D0E0F112233445`
   - Empty name: `v29 = 0xB7D49ACC3EB31A82`, `v47 = 0xD4B5EF4161BE37C6`
5. **Final check:** A chain of mix (splitmix64-style) and XOR/add uses `v29`, `v47`, `v17`, `v18` and compares the result to **`0xB9229933597558C9`**.  
   - In the binary: **`cmp rcx, rax`** at **0x2731** (rax = 0xB9229933597558C9), then a **conditional jump** (failure path).

---

## 2. The “single path” / elegant weakness

The success path is decided by **one** comparison and **one** conditional jump:

- **0x2731:** `cmp rcx, rax` (computed value vs 0xB9229933597558C9)
- **0x2734:** conditional jump (e.g. `jnz` to “Wrong incantation” at 0x27ac)

If the jump is **never taken**, execution always falls through to **“The Swamp Gate opens.”**

**Patch (elegant crack):**

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

## 3. Finding a valid key (no patch)

To get a **real** name+serial that pass the check without patching you must solve:

`compute_final(v29, v47, v17, v18) == 0xB9229933597558C9`

for one (name, serial) pair. The logic is implemented in `froggy_solver.py` (mix, FNV, `compute_final`). Solving for `(v17, v18)` requires inverting the mix function (unmix) and then solving for the serial; the current script’s unmix has edge cases. Options:

- Fix unmix (correct handling of high bits in the XOR-shift inverses), then solve for `v54`/`v17`/`v18` as in the script.
- Use a constraint solver (e.g. Z3) on the bit-vector formula for the whole check.
- Or use the patch above as the intended “elegant” solution.

---

## 4. Quick reference

| Item            | Value / Location                          |
|-----------------|-------------------------------------------|
| Target constant | `0xB9229933597558C9`                      |
| Comparison      | `cmp rcx, rax` at **0x2731**              |
| Patch           | Replace conditional jump at **0x2734** with `90 90` |
| Success message | “The Swamp Gate opens.” / “Froggy approves.” |
