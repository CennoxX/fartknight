"""Convert Axe/TI-BASIC source text (.txt) into a TI-83+/84+ program (.8xp).

Tokenizes like SourceCoder 3: greedy longest match against AxeTokens.xml
(Runer112, distributed with TokenIDE), leading indentation is dropped,
each line ends with the newline token $3F.

Usage:
    python txt28xp.py FKSRC.txt              -> FKSRC.8xp, program name FKSRC
    python txt28xp.py in.txt out.8xp -n NAME -a
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET

NS = "{http://merthsoft.com/Tokens}"
HERE = os.path.dirname(os.path.abspath(__file__))
COMMENT = b"Created by SourceCoder 3 - sc.cemetech.net"


def load_tokens(path):
    """Return {text: bytes} for every token string and alternative spelling."""
    table = {}

    def walk(node, prefix):
        for tok in node.findall(NS + "Token"):
            seq = prefix + bytes([int(tok.get("byte").lstrip("$"), 16)])
            names = [tok.get("string")] + [a.get("string") for a in tok.findall(NS + "Alt")]
            for name in names:
                # First definition wins, so single-byte tokens beat later duplicates.
                if name and name not in table:
                    table[name] = seq
            walk(tok, seq)

    walk(ET.parse(path).getroot(), b"")
    return table


def tokenize(text, table):
    maxlen = max(map(len, table))
    out = bytearray()
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for lineno, line in enumerate(lines, 1):
        line = line.lstrip("\t ")
        i = 0
        while i < len(line):
            for n in range(min(maxlen, len(line) - i), 0, -1):
                seq = table.get(line[i:i + n])
                if seq is not None:
                    out += seq
                    i += n
                    break
            else:
                sys.exit(f"Zeile {lineno}, Spalte {i + 1}: kein Token für {line[i]!r}")
        if lineno < len(lines):
            out.append(0x3F)
    return bytes(out)


def build_8xp(name, tokens, archived=False):
    if len(tokens) > 0xFFFF - 2:
        sys.exit("Programm zu groß")
    body = len(tokens).to_bytes(2, "little") + tokens
    varlen = len(body).to_bytes(2, "little")
    entry = (b"\x0D\x00" + varlen + b"\x05" + name.encode("ascii").ljust(8, b"\0")
             + b"\x00" + (b"\x80" if archived else b"\x00") + varlen + body)
    header = b"**TI83F*\x1A\x0A\x00" + COMMENT.ljust(42, b"\0")[:42]
    checksum = (sum(entry) & 0xFFFF).to_bytes(2, "little")
    return header + len(entry).to_bytes(2, "little") + entry + checksum


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input")
    ap.add_argument("output", nargs="?", help="Standard: Eingabename mit .8xp")
    ap.add_argument("-n", "--name", help="Programmname auf dem Rechner (Standard: Dateiname)")
    ap.add_argument("-a", "--archive", action="store_true", help="im Archiv ablegen")
    ap.add_argument("-t", "--tokens", default=os.path.join(HERE, "AxeTokens.xml"))
    args = ap.parse_args()

    base = os.path.splitext(args.input)[0]
    output = args.output or base + ".8xp"
    name = (args.name or os.path.basename(base)).upper()
    if not (1 <= len(name) <= 8 and name[0].isalpha() and name.isalnum()):
        sys.exit(f"Ungültiger Programmname {name!r}: 1-8 Zeichen A-Z/0-9, erstes ein Buchstabe")

    with open(args.input, encoding="utf-8-sig") as f:
        tokens = tokenize(f.read(), load_tokens(args.tokens))
    with open(output, "wb") as f:
        f.write(build_8xp(name, tokens, args.archive))
    print(f"{output}: {name}, {len(tokens)} Bytes")


if __name__ == "__main__":
    main()
