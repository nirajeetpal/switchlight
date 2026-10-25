"""
Two genuinely different scoring paths, kept deliberately separate:

1. KNOWN HbF MODIFIER VARIANTS (score_known_modifier)
   These affect HOW MUCH fetal hemoglobin a person makes -- a quantitative
   trait, not a disease/no-disease question. Real published effect sizes,
   not a model.

2. NOVEL VARIANT FUNCTIONAL IMPACT (score_novel_variant)
   For a variant with NO published effect size: real ACMG/AMP PP3/BP4
   (computational evidence, calibrated AlphaMissense thresholds) + PM2
   (population rarity). Answers a different question: "does this variant
   plausibly disrupt protein function at all."

Source for known modifiers: Shende N, Athalye S, Kamath S, Rani P,
Madkaikar M, Banerjee A, Khargekar N. "Global genetic modifiers of fetal
hemoglobin in sickle cell disease: Systematic review and meta-analysis."
iScience 2026;29(9):116997. PMID: 42657270, PMCID: PMC13508651.

Source for PP3/BP4 thresholds: ClinGen SVI AlphaMissense calibration,
2024-2025. Source for point combination: Tavtigian et al. 2018 (Bayesian
ACMG framework, approximate implementation here).
"""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class KnownModifier:
    rsid: str
    gene: str
    location: str
    effect_allele: Optional[str]
    effect_direction: str
    is_meta_analyzed: bool
    pooled_md: Optional[float]
    ci_95: Optional[tuple]
    p_value: Optional[float]
    i_squared: Optional[float]
    n_studies: Optional[int]
    note: Optional[str] = None
    chrom: Optional[str] = None             # GRCh38, filled in from GRCH38_ALLELES below
    pos: Optional[int] = None
    ref_allele: Optional[str] = None
    alt_alleles: Optional[tuple] = None
    effect_is_reference: Optional[bool] = None
    effect_allele_source: str = "Shende 2026, Table 1"
    reported_populations: Optional[tuple] = None
    ancestry_categories: Optional[tuple] = None


SOURCE_CITATION = "Shende et al. 2026, iScience 29(9):116997, PMID 42657270"

