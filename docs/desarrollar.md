# Desarrollar el kit

Para quien cambia código, skills o contratos. Onboarding de candidaturas: [README](../README.md) y [usar.md](usar.md).

## Contratos

| Documento | Uso |
|---|---|
| [`SPEC.md`](../SPEC.md) | Contrato de dominio (criterios por sección) |
| [`SHIELD.md`](../SHIELD.md) | Hard stops, PII, no autoenviar |
| [`AGENTS.md`](../AGENTS.md) | Router de agente, fronteras, skills |
| [`docs/adr/`](adr/) | Decisiones de arquitectura |

Onboarding humano del producto: README → [usar.md](usar.md). No improvisar APIs desde memoria: SPEC sección → SHIELD si aplica → AGENTS.

## Skills de desarrollo (no candidaturas)

| Skill | Cuándo |
|---|---|
| `epic-workflow` | Feature / bug no trivial |
| `shield-security-gate` | Auth, webhooks, PII, dos stores, jobs de estado, admin, infra |

Candidaturas diarias usan solo: `inicializar-base`, `generar-candidatura`, `actualizar-base`, `registrar-envio`.

## Fronteras (resumen)

| Dominio | Paths | Fuera |
|---|---|---|
| vault | `base/` | Solo skills de init/update |
| candidatura | `oferta/`, `cv/`, `candidaturas/` | No editar `base/`; no pisar otra fecha |
| toolkit | `scripts/`, `tests/`, `plantillas/` | `.env`; mutar hooks/policy |
| docs | `docs/`, `README.md`, `SPEC.md`, `SHIELD.md`, `AGENTS.md` | Código de producto salvo citas |

Detalle: [`AGENTS.md`](../AGENTS.md). No mutar `.agents/hooks/` ni `.agents/policy/`.

## Tests y smoke

```bash
.venv/bin/python scripts/cvtool.py doctor
.venv/bin/python scripts/cvtool.py test
sh scripts/demo_smoke.sh
```

CI: [`.github/`](../.github/). Suites ruidosas: subagente `.agents/agents/test-runner.md`.

## CLI de desarrollo

```bash
.venv/bin/python scripts/cvtool.py scaffold
.venv/bin/python scripts/cvtool.py render --familia <id>
.venv/bin/python scripts/cvtool.py validate
.venv/bin/python scripts/cvtool.py validate-jd path/jd.yaml
.venv/bin/python scripts/cvtool.py match --jd path/jd.yaml --base base
.venv/bin/python scripts/cvtool.py ingest-jd --from-file tests/fixtures/ingest/greenhouse_job.json --adapter greenhouse --out-dir /tmp/oferta
.venv/bin/python scripts/cvtool.py factcheck --dir candidaturas/<slug> --base base
```

Resto: `cvtool -h`. Dependencias: `pip install -r requirements.txt` en venv; nueva dep = cambio explícito de `requirements.txt`.
