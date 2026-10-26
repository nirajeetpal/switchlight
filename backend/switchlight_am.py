"""
Switchlight-AM: a small retrieval-grounded AlphaMissense module.

  retrieve  -> look the variant up in a LOCAL copy of AlphaMissense (SQLite, built once by
               build_am_index.py from DeepMind's file). Nothing is sent over the network.
  fall back -> if the position is outside the indexed gene windows (or no local copy exists),
               ask Ensembl VEP instead (see alphamissense_lookup.vep_alphamissense).
  explain   -> write a plain-language explanation using ONLY the retrieved row(s) plus the
               variant's known context. This step is rule-based text today; it is the place
               an LLM could be swapped in, with the retrieved rows as its only source.

AlphaMissense data: Cheng et al. 2023, Science. (c) 2023 DeepMind Technologies Limited,
CC BY-NC-SA 4.0 (non-commercial, share-alike, attribution required).
"""

import pathlib
import sqlite3

from alphamissense_lookup import vep_alphamissense

DB_PATH = pathlib.Path(__file__).parent / "data" / "alphamissense_local.sqlite"

# AlphaMissense's own published classes (Cheng et al. 2023)
BENIGN_BELOW, PATHOGENIC_ABOVE = 0.34, 0.564

# GRCh38 windows (1-based, chromosome without "chr") covering the genes this app studies.
# HBB sits inside the chr11 window because it holds the sickle cell mutation itself.
GENE_WINDOWS = [
    ("2", 60_400_000, 60_600_000, "BCL11A"),
    ("6", 135_000_000, 135_500_000, "HBS1L-MYB"),
    ("11", 5_200_000, 5_300_000, "HBB / HBG1 / HBG2"),
    ("22", 35_350_000, 35_420_000, "HMOX1"),
    ("2", 69_000_000, 69_500_000, "ANTXR1"),
    ("14", 61_650_000, 61_800_000, "HIF1A"),
]


def _connect():
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) if DB_PATH.exists() else None


def status() -> dict:
    con = _connect()
    if not con:
        return {"indexed": False, "note": "No local AlphaMissense copy. Run: python build_am_index.py"}
    try:
        rows = con.execute("SELECT COUNT(*) FROM am").fetchone()[0]
        windows = con.execute("SELECT chrom, start, end, label FROM windows").fetchall()
        built = con.execute("SELECT value FROM meta WHERE key='built'").fetchone()
        return {"indexed": True, "rows": rows, "built": built[0] if built else None,
                "windows": [{"chrom": c, "start": s, "end": e, "label": l} for c, s, e, l in windows]}
    finally:
        con.close()


def _covered(con, chrom, pos) -> bool:
    if con.execute("SELECT 1 FROM meta WHERE key='whole_genome'").fetchone():
        return True
    return con.execute("SELECT 1 FROM windows WHERE chrom=? AND start<=? AND end>=? LIMIT 1",
                       (str(chrom), pos, pos)).fetchone() is not None


def retrieve(chrom: str, pos: int, ref: str, alt: str) -> dict:
    """Returns {"covered": bool, "row": dict | None} from the local copy."""
    con = _connect()
    if not con:
        return {"covered": False, "row": None}
    try:
        if not _covered(con, chrom, pos):
            return {"covered": False, "row": None}
        r = con.execute("SELECT uniprot_id, transcript_id, protein_variant, score, class FROM am "
                        "WHERE chrom=? AND pos=? AND ref=? AND alt=?", (str(chrom), pos, ref, alt)).fetchone()
        if not r:
            return {"covered": True, "row": None}
        return {"covered": True, "row": {
            "chrom": str(chrom), "pos": pos, "ref": ref, "alt": alt, "uniprot_id": r[0], "transcript_id": r[1],
            "protein_variant": r[2], "am_pathogenicity": r[3], "am_class": r[4]}}
    finally:
        con.close()


def explain(scores: list, source: str, context: dict) -> str:
    """Grounded text: every number and name below comes from the retrieved rows or the given context."""
    where = "the local AlphaMissense copy" if source == "local" else "Ensembl's live AlphaMissense data"
    if scores:
        parts = []
        for s in scores:
            label = {"likely_benign": "likely harmless", "likely_pathogenic": "likely harmful"}.get(s["am_class"], "uncertain")
            parts.append(f"{s.get('protein_variant') or 'this change'} scores {s['am_pathogenicity']:.3f} ({label})")
        return (f"From {where}: " + "; ".join(parts) + ". AlphaMissense calls scores below "
                f"{BENIGN_BELOW} likely harmless and above {PATHOGENIC_ABOVE} likely harmful. This is about damage to the "
                "protein only; it says nothing about fetal hemoglobin.")
    loc = context.get("location")
    return (f"No score in {where}. AlphaMissense only scores single-letter changes that alter a protein"
            + (f", and this variant sits in: {loc}." if loc else ".") + " That is expected for most of the published fetal hemoglobin variants.")


def score_variants(chrom: str, pos: int, ref: str, alts: list, context: dict | None = None) -> dict:
    """Retrieve each alt from the local copy; fall back to live Ensembl if the position is not indexed."""
    context = context or {}
    scores, source, consequence = [], "local", None
    for alt in alts:
        got = retrieve(chrom, pos, ref, alt)
        if got["covered"]:
            if got["row"]:
                scores.append(got["row"])
            continue
        source = "ensembl-vep"
        live = vep_alphamissense(chrom, pos, ref, alt)
        consequence = consequence or live.get("consequence")
        if live["score"]:
            scores.append(live["score"])
    return {"scores": scores, "source": source, "consequence": consequence,
            "explanation": explain(scores, source, context)}