KNOWN_MODIFIERS = {
    # ---- BCL11A ----
    "rs1427407": KnownModifier(
        "rs1427407", "BCL11A", "intronic erythroid enhancer", "T", "increases",
        True, 1.1, (0.287, 1.914), 0.008, 90.7, 9),
    "rs4671393": KnownModifier(
        "rs4671393", "BCL11A", "intronic erythroid enhancer", "A", "increases",
        True, 1.13, (0.241, 2.014), 0.012, 95.2, 8),
    "rs11886868": KnownModifier(
        "rs11886868", "BCL11A", "intronic erythroid enhancer", "C", "increases",
        True, 1.229, (0.294, 2.165), 0.01, 87.9, 5,
        note="Effect allele C is INFERRED, not taken from the source paper (its "
             "Table 1 leaves it blank): C is the minor allele in African and European "
             "reference panels, and in the Brazilian SCA cohorts the minor/variant "
             "alleles at this locus go with higher Hb F. Confirm against the primary "
             "studies before clinical-style use. Associated with Hb F elevation in some ancestral backgrounds and "
             "suppression in others -- population-specific LD structure."),
    "rs766432": KnownModifier(
        "rs766432", "BCL11A", "intronic erythroid enhancer (+55kb)", "C", "increases",
        False, None, None, None, None, 5),
    "rs7557939": KnownModifier(
        "rs7557939", "BCL11A", "intronic erythroid enhancer", "G", "increases",
        False, None, None, None, None, 3),
    "rs7569946": KnownModifier(
        "rs7569946", "BCL11A", "intronic erythroid enhancer", "A", "increases",
        False, None, None, None, None, 1, note="Kuwait cohort only."),
    "rs6545816": KnownModifier(
        "rs6545816", "BCL11A", "intronic erythroid enhancer", "C", "decreases",
        False, None, None, None, None, 1, note="Nigeria cohort only."),
    "rs7606173": KnownModifier(
        "rs7606173", "BCL11A", "intronic erythroid enhancer (+62kb)", "G", "decreases",
        False, None, None, None, None, 4),
    "rs10195871": KnownModifier(
        "rs10195871", "BCL11A", "intronic erythroid enhancer", "G", "decreases",
        False, None, None, None, None, 1, note="Kuwait cohort only."),
    "rs6706648": KnownModifier(
        "rs6706648", "BCL11A", "intronic erythroid enhancer", "T", "decreases",
        False, None, None, None, None, 2),

    # ---- HBS1L-MYB (HMIP) ----
    "rs9399137": KnownModifier(
        "rs9399137", "HBS1L-MYB", "intergenic enhancer (HMIP-2A)", "C", "increases",
        True, 0.832, (-0.096, 1.759), 0.079, 86.7, 6,
        note="Most widely replicated HMIP variant (19 studies total) but pooled "
             "estimate did not reach significance at 95% -- directionally "
             "consistent, not statistically confirmed."),
    "rs4895441": KnownModifier(
        "rs4895441", "HBS1L-MYB", "intergenic enhancer (HMIP-2B)", "G", "increases",
        True, 0.356, (0.181, 0.532), 0.0001, 49.4, 6,
        note="Lowest heterogeneity in the whole study (I2=49.4%) -- most cross-"
             "population reproducible signal. Maps to the +62kb enhancer region "
             "directly targeted by CRISPR-Cas9 therapy."),
    "rs28384513": KnownModifier(
        "rs28384513", "HBS1L-MYB", "intergenic enhancer (HMIP-1)", "C", "decreases",
        True, -0.0904, (-0.144, -0.037), 0.001, 0.0, 5,
        note="DATA DISCREPANCY: source paper's Table 1 lists 'increase', but its "
             "meta-analysis/discussion report a significant NEGATIVE pooled MD "
             "and call it 'Hb F-suppressing'. This entry trusts the quantitative "
             "result. Also the single most homogeneous result in the study (I2=0%)."),
    "rs9402686": KnownModifier(
        "rs9402686", "HBS1L-MYB", "intergenic enhancer (HMIP-2B)", "A", "increases",
        False, None, None, None, None, 9),
    "rs66650371": KnownModifier(
        "rs66650371", "HBS1L-MYB", "intergenic enhancer (HMIP-2A)", "TA", "increases",
        False, None, None, None, None, 4),
    "rs35786788": KnownModifier(
        "rs35786788", "HBS1L-MYB", "intergenic enhancer (HMIP)", "A", "increases",
        False, None, None, None, None, 3),
    "rs35959442": KnownModifier(
        "rs35959442", "HBS1L-MYB", "intergenic enhancer (HMIP)", "G", "increases",
        False, None, None, None, None, 1, note="Kuwait cohort only."),

    # ---- HBG2 / XmnI ----
    "rs7482144": KnownModifier(
        "rs7482144", "HBG2", "promoter, -158 C>T (XmnI polymorphism)", "A", "increases",
        True, 2.855, (0.626, 5.083), 0.012, 96.0, 13,
        note="Effect allele A is on the forward (GRCh38) strand; the source paper "
             "writes it 'A/T' because HBG2 is read on the opposite strand, where "
             "this is the -158 C>T change. Strongly haplotype-dependent: positive in Indian/Arab-Indian "
             "populations, near-null/negative in African/Middle Eastern cohorts "
             "with Bantu haplotype."),

    # ---- Secondary loci ----
    "rs2071746": KnownModifier(
        "rs2071746", "HMOX1", "promoter/intronic, -413 A>T", "T", "increases",
        True, 4.453, (0.935, 7.971), 0.013, 97.8, 6,
        note="Largest pooled effect of any variant studied, but also highest "
             "heterogeneity (I2=97.8%) -- source paper cautions against treating "
             "this as a generalizable modifier."),
    "rs4527238": KnownModifier(
        "rs4527238", "ANTXR1", "intronic", "C", "decreases",
        False, None, None, None, None, 1,
        note="Saudi Arabia cohort only. The source paper's text calls this variant "
             "Hb F-increasing, but its Table 1 and the original study (Al-Ali 2018, "
             "Acta Haematol 140:55) agree: the CC genotype goes with LOW Hb F, so "
             "'decreases' is correct here."),
    "rs35685045": KnownModifier(
        "rs35685045", "ANTXR1", "intronic", "T", "decreases",
        False, None, None, None, None, 1, note="Saudi Arabia cohort only."),
    "rs11549465": KnownModifier(
        "rs11549465", "HIF-1α", "coding (C1772T)", "T", "increases",
        False, None, None, None, None, 1,
        note="Saudi Arabia cohort only; a coding variant, mechanistically "
             "different from the regulatory variants above."),
}

