"""Checks FARTKNIGHT levels: solvable with guard timing, gems reachable, walking paths.

Reads FKLVL.txt. Same rules as FKSRC.txt:
- Guards walk straight over . K G P and open T, otherwise they turn around
- Sight is 3 tiles straight ahead, blocked by W E H, crates and closed T
- Gate is open when the lever is on or a crate is on a plate
- Crate: onto . -> crate, onto P -> crate on plate, onto F -> both gone,
  onto open T -> crate in gate
- A crate cannot be pushed onto a guard
- Player makes STEPS steps per guard step

Usage: python FK_levelcheck.py [STEPS] [ghost]
"""
import heapq
import re
import sys
from collections import deque

STEPS = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2
D = {1: (0, 1), 2: (-1, 0), 3: (1, 0), 4: (0, -1)}
GHOST = "ghost" in sys.argv  # guards ignore crates: is blocking needed?


def load_levels(path="FKLVL.txt"):
    rows = re.findall(r'^"([.WKEGFBPTHX1234]{14})"$', open(path, encoding="utf-8").read(), re.M)
    assert len(rows) % 10 == 0, len(rows)
    rows = ["W" + r + "W" for r in rows]
    wall = "W" * 16
    return [[wall] + rows[i:i + 10] + [wall] for i in range(0, len(rows), 10)]


class Level:
    def __init__(self, rows):
        self.base = {}
        self.guards = []
        for y, r in enumerate(rows):
            for x, c in enumerate(r):
                if c == "X":
                    self.start = (x, y); c = "."
                elif c in "1234":
                    self.guards.append((x, y, int(c))); c = "."
                self.base[(x, y)] = c
        self.key = next(p for p, c in self.base.items() if c == "K")
        self.exit = next(p for p, c in self.base.items() if c == "E")
        self.gems = [p for p, c in self.base.items() if c == "G"]

    def tile(self, p, boxes, traps, picked):
        c = self.base[p]
        if p in boxes:
            return {"P": "Q", "T": "R"}.get(c, "B")
        if c == "B":
            return "."
        if c == "F" and p not in traps:
            return "."
        if c == "K" and p in picked:
            return "."
        return c


def solve(lv, goal, pri=None, limit=None):
    """BFS over (player, crates, traps, items, lever, guards, sub-step).

    pri(state) -> number: best-first instead of BFS (lowest first, finds a
    solution fast but not the shortest). limit: give up after that many states.
    """
    boxes0 = frozenset(p for p, c in lv.base.items() if c == "B")
    traps0 = frozenset(p for p, c in lv.base.items() if c == "F")
    s0 = (lv.start, boxes0, traps0, frozenset(), 0, tuple(lv.guards), 0)
    prev = {s0: None}
    q = deque([s0]) if pri is None else [(0, 0, s0)]

    def is_open(boxes, lever):
        return lever or any(lv.base[b] == "P" for b in boxes)

    def seen_by(pos, guards, boxes, traps, picked, opened):
        block = "WEBHQR" + ("" if opened else "T")
        if GHOST:
            boxes = frozenset()
        for gx, gy, gd in guards:
            x, y = gx, gy
            for _ in range(4):
                if (x, y) == pos:
                    return True
                dx, dy = D[gd]
                x, y = x + dx, y + dy
                if lv.tile((x, y), boxes, traps, picked) in block:
                    break
        return False

    def guards_step(guards, boxes, traps, picked, opened):
        free = ".KGP" + ("T" if opened else "")
        if GHOST:
            boxes = frozenset()
        out = []
        for gx, gy, gd in guards:
            dx, dy = D[gd]
            t = (gx + dx, gy + dy)
            if lv.tile(t, boxes, traps, picked) in free:
                out.append((t[0], t[1], gd))
            else:
                out.append((gx, gy, 5 - gd))
        return tuple(out)

    while q:
        if limit and len(prev) > limit:
            break
        s = q.popleft() if pri is None else heapq.heappop(q)[2]
        pos, boxes, traps, picked, lever, guards, sub = s
        opened = is_open(boxes, lever)
        nexts = []
        # wait: guards move
        g2 = guards_step(guards, boxes, traps, picked, opened)
        if not seen_by(pos, g2, boxes, traps, picked, opened):
            nexts.append((pos, boxes, traps, picked, lever, g2, 0))
        if sub < STEPS:
            for d in (1, 2, 3, 4):
                dx, dy = D[d]
                t = (pos[0] + dx, pos[1] + dy)
                c = lv.tile(t, boxes, traps, picked)
                nb, nt, npk, nl, np_ = boxes, traps, picked, lever, t
                if c == "W":
                    continue
                if c == "H":
                    nl, np_ = 1 - lever, pos
                elif c == "T" and not opened:
                    continue
                elif c == "E":
                    if lv.key in picked and goal is None:
                        return s, prev
                    continue
                elif c == "F":
                    continue
                elif c in "BQR":
                    t2 = (t[0] + dx, t[1] + dy)
                    c2 = lv.tile(t2, boxes, traps, picked)
                    if c2 not in ".PF" + ("T" if opened else "") or any((gx, gy) == t2 for gx, gy, _ in guards):
                        continue
                    b = set(boxes); b.discard(t)
                    if c2 == "F":
                        tt = set(traps); tt.discard(t2); nt = frozenset(tt)
                    else:
                        b.add(t2)
                    nb = frozenset(b)
                elif c == "K":
                    npk = picked | {t}
                ns = (np_, nb, nt, npk, nl, guards, sub + 1)
                if np_ == goal:
                    prev[ns] = s
                    return ns, prev
                if not seen_by(np_, guards, nb, nt, npk, is_open(nb, nl)):
                    nexts.append(ns)
        for ns in nexts:
            if ns not in prev:
                prev[ns] = s
                if pri is None:
                    q.append(ns)
                else:
                    heapq.heappush(q, (pri(ns), len(prev), ns))
    return None, prev


def moves(end, prev):
    n = 0
    while prev[end] is not None:
        if end[0] != prev[end][0]:
            n += 1
        end = prev[end]
    return n


def walk(lv, a, b):
    """Shortest static path (only walls/gates/levers block)."""
    q = deque([(a, 0)]); seen = {a}
    while q:
        p, n = q.popleft()
        if p == b:
            return n
        for dx, dy in D.values():
            t = (p[0] + dx, p[1] + dy)
            if t not in seen and lv.base.get(t, "W") not in "WH":
                seen.add(t); q.append((t, n + 1))
    return None


if __name__ == "__main__":
    for i, rows in enumerate(load_levels(), 1):
        lv = Level(rows)
        end, prev = solve(lv, None)
        res = f"solvable, {moves(end, prev) + 1} steps" if end else "NOT SOLVABLE"
        print(f"Level {i}: {res}; path key->exit {walk(lv, lv.key, lv.exit)}")
        for g in lv.gems:
            e, p = solve(lv, g)
            print(f"   Gem {g}: " + (f"{moves(e, p)} steps" if e else "UNREACHABLE"))
