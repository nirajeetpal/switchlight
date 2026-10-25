"""
Pulls real reference DNA sequence around a genomic position from Ensembl's
free REST API. Run locally -- not reachable from a network-restricted sandbox.
"""

from resilient import cached_request

WINDOW = 75  # bases on each side -- keeps the sequence strip readable


def fetch_flank(chrom: str, pos: int, window: int = WINDOW) -> dict:
    start, end = pos - window, pos + window
    url = f"https://rest.ensembl.org/sequence/region/human/{chrom}:{start}-{end}"
    try:
        status, text = cached_request("GET", url, headers={"Content-Type": "text/x-fasta"}, as_text=True, retries=2)
        if status != 200:
            raise RuntimeError(f"Ensembl sequence lookup returned HTTP {status}")
        sequence = "".join(text.strip().split("\n")[1:])
    except RuntimeError:
        # Ensembl is often overloaded; UCSC serves the same GRCh38 sequence (0-based start).
        status, data = cached_request(
            "GET", "https://api.genome.ucsc.edu/getData/sequence",
            params={"genome": "hg38", "chrom": f"chr{chrom}", "start": start - 1, "end": end}, retries=3)
        if status != 200 or not data.get("dna"):
            raise RuntimeError(f"Both Ensembl and UCSC sequence lookups failed (UCSC HTTP {status})")
        sequence = data["dna"].upper()
    return {
        "chrom": chrom, "variant_pos": pos,
        "window_start": start, "window_end": end,
        "sequence": sequence,
        "variant_index_in_sequence": pos - start,  # where the variant sits within the string
    }


if __name__ == "__main__":
    result = fetch_flank("2", 60490908)
    print(f"Fetched {len(result['sequence'])} real bases around chr2:60,490,908")
    print(result["sequence"])
