"""
Builds the local AlphaMissense copy used by switchlight_am.py. Run once from backend/:

    python build_am_index.py                 # streams DeepMind's file (643 MB) and keeps only the gene windows
    python build_am_index.py --file PATH.gz  # use a file you already downloaded
    python build_am_index.py --all           # keep every row (several GB of disk)

One-time download, deliberately no retry layer: if it fails, run it again.
AlphaMissense: Cheng et al. 2023, Science. (c) DeepMind, CC BY-NC-SA 4.0 (non-commercial use, attribution).
"""
import argparse
import datetime
import gzip
import io
import sqlite3
import sys

import requests

from switchlight_am import DB_PATH, GENE_WINDOWS

URL = "https://storage.googleapis.com/dm_alphamissense/AlphaMissense_hg38.tsv.gz"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    DB_PATH.parent.mkdir(exist_ok=True)
    tmp = DB_PATH.with_suffix(".building")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.executescript("""
        CREATE TABLE am (chrom TEXT, pos INTEGER, ref TEXT, alt TEXT, uniprot_id TEXT, transcript_id TEXT,
                         protein_variant TEXT, score REAL, class TEXT, PRIMARY KEY (chrom, pos, ref, alt));
        CREATE TABLE windows (chrom TEXT, start INTEGER, end INTEGER, label TEXT);
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);""")

    wins = {}
    for c, s, e, label in GENE_WINDOWS:
        wins.setdefault("chr" + c, []).append((s, e))
    prefixes = tuple(c + "\t" for c in wins)

    raw = open(args.file, "rb") if args.file else requests.get(URL, stream=True, timeout=60).raw
    text = io.TextIOWrapper(gzip.GzipFile(fileobj=raw), encoding="utf-8")
    batch, kept, seen = [], 0, 0
    for line in text:
        seen += 1
        if line[0] == "#" or (not args.all and not line.startswith(prefixes)):
            continue
        f = line.rstrip("\n").split("\t")
        chrom, pos = f[0], int(f[1])
        if not args.all and not any(s <= pos <= e for s, e in wins[chrom]):
            continue
        batch.append((chrom.replace("chr", ""), pos, f[2], f[3], f[5], f[6], f[7], float(f[8]), f[9]))
        if len(batch) >= 20000:
            con.executemany("INSERT OR IGNORE INTO am VALUES (?,?,?,?,?,?,?,?,?)", batch); kept += len(batch); batch = []
            print(f"\r{seen:,} lines read, {kept:,} kept", end="", file=sys.stderr)
    con.executemany("INSERT OR IGNORE INTO am VALUES (?,?,?,?,?,?,?,?,?)", batch); kept += len(batch)

    if args.all:
        con.execute("INSERT INTO meta VALUES ('whole_genome', '1')")
    for c, s, e, label in GENE_WINDOWS:
        con.execute("INSERT INTO windows VALUES (?,?,?,?)", (c, s, e, label))
    con.execute("INSERT INTO meta VALUES ('built', ?)", (datetime.date.today().isoformat(),))
    con.commit(); con.close()
    tmp.replace(DB_PATH)
    print(f"\nDone: {kept:,} rows from {seen:,} lines -> {DB_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
