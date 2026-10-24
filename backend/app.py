"""
Run with: uvicorn app:app --reload --port 8000

Requires real network access -- won't work in a sandboxed environment.
Install deps first: pip install fastapi uvicorn requests pysam
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from variant_scorer import (
    score_known_modifier, list_known_modifiers_by_gene,
    score_novel_variant, KNOWN_MODIFIERS,
)
from gnomad_lookup import fetch_allele_frequency
from sequence_lookup import fetch_flank
from alphamissense_lookup import query_exact_variant, vep_alphamissense

app = FastAPI(title="Sickle Cell Variant Explorer API")

# Allow the frontend (served from a different port/origin) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this before deploying anywhere public
    allow_methods=["*"],
    allow_headers=["*"],
)

# Real, dbSNP-confirmed genomic coordinates -- only populate entries you've
# personally verified (search "<rsID> dbSNP NCBI", read "Position GRCh38").
# Unverified known modifiers still work via direct rsID lookup; they just
# can't be reached by clicking a position on the 3D helix yet.
# All 22 positions below (GRCh38) were checked against both Ensembl REST and NCBI
# dbSNP (refsnp API) and matched. Note Ensembl imports its variants from dbSNP, so
# this confirms the two services agree, not an independent third source.
# rs66650371 is a small deletion (chr6:135097495-135097499), so only its start is keyed.
CONFIRMED_COORDINATES = {
    "2:60490908": "rs1427407",  # GRCh38
    "2:60493816": "rs4671393",
    "2:60493111": "rs11886868",
    "2:60492835": "rs766432",
    "2:60494212": "rs7557939",
    "2:60460824": "rs7569946",
    "2:60487726": "rs6545816",
    "2:60498316": "rs7606173",
    "2:60493454": "rs10195871",
    "2:60494905": "rs6706648",
    "6:135097880": "rs9399137",
    "6:135105435": "rs4895441",
    "6:135055071": "rs28384513",
    "6:135106679": "rs9402686",
    "6:135097495": "rs66650371",
    "6:135097904": "rs35786788",
    "6:135103041": "rs35959442",
    "11:5254939": "rs7482144",
    "22:35380679": "rs2071746",
    "2:69092659": "rs4527238",
    "2:69098684": "rs35685045",
    "14:61740839": "rs11549465"
}


@app.get("/api/known/{rsid}")
def get_known_modifier(rsid: str):
    result = score_known_modifier(rsid)
    if not result:
        raise HTTPException(status_code=404, detail=f"{rsid} not in known modifiers table")
    return result


@app.get("/api/full/{rsid}")
def get_full_known_variant(rsid: str):
    """
    Everything we can honestly say about a known modifier in one call: the
    published meta-analysis row, plus (only if its coordinate is verified)
    the real flanking sequence and gnomAD frequency for its effect allele.
    """
    known = score_known_modifier(rsid)
    if not known:
        raise HTTPException(status_code=404, detail=f"{rsid} not in known modifiers table")
    coord = next((k for k, v in CONFIRMED_COORDINATES.items() if v == rsid), None)
    out = {"known": known, "coordinate": coord, "sequence": None, "gnomad": None, "note": None}
    if not coord:
        out["note"] = "No verified genomic coordinate for this variant yet, so live sequence and gnomAD lookups are unavailable."
        return out
    chrom, pos = coord.split(":")
    notes = []
    try:
        out["sequence"] = fetch_flank(chrom, int(pos))
    except Exception as e:
        notes.append(f"Sequence lookup failed: {e}")
    ref = known.get("ref_allele")
    alt = known.get("effect_allele")
    if alt and len(alt) == 1 and alt != ref:
        try:
            out["gnomad"] = fetch_allele_frequency(chrom, int(pos), ref, alt)
        except Exception as e:
            notes.append(f"gnomAD lookup failed: {e}")
    elif alt:
        notes.append(f"The studied letter ({alt}) is the reference base or not a single letter, so there is no alternate allele to query in gnomAD.")
    out["note"] = " ".join(notes) or None
    return out


@app.get("/api/alphamissense/{rsid}")
def get_alphamissense_for_known(rsid: str):
    """
    AlphaMissense score(s) for a known modifier's position. Kept separate from
    /api/full because the remote lookup is slower. It only scores missense
    (protein-changing) variants, so most of the 22 will honestly return no score.
    """
    known = score_known_modifier(rsid)
    if not known:
        raise HTTPException(status_code=404, detail=f"{rsid} not in known modifiers table")
    chrom, pos, ref = known["chrom"], known["pos"], known["ref_allele"]
    alts = [a for a in (known["alt_alleles"] or []) if len(a) == 1 and len(ref) == 1]
    if not alts:
        return {"rsid": rsid, "scores": [], "note": "This is an insertion/deletion; AlphaMissense only scores single-letter protein changes."}
    try:
        looked = [vep_alphamissense(chrom, pos, ref, a) for a in alts]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AlphaMissense lookup failed: {e}")
    scores = [x["score"] for x in looked if x["score"]]
    consequence = next((x["consequence"] for x in looked if x["consequence"]), None)
    note = None if scores else (
        f"AlphaMissense has no score for {rsid} (chr{chrom}:{pos}). It only scores changes that alter a protein. "
        f"Ensembl classifies this variant as {consequence.replace('_', ' ') if consequence else 'non-coding'}, "
        f"in: {known['location']}.")
    return {"rsid": rsid, "chrom": chrom, "pos": pos, "ref": ref, "scores": scores,
            "consequence": consequence, "note": note}


@app.get("/api/known-by-gene/{gene}")
def get_known_modifiers_for_gene(gene: str):
    return list_known_modifiers_by_gene(gene)


@app.get("/api/novel")
def get_novel_variant_score(am_score: float, allele_count: int, total_alleles: int = 800_000):
    if not 0 <= am_score <= 1:
        raise HTTPException(status_code=400, detail="am_score must be between 0 and 1")
    return score_novel_variant(am_score, allele_count, total_alleles)


@app.get("/api/sequence")
def get_sequence(chrom: str, pos: int):
    try:
        return fetch_flank(chrom, pos)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Ensembl lookup failed: {e}")


@app.get("/api/gnomad")
def get_gnomad_frequency(chrom: str, pos: int, ref: str, alt: str):
    try:
        return fetch_allele_frequency(chrom, pos, ref, alt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"gnomAD lookup failed: {e}")


@app.get("/api/variant-at-position")
def get_variant_at_position(chrom: str, pos: int, alt: str):
    """
    The main endpoint the 3D helix calls when a position is tapped.
    Routes to the known-modifier path if this position has a confirmed
    coordinate match; otherwise runs the FULL real novel-variant path:
    live AlphaMissense query + live gnomAD query + ACMG classification.

    'alt' (the proposed alternate base) must be supplied by the caller --
    a tapped position alone doesn't specify which base it's being mutated
    to, and AlphaMissense scores are specific to a particular ref>alt change.
    """
    coord_key = f"{chrom}:{pos}"
    sequence = fetch_flank(chrom, pos)
    ref = sequence["sequence"][sequence["variant_index_in_sequence"]]

    if coord_key in CONFIRMED_COORDINATES:
        rsid = CONFIRMED_COORDINATES[coord_key]
        return {
            "path": "known_modifier",
            "sequence": sequence,
            "data": score_known_modifier(rsid),
        }

    if alt.upper() == ref.upper():
        return {
            "path": "novel_variant", "sequence": sequence, "gnomad": None, "data": None,
            "note": f"The changed letter {alt} is the same as the GRCh38 reference base at "
                    f"chr{chrom}:{pos}, so there is no change to score. If this came from a file, "
                    f"its REF letter does not match GRCh38 at this position (wrong genome build or position).",
        }

    # Real novel-variant path: live AlphaMissense + live gnomAD.
    try:
        am_result = query_exact_variant(chrom, pos, ref, alt)
        gnomad_result = fetch_allele_frequency(chrom, pos, ref, alt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Live lookup failed: {e}")
    allele_count = gnomad_result.get("ac", 0)

    if am_result is None:
        # AlphaMissense only scores missense (protein-coding) variants --
        # a real, expected "miss" for anything in a non-coding/regulatory
        # region, not a bug. Report this honestly rather than guessing.
        return {
            "path": "novel_variant",
            "sequence": sequence,
            "gnomad": gnomad_result,
            "data": None,
            "note": f"AlphaMissense has no score for {chrom}:{pos} {ref}>{alt} -- "
                     "likely a non-coding/regulatory position, which AlphaMissense "
                     "doesn't evaluate (it only scores missense/coding variants).",
        }

    scored = score_novel_variant(am_result["am_pathogenicity"], allele_count)
    return {
        "path": "novel_variant",
        "sequence": sequence,
        "gnomad": gnomad_result,
        "alphamissense_raw": am_result,
        "data": scored,
    }


@app.get("/api/all-known-modifiers")
def list_all_known_modifiers():
    return {rsid: score_known_modifier(rsid) for rsid in KNOWN_MODIFIERS}
