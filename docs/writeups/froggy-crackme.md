# Froggy CrackMe – Soluție

**Categorie:** Reverse / CrackMe  
**Instrumente:** IDA Pro, Python, Z3 (opțional)

## Rezumat

- **Format serial:** `XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX` (32 cifre hex, 3 liniuțe).
- **Validare:** Numele și serialul sunt combinate (hash FNV + mix în stil splitmix64) și trebuie să satisfacă o singură comparație finală.
- **Punct slab elegant:** Un singur salt condiționat decide succesul. Patch-uind acel jump, programul acceptă orice input valid.

---

## 1. Flow-ul de validare (din reversing)

1. **Anti-debug:** Citește `/proc/self/status`, caută `TracerPid:`. Dacă e nenul → „Debugger detected. The swamp rejects you.”
2. **Input:** Cere **Name** și **Serial** (formatul de mai sus).
3. **Parsare serial:** 4 grupe de câte 8 cifre hex → două valori 64-bit:
   - `v17 = (grupa1 << 32) | grupa2`
   - `v18 = (grupa3 << 32) | grupa4`
4. **Hash-uri pe nume (FNV-1a, prim 0x100000001B3):**
   - Nume → hash → `v29 = hash ^ 0xA3B1957C4D2E1901`
   - Nume inversat → hash → `v47 = hash ^ 0xC0D0E0F112233445`
   - Nume gol: `v29 = 0xB7D49ACC3EB31A82`, `v47 = 0xD4B5EF4161BE37C6`
5. **Verificarea finală:** Un lanț de mix (stil splitmix64) și XOR/adunare folosește `v29`, `v47`, `v17`, `v18` și compară rezultatul cu **`0xB9229933597558C9`**.
   - În binar: **`cmp rcx, rax`** la **0x2731** (rax = 0xB9229933597558C9), apoi **un salt condiționat** (calea de eșec).

---

## 2. „Un singur path” / punctul slab elegant

Succesul e decis de **o** comparație și **un** salt condiționat:

- **0x2731:** `cmp rcx, rax` (valoarea calculată vs 0xB9229933597558C9)
- **0x2734:** salt condiționat (ex. `jnz` către „Wrong incantation” la 0x27ac)

Dacă saltul **nu se ia niciodată**, execuția trece mereu la **„The Swamp Gate opens.”**

### Patch (crack elegant)

- **Fișier:** `froggy_crackme` (sau copia ta).
- **Locație:** cei **2 octeți** ai instrucțiunii imediat după `cmp rcx, rax` (saltul condiționat la **0x2734**).
- **Original:** salt condiționat (ex. `75 xx` = `jnz`).
- **Patch:** înlocuiești cei 2 octeți cu **`90 90`** (două NOP-uri).

Apoi:

- Rulezi fără debugger (sau cu TracerPid 0).
- Introduci orice nume nevid și orice serial în formatul corect, ex:
  - **Name:** `Froggy`
  - **Serial:** `00000000-00000000-00000000-00000000`

Programul va deschide poarta oricum.

---

## 3. Găsirea unei chei valide (fără patch)

Pentru un cuplu **name + serial** care trece verificarea fără patch trebuie rezolvat:

`compute_final(v29, v47, v17, v18) == 0xB9229933597558C9`

Logica e implementată în `froggy_solver.py` (mix, FNV, `compute_final`). Rezolvarea pentru `(v17, v18)` necesită inversarea funcției mix (`unmix`) și apoi rezolvarea pentru serial; scriptul curent are cazuri limită la unmix. Opțiuni:

- Corectezi unmix (inverse XOR-shift pe toți biții), apoi rezolvi pentru `v54`/`v17`/`v18` ca în script.
- Folosești un constraint solver (ex. Z3) pe formula bit-vector a întregii verificări.
- Sau folosești patch-ul de mai sus ca soluție „elegantă”.

### Exemplu de rulare keygen (Z3)

Scriptul `key.py` folosește Z3 pentru a genera un serial valid pentru un nume dat:

```bash
python3 key.py "Froggy"
```

---

## 4. Referință rapidă

| Element          | Valoare / Locație                                   |
|------------------|------------------------------------------------------|
| Constantă target | `0xB9229933597558C9`                                 |
| Comparație       | `cmp rcx, rax` la **0x2731**                         |
| Patch            | Înlocuiești saltul condiționat la **0x2734** cu `90 90` |
| Mesaj succes     | „The Swamp Gate opens.” / „Froggy approves.”        |
