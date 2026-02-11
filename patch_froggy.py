#!/usr/bin/env python3
"""
Patch Froggy CrackMe so the gate always opens (elegant weakness).
Patch: replace the conditional jump after "cmp rcx, rax" with NOPs.

Usage: python3 patch_froggy.py /path/to/froggy_crackme
Creates froggy_crackme_patched (or overwrites if -f).
"""
import sys
import shutil

# From IDA: cmp rcx, rax at 0x2731, next instruction at 0x2734 (file offset = 0x2734 in ELF .text)
# We need the file offset of 0x2734. For a typical ELF, .text at 0x1000, so 0x2734 might be at file offset 0x1f34 or similar.
# IDA base is 0, so virtual 0x2734. If .text VMA is 0x1000, then file offset = 0x2734 - 0x1000 + file_offset_of_text.
# idb_meta: base 0x0, so 0x2734 is likely file offset 0x2734 - 0x1000 = 0x1734 if .text starts at 0x1000. Actually for PIE/base 0, often file offset equals VA. So try 0x2734.
JUMP_OFFSET = 0x2734  # virtual address of the JNZ (after cmp)
NOP_PATCH = bytes([0x90, 0x90])  # 2 NOPs to replace 2-byte short jump

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch_froggy.py /path/to/froggy_crackme [-f]")
        sys.exit(1)
    path = sys.argv[1]
    force = "-f" in sys.argv
    out_path = path + "_patched" if not force else path
    if not force and out_path == path:
        out_path = path + "_patched"

    with open(path, "rb") as f:
        data = bytearray(f.read())

    # ELF: find .text section to convert VA to file offset
    if data[:4] != b"\x7fELF":
        print("Not an ELF file")
        sys.exit(1)
    # Minimal: assume 64-bit ELF, program headers
    e_phoff = int.from_bytes(data[0x20:0x28], "little")
    e_phnum = int.from_bytes(data[0x38:0x3a], "little")
    file_offset = None
    for i in range(e_phnum):
        ph = e_phoff + i * 0x38
        p_type = int.from_bytes(data[ph : ph + 4], "little")
        if p_type != 1:  # PT_LOAD
            continue
        p_vaddr = int.from_bytes(data[ph + 0x10 : ph + 0x18], "little")
        p_offset = int.from_bytes(data[ph + 0x08 : ph + 0x10], "little")
        p_memsz = int.from_bytes(data[ph + 0x28 : ph + 0x30], "little")
        if p_vaddr <= JUMP_OFFSET < p_vaddr + p_memsz:
            file_offset = p_offset + (JUMP_OFFSET - p_vaddr)
            break
    if file_offset is None:
        # Fallback: try raw offset (non-PIE)
        file_offset = JUMP_OFFSET
        if file_offset >= len(data) or file_offset + 2 > len(data):
            print("Could not find segment for 0x%x; try setting JUMP_OFFSET" % JUMP_OFFSET)
            sys.exit(1)

    original = bytes(data[file_offset : file_offset + 2])
    data[file_offset : file_offset + 2] = NOP_PATCH
    with open(out_path, "wb") as f:
        f.write(data)
    print("Patched at file offset 0x%x: %s -> 90 90" % (file_offset, original.hex()))
    print("Saved to:", out_path)
    print("Run with any name and serial (e.g. 00000000-00000000-00000000-00000000).")

if __name__ == "__main__":
    main()