# GRCh38 forward-strand coordinates and alleles for each variant (from Ensembl/dbSNP,
# cross-checked in app.py's CONFIRMED_COORDINATES). The effect_allele above comes from
# the source paper's Table 1 (two inferred entries are marked in
# effect_allele_source); every one of them is one of these alleles on this same
# strand, so no strand flip is needed. The first allele listed for an indel is the
# reference and the others are the observed alternatives.
GRCH38_ALLELES = {
    "rs1427407": ("2", 60490908, "T", ('C', 'G')),
    "rs4671393": ("2", 60493816, "A", ('C', 'G', 'T')),
    "rs11886868": ("2", 60493111, "C", ('T',)),
    "rs766432": ("2", 60492835, "C", ('A', 'G', 'T')),
    "rs7557939": ("2", 60494212, "G", ('A',)),
    "rs7569946": ("2", 60460824, "A", ('C', 'G', 'T')),
    "rs6545816": ("2", 60487726, "A", ('C', 'G', 'T')),
    "rs7606173": ("2", 60498316, "G", ('A', 'C', 'T')),
    "rs10195871": ("2", 60493454, "A", ('G', 'T')),
    "rs6706648": ("2", 60494905, "C", ('G', 'T')),
    "rs9399137": ("6", 135097880, "T", ('C',)),
    "rs4895441": ("6", 135105435, "A", ('G',)),
    "rs28384513": ("6", 135055071, "T", ('A', 'C', 'G')),
    "rs9402686": ("6", 135106679, "G", ('A',)),
    "rs66650371": ("6", 135097495, "TACTA", ('TA', 'TACTACTA')),
    "rs35786788": ("6", 135097904, "G", ('A',)),
    "rs35959442": ("6", 135103041, "C", ('G', 'T')),
    "rs7482144": ("11", 5254939, "G", ('A',)),
    "rs2071746": ("22", 35380679, "A", ('T',)),
    "rs4527238": ("2", 69092659, "T", ('C',)),
    "rs35685045": ("2", 69098684, "C", ('A', 'G', 'T')),
    "rs11549465": ("14", 61740839, "C", ('T',)),
}
EFFECT_ALLELE_SOURCE_OVERRIDES = {
    "rs7482144": "Shende 2026 Table 1 ('A/T'), translated to the forward strand",
    "rs11886868": "Inferred (blank in Shende 2026 Table 1): minor allele in AFR/EUR panels",
    "rs66650371": "Inferred from Table 1's 'Del': TA is the 3-bp deletion allele (CTA removed)",
}
for _rsid, (_chrom, _pos, _ref, _alts) in GRCH38_ALLELES.items():
    _m = KNOWN_MODIFIERS[_rsid]
    _m.chrom, _m.pos, _m.ref_allele, _m.alt_alleles = _chrom, _pos, _ref, _alts
    # True when the Hb F effect is carried by the reference letter itself, so a
    # genotype check must count REF copies rather than ALT copies.
    _m.effect_allele_source = EFFECT_ALLELE_SOURCE_OVERRIDES.get(_rsid, _m.effect_allele_source)
    _m.effect_is_reference = (_m.effect_allele == _ref) if _m.effect_allele in {_ref, *_alts} else None

# Populations in which each variant was reported and their standardized ancestry
# categories, from Table 1 of the source paper (Shende et al. 2026). AFR = African,
# AMR = admixed American, EUR = European, SAS = South Asian, MID = Middle Eastern.
REPORTED_POPULATIONS = {
    "rs1427407": (('Angola', 'Brazil', 'Cameroon', 'India', 'Iraq', 'Kuwait', 'Nigeria', 'Saudi Arabia', 'Tanzania', 'USA'), ('AFR', 'AMR', 'SAS', 'MID')),
    "rs4671393": (('Angola', 'Brazil', 'France', 'Mauritania', 'Pakistan', 'Portugal', 'Saudi Arabia', 'Spain', 'Tanzania', 'Tunisia', 'USA'), ('AFR', 'AMR', 'EUR', 'SAS', 'MID')),
    "rs11886868": (('Angola', 'Brazil', 'Egypt', 'France', 'India', 'Mauritania', 'Mexico', 'Portugal', 'Saudi Arabia', 'Tanzania', 'Tunisia', 'USA'), ('AFR', 'AMR', 'EUR', 'SAS', 'MID')),
    "rs766432": (('Brazil', 'Saudi Arabia', 'USA'), ('AMR', 'MID', 'AFR (African American)')),
    "rs7557939": (('Angola', 'Brazil', 'USA'), ('AFR', 'AMR')),
    "rs7569946": (('Kuwait',), ('MID',)),
    "rs6545816": (('Nigeria',), ('AFR',)),
    "rs7606173": (('Cameroon', 'Kuwait', 'USA'), ('AFR', 'MID')),
    "rs10195871": (('Kuwait',), ('MID',)),
    "rs6706648": (('Nigeria', 'USA'), ('AFR',)),
    "rs9399137": (('Brazil', 'Cameroon', 'France', 'India', 'Iraq', 'Kuwait', 'Nigeria', 'Saudi Arabia', 'Tanzania', 'USA', 'Jamaica'), ('AFR', 'AMR', 'EUR', 'SAS', 'MID')),
    "rs4895441": (('Brazil', 'France', 'Morocco', 'Saudi Arabia', 'Tanzania', 'USA', 'Jamaica'), ('AFR', 'AMR', 'EUR', 'MID')),
    "rs28384513": (('Brazil', 'France', 'Iraq', 'Morocco', 'Saudi Arabia', 'Tanzania', 'USA'), ('AFR', 'AMR', 'EUR', 'MID')),
    "rs9402686": (('Brazil', 'Morocco', 'Nigeria', 'Saudi Arabia', 'Tanzania', 'USA', 'Jamaica'), ('AFR', 'AMR', 'MID')),
    "rs66650371": (('Angola', 'Kuwait', 'Nigeria', 'Tanzania'), ('AFR', 'MID')),
    "rs35786788": (('Brazil', 'Kuwait', 'Tanzania'), ('AMR', 'MID', 'AFR')),
    "rs35959442": (('Kuwait',), ('MID',)),
    "rs7482144": (('Angola', 'Brazil', 'Egypt', 'France', 'India', 'Iraq', 'Kuwait', 'Nigeria', 'Portugal', 'Saudi Arabia', 'Spain', 'Tanzania', 'USA', 'Morocco'), ('AFR', 'AMR', 'EUR', 'SAS', 'MID')),
    "rs2071746": (('Brazil', 'Egypt', 'India', 'Iran'), ('AMR', 'MID', 'SAS')),
    "rs4527238": (('Saudi Arabia',), ('MID',)),
    "rs35685045": (('Saudi Arabia',), ('MID',)),
    "rs11549465": (('Saudi Arabia',), ('MID',)),
}
for _rsid, (_pops, _anc) in REPORTED_POPULATIONS.items():
    KNOWN_MODIFIERS[_rsid].reported_populations = _pops
    KNOWN_MODIFIERS[_rsid].ancestry_categories = _anc


