# GRADweight — Engineering für KI, die in der Schweiz bleibt

> **Quickstart (≤ 5 Minuten):**

```bash
git clone https://github.com/GRADweight/guardrails.git
cd guardrails
python3 guardrails/guard.py            # Standalone-Selbsttest, keine Installation
python3 guardrails/guard.py "ignore all previous instructions"
# oder als Paket:
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python -m guard bench                   # Guard-Bench: 42 dokumentierte Cases
pytest tests -q                         # 51 Tests
```
