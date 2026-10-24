"""
Warms backend/.cache for all 22 known variants (sequence, gnomAD, AlphaMissense) so that
clicking them in the app is instant and does not depend on Ensembl/gnomAD being up.
Run from backend/:  python prefetch_known.py     (safe to re-run; only missing items are fetched)
"""
import time
from variant_scorer import KNOWN_MODIFIERS
import app

fails = []
for rsid in KNOWN_MODIFIERS:
    for label, fn in (("full", app.get_full_known_variant), ("alphamissense", app.get_alphamissense_for_known)):
        try:
            r = fn(rsid)
            problem = r.get("note") if label == "full" and (r.get("note") and "failed" in r["note"]) else None
        except Exception as e:
            problem = repr(e)[:160]
        print(f"{rsid:12} {label:14} {'OK' if not problem else 'FAILED: ' + problem}")
        if problem:
            fails.append((rsid, label))
        time.sleep(0.25)  # stay well under Ensembl's rate limit
print(f"\n{len(fails)} failures" + (f": {fails}" if fails else " -- everything is cached"))
