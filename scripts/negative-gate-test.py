#!/usr/bin/env python3
"""Negativ-Test: belegt, dass der Regression-Gate eintreigt, wenn ein FP entsteht.

Fügt temporär eine zu-brede Signatur ('ratgeber' — trifft legit-02 'onboarding-Ratgebers')
in INJECTION_SIGNATURES + INJECTION_CATEGORIES ein, prüft, dass der Gate FP=1 erkennt
und Exit(1) liefert, rückt dann zurück. Beweist, dass das Gate NICHT permanent grün ist."""
import sys, pathlib, subprocess, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
core = pathlib.Path("guard/core.py").resolve()
orig = core.read_text()
inject_sig = '    "ratgeber",   # NEGATIV-TEST FP\n'
inject_cat = '    "jailbreak",  # NEGATIV-TEST\n'
# Anchor: die v1.4-Schlosszeile in beiden Listen (eindeutig)
sig_anchor = '    "unfiltered mode",        # Jailbreak\n)\n'
cat_anchor = '    "jailbreak",          # "unfiltered mode"\n)\n'
new = orig
assert sig_anchor in new, "sig anchor missing\n---\n" + "\n".join(l for l in new.splitlines() if "unfiltered" in l)
assert cat_anchor in new, "cat anchor missing\n---\n" + "\n".join(l for l in new.splitlines() if "unfiltered mode" in l)
new = new.replace(sig_anchor, '    "unfiltered mode",        # Jailbreak\n' + inject_sig + ')\n', 1)
new = new.replace(cat_anchor, '    "jailbreak",          # "unfiltered mode"\n' + inject_cat + ')\n', 1)
core.write_text(new)
try:
    r = subprocess.run([sys.executable, "-m", "guard", "bench", "--metrics"],
                       capture_output=True, text=True)
    print("STDOUT:\n", r.stdout)
    print("STDERR:\n", r.stderr[-2000:] if r.stderr else "(none)")
    print("EXIT:", r.returncode)
    # Erwartung: Exit 1 — der Bench/Report blockt, sobald ein Fall ROT ist
    # (ob als Regression oder als fehlerhafter Bench-Case: jeder FP = block).
    success = r.returncode == 1 and "ROT" in r.stdout
    print("=== NEGATIV-TEST", "PASS (Gate hat den FP gefangen)" if success else "FAIL ===")
    sys.exit(0 if success else 2)
finally:
    core.write_text(orig)  # revert