def score_known_modifier(rsid: str) -> Optional[dict]:
    modifier = KNOWN_MODIFIERS.get(rsid)
    return asdict(modifier) if modifier else None


def list_known_modifiers_by_gene(gene: str) -> list:
    return [asdict(v) for v in KNOWN_MODIFIERS.values() if v.gene == gene]


# ---------------------------------------------------------------------------
# PATH 2: Novel variant -- ACMG/AMP PP3/BP4 (computational) + PM2 (rarity)
# ---------------------------------------------------------------------------

AM_THRESHOLDS = [
    (0.990, 1.000, "PP3", "Strong", 4),
    (0.972, 0.989, "PP3", "Moderate-Strong", 3),
    (0.906, 0.971, "PP3", "Moderate", 2),
    (0.792, 0.905, "PP3", "Supporting", 1),
    (0.170, 0.791, None, "Indeterminate", 0),
    (0.071, 0.169, "BP4", "Supporting", -1),
    (0.000, 0.070, "BP4", "Strong", -4),
]


def classify_computational_evidence(am_score: float) -> dict:
    for low, high, code, strength, points in AM_THRESHOLDS:
        if low <= am_score <= high:
            return {"raw_score": am_score, "acmg_code": code,
                    "strength": strength, "points": points}
    raise ValueError(f"Score {am_score} out of expected 0-1 range")


def classify_population_rarity(allele_count: int, total_alleles: int = 800_000) -> dict:
    allele_freq = allele_count / total_alleles if total_alleles else 0
    if allele_freq < 0.0001:
        return {"acmg_code": "PM2", "strength": "Supporting", "points": 1,
                "allele_count": allele_count, "allele_freq": allele_freq}
    return {"acmg_code": None, "strength": "Not applicable", "points": 0,
            "allele_count": allele_count, "allele_freq": allele_freq}


def classify_overall(pp3bp4_points: int, pm2_points: int) -> dict:
    total = pp3bp4_points + pm2_points
    if total >= 10:
        label = "Pathogenic"
    elif total >= 6:
        label = "Likely Pathogenic"
    elif total >= 0:
        label = "Uncertain Significance (VUS)"
    elif total >= -6:
        label = "Likely Benign"
    else:
        label = "Benign"
    return {"total_points": total, "classification": label,
            "caveat": "Approximate demonstration only -- real classification "
                      "requires additional evidence types this tool doesn't have."}


def score_novel_variant(am_score: float, allele_count: int, total_alleles: int = 800_000) -> dict:
    comp = classify_computational_evidence(am_score)
    rarity = classify_population_rarity(allele_count, total_alleles)
    overall = classify_overall(comp["points"], rarity["points"])
    return {"computational_evidence": comp, "population_evidence": rarity,
            "overall": overall}
