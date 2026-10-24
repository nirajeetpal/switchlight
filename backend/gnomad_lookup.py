"""
Queries gnomAD's real, public GraphQL API for a variant's population allele
count/frequency -- this is the real data source for the PM2 (population
rarity) evidence line in variant_scorer.py.

No API key needed. This CANNOT be run from a network-restricted sandbox --
run it on your own machine.

NOTE: gnomAD's GraphQL schema has changed across dataset versions before.
If this script errors, check https://gnomad.broadinstitute.org/api for the
current schema before assuming the logic here is wrong.
"""

from resilient import cached_request

GNOMAD_API_URL = "https://gnomad.broadinstitute.org/api"

QUERY = """
query GetVariant($variantId: String!, $datasetId: DatasetId!) {
  variant(variantId: $variantId, dataset: $datasetId) {
    variant_id
    genome {
      ac
      an
      populations {
        id
        ac
        an
      }
    }
  }
}
"""


def fetch_allele_frequency(chrom: str, pos: int, ref: str, alt: str,
                            dataset_id: str = "gnomad_r4") -> dict:
    """
    variant_id format gnomAD expects: "chrom-pos-ref-alt", e.g. "2-60490908-T-C"
    """
    variant_id = f"{chrom}-{pos}-{ref}-{alt}"
    status, payload = cached_request(
        "POST", GNOMAD_API_URL, timeout=60,
        json_body={"query": QUERY, "variables": {"variantId": variant_id, "datasetId": dataset_id}},
    )
    if status != 200:
        raise RuntimeError(f"gnomAD returned HTTP {status}")

    if "errors" in payload:
        return {"found": False, "variant_id": variant_id, "errors": payload["errors"]}

    variant = payload.get("data", {}).get("variant")
    if not variant or not variant.get("genome"):
        # Not found = essentially absent from gnomAD -- itself a meaningful
        # result for PM2 (very rare / unobserved), not a failure.
        return {"found": False, "variant_id": variant_id, "ac": 0, "an": 0}

    genome = variant["genome"]
    return {
        "found": True,
        "variant_id": variant_id,
        "ac": genome["ac"],          # allele count (how many times the alt allele was seen)
        "an": genome["an"],          # allele number (total alleles sequenced at this position)
        "allele_freq": genome["ac"] / genome["an"] if genome["an"] else 0,
        "by_population": genome.get("populations", []),
    }


if __name__ == "__main__":
    # Real test case: rs334 at chr6:135,105,435, A>G
    result = fetch_allele_frequency("6", 135105435, "A", "G")
    import json
    print(json.dumps(result, indent=2))
