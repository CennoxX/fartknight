"""Fast check for FARTKNIGHT levels, same rules as FK_levelcheck.py.

Best-first search towards progress (traps filled, gate open, key taken):
finds a solution in seconds, but not necessarily the shortest one.
Prints the important events of the solution, checks the gems and, with
"need", whether every crate, trap, guard and gate actually matters.
Coordinates include the wall border (like FK_levelcheck.py).

Usage: python FK_fastcheck.py LEVEL [ghost] [need] [steps=N] [limit=N]
  LEVEL  number of a level in FKLVL.txt, or a text file with a draft:
         10 rows of 14 tiles (border is added) or 12 rows of 16,
         quotes are allowed
  ghost  guards ignore crates (is blocking guards needed?)
  need   remove each crate/trap/guard/gate once and solve again
  limit  give up after N states (default 400000, about a minute)
"""
import os
import re
import sys
import time

import FK_levelcheck as F

HERE = os.path.dirname(os.path.abspath(__file__))
TILES = "[.WKEGFBPTHX1234]"


def load(arg):
    if arg.isdigit():
        return F.load_levels(os.path.join(HERE, "FKLVL.txt"))[int(arg) - 1]
    rows = []
    for line in open(arg, encoding="utf-8"):
        line = line.strip().strip('"')
        if re.fullmatch(TILES + "{14}|" + TILES + "{16}", line):
            rows.append(line)
    if len(rows) == 10 and all(len(r) == 14 for r in rows):
        return ["W" * 16] + ["W" + r + "W" for r in rows] + ["W" * 16]
    assert len(rows) == 12 and all(len(r) == 16 for r in rows), \
        f"need 10x14 or 12x16, got {len(rows)} rows"
    return rows


def progress(lv):
    """Lower is better: filled traps, open gate, taken key."""
    def pri(s):
        pos, boxes, traps, picked, lever, guards, sub = s
        opened = lever or any(lv.base[b] == "P" for b in boxes)
        return -(10 * (lv.ntraps - len(traps)) + 20 * opened + 40 * len(picked))
    return pri


def run(rows, goal_gem=None, limit=400000):
    lv = F.Level(rows)
    lv.ntraps = sum(c == "F" for c in lv.base.values())
    goal = None if goal_gem is None else lv.gems[goal_gem]
    t = time.time()
    end, prev = F.solve(lv, goal, progress(lv), limit)
    return lv, end, prev, time.time() - t


def events(end, prev):
    """Pushes, filled traps, key and lever changes along the solution."""
    path = []
    s = end
    while s is not None:
        path.append(s)
        s = prev[s]
    path.reverse()
    out = []
    for a, b in zip(path, path[1:]):
        if a[1] != b[1]:
            gone, new = sorted(a[1] - b[1]), sorted(b[1] - a[1])
            what = f"crate {gone[0]} -> {new[0]}" if new else f"crate {gone[0]} into trap"
            out.append(f"{a[0]} pushes {what}")
        if a[3] != b[3]:
            out.append(f"{b[0]} takes key")
        if a[4] != b[4]:
            out.append(f"{a[0]} lever {'on' if b[4] else 'off'}")
    return out


def result(end, prev, limit, exit_goal=True):
    if end:
        return f"{F.moves(end, prev) + exit_goal} steps"
    return "gave up (limit)" if len(prev) > limit else "NOT SOLVABLE"


def variants(rows):
    """One copy of the level per removable element."""
    names = {"B": "crate", "F": "trap", "T": "gate", "1": "guard", "2": "guard",
             "3": "guard", "4": "guard"}
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            if c in names:
                copy = list(rows)
                copy[y] = r[:x] + "." + r[x + 1:]
                yield f"without {names[c]} {(x, y)}", copy


def main():
    args = sys.argv[1:]
    opts = dict(a.split("=") for a in args if "=" in a)
    F.STEPS = int(opts.get("steps", 2))
    F.GHOST = "ghost" in args
    limit = int(opts.get("limit", 400000))
    level = next(a for a in args if "=" not in a and a not in ("ghost", "need"))
    rows = load(level)
    print("\n".join(rows))

    lv, end, prev, dt = run(rows, None, limit)
    print(f"\nExit: {result(end, prev, limit)} ({dt:.1f}s, {len(prev)} states)")
    if end:
        print("  " + "\n  ".join(events(end, prev)))
    for i, g in enumerate(lv.gems):
        _, e, p, dt = run(rows, i, limit)
        print(f"Gem {g}: {result(e, p, limit, False)} ({dt:.1f}s)")

    if "need" in args:
        print("\nNeed test (steps are not minimal, compare roughly):")
        for name, copy in variants(rows):
            _, e, p, dt = run(copy, None, limit)
            print(f"  {name:24} {result(e, p, limit)}")


if __name__ == "__main__":
    main()
