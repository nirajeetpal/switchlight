"""
Queries AlphaMissense's real precomputed pathogenicity scores -- this IS
the actual AI model in this project: a deep learning model from Google
DeepMind (Cheng et al. 2023, Science, doi:10.1126/science.adg7492) that
predicts missense variant pathogenicity.

Rather than downloading the full genome-wide file (tens of GB), this uses
pysam's remote tabix support to fetch just the rows for a given region
directly over HTTPS -- the file is already bgzip-compressed and
tabix-indexed by DeepMind/Ensembl, which is exactly what makes this
possible.

Requires: pip install pysam
Requires real network access -- won't work in a sandboxed environment.

Data source: https://storage.googleapis.com/dm_alphamissense/AlphaMissense_hg38.tsv.gz
License: CC-BY 4.0, AlphaMissense Database (c) 2023 DeepMind Technologies Limited.
Cite: Cheng J, Novati G, Pan J, et al. "Accurate proteome-wide missense
variant effect prediction with AlphaMissense." Science. 2023.
"""

import requests
from resilient import cached_request

try:
    import pysam  # only needed for the (currently unusable) remote-tabix route below
except ImportError:  # pragma: no cover
    pysam = None

ENSEMBL_REST = "https://rest.ensembl.org"

ALPHAMISSENSE_URL = "https://storage.googleapis.com/dm_alphamissense/AlphaMissense_hg38.tsv.gz"

# Column order per the file's documented format (CHROM, POS, REF, ALT,
# genome, uniprot_id, transcript_id, protein_variant, am_pathogenicity,
# am_class). VERIFY this against the first row you actually get back --
# file formats occasionally add/reorder columns between releases.
COLUMNS = ["chrom", "pos", "ref", "alt", "genome", "uniprot_id",
           "transcript_id", "protein_variant", "am_pathogenicity", "am_class"]


def query_region(chrom: str, start: int, end: int) -> list[dict]:
    """
    Fetches all AlphaMissense-scored variants in a genomic region.
    chrom should be WITHOUT 'chr' prefix (e.g. "2", not "chr2") -- confirm
    this matches the file's own convention on your first real query.
    """
    tbx = pysam.TabixFile(ALPHAMISSENSE_URL)
    results = []
    for row in tbx.fetch(chrom, start, end):
        fields = row.split("\t")
        results.append(dict(zip(COLUMNS, fields)))
    tbx.close()
    return results


def vep_alphamissense(chrom: str, pos: int, ref: str, alt: str) -> dict:
    """
    AlphaMissense via Ensembl's VEP REST service (AlphaMissense=1). This replaces the
    remote-tabix route above: DeepMind publishes AlphaMissense_hg38.tsv.gz without a
    .tbi index (the index URL returns 404), so pysam cannot read it remotely.

    Returns {"score": dict | None, "consequence": most severe consequence term}.
    "score" is None when AlphaMissense has nothing, which is expected for any
    variant that does not change a protein (intronic, intergenic, promoter...).
    """
    status, result = cached_request(
        "GET", f"{ENSEMBL_REST}/vep/human/region/{chrom}:{pos}-{pos + len(ref) - 1}:1/{alt}",
        params={"AlphaMissense": 1, "canonical": 1}, headers={"Content-Type": "application/json"},
    )
    if status == 400:
        # e.g. "request for consequence of [G] matches reference [G]": the alt is the reference base
        return {"score": None, "consequence": None, "error": result.get("error", "bad request")}
    if status != 200:
        raise RuntimeError(f"Ensembl VEP returned HTTP {status}")
    if not result:
        return {"score": None, "consequence": None}
    entry = result[0]
    hits = [t for t in entry.get("transcript_consequences", []) if t.get("alphamissense")]
    # prefer the canonical transcript so the protein change is the familiar one
    hits.sort(key=lambda t: 0 if t.get("canonical") else 1)
    score = None
    if hits:
        t = hits[0]
        aa = t.get("amino_acids", "")
        change = f"{aa[0]}{t.get('protein_start')}{aa[-1]}" if "/" in aa else None
        score = {"chrom": chrom, "pos": pos, "ref": ref, "alt": alt, "gene": t.get("gene_symbol"),
                 "transcript_id": t.get("transcript_id"), "protein_variant": change,
                 "am_pathogenicity": float(t["alphamissense"]["am_pathogenicity"]),
                 "am_class": t["alphamissense"]["am_class"],
                 "consequence": ",".join(t.get("consequence_terms", []))}
    return {"score": score, "consequence": entry.get("most_severe_consequence")}


def query_exact_variant(chrom: str, pos: int, ref: str, alt: str) -> dict | None:
    """The single AlphaMissense row for this exact variant, if it has one."""
    return vep_alphamissense(chrom, pos, ref, alt)["score"]


if __name__ == "__main__":
    # Real test: query a small window around rs1427407's region to confirm
    # the connection and column format both work as expected.
    print("Querying AlphaMissense for chr2:60,490,800-60,490,900 ...")
    rows = query_region("2", 60490800, 60490900)
    print(f"Got {len(rows)} scored variant(s) in this window")
    if rows:
        print("First row:", rows[0])
        print("\nIf 'am_pathogenicity' isn't the 9th field or column names look "
              "wrong, update COLUMNS at the top of this file to match.")
