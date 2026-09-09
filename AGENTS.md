# AGENTS.md — Orquestación

**Gobernanza:** `SHIELD.md` (prosa; el host enforcea). **Contrato:** `SPEC.md`.
**Compatibilidad:** `CLAUDE.md` → `@AGENTS.md`. No `.cursorrules`.
**Contexto (AAIF):** chat explícito > este archivo más cercano > raíz. En conflicto, nearest wins; varios runtimes concatenan root→cwd.
**Enforcement:** política administrada / OS / sandbox > hooks (Cursor: `failClosed` por hook; Claude: exit 2, crash = fail-open) > Markdown.
El hook es un punto de decisión, no una barrera dura por sí solo. Cloud ≠ local.
Si este archivo y el chat chocan en estilo o comandos de test, gana el chat. Hard Stops los enforcea el host, no este Markdown.
Si el chat pide un Hard Stop cubierto por hooks/sandbox: STOP.
No mutar `.agents/hooks/` ni `.agents/policy/`.

Raíz del producto: carpeta con `base/` y `oferta/`. Python: `.venv/bin/python` si existe. Usuario primero: `cvtool doctor`. Skills ejecutan el pipeline; no improvisar PDFs.
Onboarding humano: `README.md` → `docs/usar.md`. Desarrollo del kit: `docs/desarrollar.md`.

## Skills de dominio

| Frase del usuario | Skill |
|---|---|
| inicializa mi base | `.agents/skills/inicializar-base/SKILL.md` |
| genera candidatura | `.agents/skills/generar-candidatura/SKILL.md` |
| actualizar base | `.agents/skills/actualizar-base/SKILL.md` |
| registrar envío | `.agents/skills/registrar-envio/SKILL.md` |

CLI: `scripts/cvtool.py` — doctor, status, init, validate, validate-jd, ingest-jd, scaffold, match (`--forzar`), pack, render, verify, factcheck, refresh, copy (`--force` omite gates), salary, respuestas, empresa, basename, tablero, test.
Schemas: `.agents/skills/generar-candidatura/schemas.md`.

## Subagentes

| Uso | Path |
|---|---|
| Suites / builds ruidosos | `.agents/agents/test-runner.md` |
| Recorte de payloads MCP | `.agents/agents/mcp-analyzer.md` |

## Arranque (antes de escribir código)

1. Clasificar dominio (paths + petición).
2. Leer skill `.agents/skills/epic-workflow/SKILL.md` salvo tweak < 5 líneas o single-file sin impacto transversal.
3. Criterios = petición + **sección** de `SPEC.md` (nunca el archivo completo por defecto).
4. Si auth, webhooks, PII, dos stores/agregados, jobs de estado, admin, infra → skill `shield-security-gate` + sección `SHIELD.md`. Candidaturas y vault tocan PII → SHIELD §1.1 / §5 / §7.
5. Skill de dominio on-demand (tabla arriba). MCP/docs versionadas antes de APIs.
6. Plan Mode si multi-archivo o decisión arquitectónica. DAG: `.scratch/dag.json` (gitignored) si no hay Spec Kit.

Prohibido: vibe coding; transcripts/dumps como SoT; interpolar estado de sesión en este archivo.

## Roles

| Rol | Tools | Write |
|---|---|---|
| Planificador | Read, Grep, Glob, shell read-only | Solo `SPEC.md` entre tareas, con HITL |
| Ejecutor | Subset por nodo DAG | Paths de la tabla de fronteras |

Un rol por turno. Ejecutor no toma decisiones de arquitectura.

## Fronteras

| Dominio | Paths | Fuera |
|---|---|---|
| vault | `base/` | Solo skills `inicializar-base` / `actualizar-base` |
| candidatura | `oferta/`, `cv/`, `candidaturas/` | No editar `base/`; no pisar otra fecha |
| toolkit | `scripts/`, `tests/`, `plantillas/` | `.env`; mutar hooks/policy |
| docs | `docs/`, `README.md`, `SPEC.md`, `SHIELD.md`, `AGENTS.md` | Código de producto salvo citas |

## Docs

Prioridad: SPEC sección → SHIELD si aplica → este archivo → docs del lockfile → MCP versionado → web oficial.
Prohibido: APIs desde memoria de entrenamiento.

## Tokens

`/clear` entre dominios. `/compact` dirigido. Subagentes para tests/builds/MCP ruidoso. MCP idle off.

## Git

No `commit` sin instrucción explícita. Force-push, `reset --hard` y push a `main`/`master`/`production`: deny. Push a feature: `ask` (standard) o deny (strict/ci). No `--no-verify`.

## Dependencias

Locked install (`pip install -r requirements.txt` en venv controlado): allow en sandbox. Nueva dep / cambio de requirements: ask (standard) o deny (strict/ci).

## Confirmación

Tests del `acceptance[]` verdes. Formatter. Purge dumps de `.scratch/`.
