"""
Pulls real reference DNA sequence around a genomic position from Ensembl's
free REST API. Run locally -- not reachable from a network-restricted sandbox.
"""

from resilient import cached_request

WINDOW = 75  # bases on each side -- keeps the sequence strip readable


def fetch_flank(chrom: str, pos: int, window: int = WINDOW) -> dict:
    start, end = pos - window, pos + window
    url = f"https://rest.ensembl.org/sequence/region/human/{chrom}:{start}-{end}"
    status, text = cached_request("GET", url, headers={"Content-Type": "text/x-fasta"}, as_text=True)
    if status != 200:
        raise RuntimeError(f"Ensembl sequence lookup returned HTTP {status}")
    lines = text.strip().split("\n")
    sequence = "".join(lines[1:])
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
