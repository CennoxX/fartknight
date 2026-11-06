# FARTKNIGHT

A stealth/puzzle game for the TI-83+ written in [Axe](https://axe.eeems.ca/).
Sneak Sir Fartalot past patrolling guards, push crates onto plates and into traps,
pull levers, collect gems and grab the key to reach the exit.

![Title screen](fartknight_96x64.png)

## Play

Send these two files to your calculator (TI Connect CE, TILP or an emulator):

- `FKNIGHT.8Xp` – the game
- `FKLVLS.8Xv` – the levels (AppVar, must be on the calculator)

Run it with `Asm(prgmFKNIGHT)` from the home screen, or from a shell such as MirageOS or No Shell.

## Controls

| Key | Action |
|-----|--------|
| Arrows | Move (hold to repeat) |
| 2nd | Action |
| MODE | Restart level (costs a life) |
| CLEAR | Back to title |
| Alpha | High Score (from title) |

## Repository layout

| File | Purpose |
|------|---------|
| `source/FKSRC.txt` | Game source (Axe), compiles to `FKNIGHT` |
| `source/FKLVL.txt` | Level data and poems, included by `FKDATSRC` |
| `source/FKDATSRC.txt` | Level packer: writes the levels into AppVar `FKLVLS` |
| `tools/fk_editor.html` | Browser level editor (import/export `FKLVL.txt`) |
| `tools/FK_levelcheck.py` | Exact solver: checks solvability, guard timing, gem reachability |
| `tools/FK_fastcheck.py` | Fast best-first solver, also for draft levels |
| `tools/txt28xp.py` | Converts `.txt` source into `.8xp` programs (uses `tools/AxeTokens.xml`) |

## Building from source

Only needed if you want to change the game or the levels. Requirements: Python 3, the Axe Parser app (`Axe.8xk`) on the calculator or in an emulator
(e.g. jsTIfied, Wabbitemu, CEmu for 84+).

1. Convert the sources:
   ```bash
   python tools/txt28xp.py FKSRC.txt
   python tools/txt28xp.py FKLVL.txt
   python tools/txt28xp.py FKDATSRC.txt
   ```
2. Send `FKSRC.8xp`, `FKLVL.8xp`, `FKDATSRC.8xp` to the calculator.
3. In Axe, compile `FKDATSRC` and run the result once. It creates AppVar `FKLVLS`.
   Do this again after every level change.
4. Compile `FKSRC`. This produces `FKNIGHT`.
5. Play `FKNIGHT`.

## Level design

Make levels in `fk_editor.html`, copy them into `FKLVL.txt`. Check them with:

```bash
python FK_levelcheck.py 1
```

```bash
python FK_fastcheck.py 5 need
```

Test with `steps=1` (one player step per guard step).

Tiles: `W` wall, `.` floor, `X` start, `K` key, `E` exit, `G` gem, `F` trap, `B` crate,
`P` plate, `T` gate, `H` lever, `1`–`4` guard facing down/left/right/up.

## Credits

- [Axe Parser](https://axe.eeems.ca/) by Quigibo
- `AxeTokens.xml` by Runer112, from TokenIDE
