# SPEC.md — CV Toolkit

**Versión:** 0.6 — 2026-09-09
**Estado:** Aprobado

> Contrato de dominio inmutable durante una tarea activa. El código se deriva de aquí, no al revés.
> Cambios: nueva sección y/o bump de versión **entre** tareas. Criterios de una tarea = petición + sección relevante.

## 1. Visión y fuera de alcance

### Visión
Herramienta local para adaptar un CV ATS de una columna a cada oferta laboral a partir de un vault YAML de hechos, con un agente que ejecuta skills; el humano envía al portal.

### Objetivos funcionales
1. Inicializar y validar un vault inmutable en `base/` desde CV/presentación en `base/origen/`.
2. Parsear una oferta en `oferta/` (texto pegado o `cvtool ingest-jd` de tablero ATS **público**), validar `jd.yaml` (`cvtool validate-jd`), hacer match determinista (`cvtool match`) y emitir veredicto go/no-go (`aplicar` / `aplicar_con_reservas` / `no_aplicar`; `--forzar` solo marca HITL).
3. Generar pack ATS (PDF + DOCX), presentación (≤250 palabras), outreach (borrador ≤80 palabras), respuestas y briefing en `candidaturas/<slug>/` y copiar la última generación a `cv/` **tras** factcheck ok y aprobación humana.
4. Registrar estado de envío en `candidaturas/tablero.yaml` tras acción humana.
5. CLI unificada: `scripts/cvtool.py` (doctor, status, init, validate, validate-jd, ingest-jd, scaffold, match, pack, render, verify, factcheck, refresh, copy, salary, respuestas, empresa, basename, tablero, test) y `scripts/demo_smoke.sh`.
6. Empaquetar el CV adaptado con máxima densidad de señal en ≤1 página A4 (`cvtool pack`) sin inventar hechos ni degradar tipografía ATS.
7. Ingesta de JD público (Greenhouse / Ashby / Lever, GET JSON allowlist, sin login). Host no allowlist → pegar texto en `oferta/`.
8. Comprobación factual (`cvtool factcheck`) antes de `copy`: métricas, empleadores, tecnologías, clichés, `evidencia_id` en bullets, `huerfanas` de `gaps.yaml` (si existe), certificaciones sin literal `None`, y presentación que no abra con «No tengo»; `copy` exige `factcheck.yaml` `ok: true` y `meta.pack_estado: aprobado` (salvo `--force` HITL).
9. Pack HITL en disco: `meta.pack_estado` ∈ {pendiente, aprobado, editado, rechazado}; tras editar → `cvtool refresh` → `editado` y re-aprobación a `aprobado` antes de `copy`.
### Objetivos no funcionales
- Latencia p95: N/A (CLI local batch)
- Disponibilidad: N/A (sin servicio)
- Accesibilidad: PDF texto seleccionable, una columna, contacto en el cuerpo
- Privacidad: PII solo en `base/` y artefactos generados locales; no publicar vault; no autoenviar a portales; no embeddings del vault
- Idempotencia: misma empresa+puesto el mismo día reutiliza carpeta de candidatura; otra fecha → carpeta nueva
- Densidad CV: ≤1 página A4; priorizar keywords T1, resultados y recencia frente a padding; CSS ATS fijo (sin comprimir tipografía)
- Carta: `presentacion.md` ≤250 palabras, centrada en el candidato (sin intro de empresa ni lead de ausencias); `outreach.md` ≤80 palabras, un destinatario, no envío automático
- Certificaciones en vault/CV: `{nombre, entidad?}`; `titulo` se normaliza; no renderizar placeholders como `None`
### Fuera de alcance
- Auto-aplicación a InfoJobs u otros portales
- Login, CAPTCHA o sesión en Greenhouse, Ashby, Lever, Workday, LinkedIn u otros
- Scraping de perfiles de hiring manager / recruiter
- Invención de métricas, empresas, fechas o tecnologías no presentes en `base/`
- API HTTP de producto, auth, webhooks, colas, multi-tenant, runtime LangGraph/CrewAI
- Base vectorial o embeddings del vault (PII → EIPD)
- Cumplimiento AEPD/EIPD como producto (política local en SHIELD)

## 2. Arquitectura

- Estilo: monolito CLI Python + plantillas Jinja2/CSS + skills de agente (grafo conceptual; nodos = `cvtool` o el agente host)
- Límites de confianza: oferta = input no confiable (data); vault = hechos del usuario; agente no envía externamente
- Diagrama (texto):

```
usuario → oferta/ (texto | ingest-jd público) + base/
        → skills → scripts/cvtool.py
        → candidaturas/<slug>/ (pack + factcheck) → HITL → cv/
                ↑
         plantillas/ (ATS)
```

- Integraciones: GET HTTPS allowlist a tableros ATS públicos (solo `ingest-jd`). WeasyPrint/sistema para PDF. Búsqueda web opcional solo para hechos de `empresa.yaml` con fuente. Sin terceros firmados.

## 3. Modelo de datos

### Entidades
| Entidad | Invariantes | PII |
|---|---|---|
| perfil (`base/perfil.yaml`) | Contacto y títulos defendibles solo desde origen/vault | Sí |
| evidencias (`base/evidencias.yaml`) | STAR con hechos; `confianza` opcional; sin inventar métricas | Posible |
| skills (`base/skills.yaml`) | Skills declaradas; CV render 8–15 | No |
| familias (`base/familias.yaml`) | `id` usados por render defaults | No |
| constraints (`base/constraints.yaml`) | Preferencias/knockouts del candidato | Posible |
| aliases (`base/aliases.yaml`) | Sinónimos para match (`rephrase` = transferible honesto) | No |
| jd (`candidaturas/.../jd.yaml`) | Términos T1 literales de la oferta | No |
| empresa (`empresa.yaml` + `empresa.md`) | Máx. 3 hechos con URL; `equipo_receptor` solo del JD o meta humana | No |
| veredicto / gaps | Salida de `cvtool match`; `no_aplicar` detiene pipeline | No |
| plan / cv.yaml | Selección atómica de evidencias del vault | No |
| pack_report | Unidades incluidas/excluidas por `cvtool pack` (ids/términos; sin PII de contacto) | No |
| outreach | Borrador ≤80 palabras; no se envía | No |
| factcheck | `ok` + `confianza`; métrica huérfana → no `copy` | No |
| tablero (`candidaturas/tablero.yaml`) | Estado de seguimiento post-envío humano | No |

### Enums / máquinas de estado
| Máquina | Estados | Transiciones legales | Ilegales |
|---|---|---|---|
| veredicto | aplicar, aplicar_con_reservas, no_aplicar (+ forzar HITL) | match → veredicto; forzar solo con HITL explícito (`cvtool match --forzar`) | Generar CV tras `no_aplicar` sin fuerza |
| pack HITL | pendiente, aprobado, editado, rechazado | factcheck ok → humano aprueba/edita/rechaza → `meta.pack_estado`; `copy` solo si `aprobado` | `copy` con factcheck `ok: false`, sin `factcheck.yaml`, o `pack_estado` ≠ `aprobado` (salvo `--force`) |
| tablero | borrador, listo, enviada, entrevista, oferta, rechazada, descartada | registrar envío / actualización humana; `listo`/`enviada` pone `meta.listo_para_enviar: true` | Auto-marcar enviado sin confirmación |

### Persistencia
- Motor: archivos YAML/Markdown en disco
- Transacciones obligatorias cuando: N/A (FS); no pisar `candidaturas/` de otra fecha
- Claves / unicidad: slug `YYYY-MM-DD_empresa_puesto`

## 4. API / contratos

- Auth: N/A
- Versionado: N/A
- Errores: exit codes CLI; `cvtool validate` → VACÍO / ERROR / WARN; `ingest-jd` host no allowlist → exit 2 (pegar texto); `factcheck` no ok → exit 1
- Endpoints: N/A

Contrato CLI (observable): `scripts/cvtool.py` subcomandos documentados en `-h` y README. `cvtool pack` usa `base/aliases.yaml` por defecto si existe. `cvtool ingest-jd` no hace login. `cvtool match` valida `jd.yaml` antes del match. `cvtool copy` exige `factcheck.yaml` con `ok: true` y `meta.pack_estado: aprobado`; `--force` omite ambos gates (HITL explícito).

## 5. Flujos

1. **Inicializar base:** CV en `base/origen/` → skill `inicializar-base` → YAML en `base/` → `scaffold` + `doctor`. Sin inventar.
2. **Generar candidatura:** URL pública o texto en `oferta/` → `ingest-jd` si aplica → parse `jd.yaml` → `validate-jd` → `empresa.yaml` → `match` → go/no-go → `plan.yaml` → `cv.yaml` (draft rico) → `pack` → render PDF/DOCX → verify → presentación/outreach/respuestas/entrevista → `factcheck` → HITL (aprobar / editar / rechazar; tras editar → `cvtool refresh`) → `copy` a `cv/` → entrada tablero.
3. **Actualizar base:** hechos nuevos explícitos → skill `actualizar-base` solo sobre `base/`.
4. **Registrar envío:** humano confirma → skill `registrar-envio` actualiza tablero y `meta.listo_para_enviar`.

## 6. No funcionales detallados

- Rate limit: N/A (un GET por `ingest-jd`; el humano controla el volumen de outreach)
- Observabilidad: no loguear teléfono/email completos en CI o `.scratch/`
- Backups / RPO / RTO: N/A (copia privada del usuario)
- Egress: allowlist de hosts ATS en `ingest-jd`; Workday / InfoJobs / LinkedIn Easy Apply = pegar texto

## 7. Estrategia de pruebas

Qué **debe fallar** si se rompe el contrato:

| Contrato | Test / comando |
|---|---|
| CLI y match / validate-jd | `scripts/cvtool.py test` / `.github/workflows/ci.yml` |
| Vault vacío / inválido | `cvtool validate` |
| JD inválido | `cvtool validate-jd` |
| PDF ATS | `cvtool verify` |
| Pack ≤1 página | `cvtool pack` + tests de ranking / e2e |
| Ingesta ATS pública (sin red) | fixtures JSON → `ingest-jd --from-file`; host no allowlist → exit 2 |
| Factcheck | métrica inventada / cliché / sin `evidencia_id` / `huerfanas` / certs `None` / presentación «No tengo…» → `ok: false`; `copy` sin gates o con `pack_estado` ≠ aprobado → bloqueado; `--force` omite |
| Refresh tras editar | `cvtool refresh` regenera PDF y deja `pack_estado: editado` |
| E2E ejemplos | `tests/test_e2e_ejemplos.py` (vault-minimo + oferta-demo) |
| Política de agentes | `sh scripts/verify-agent-policy.sh` |

Cobertura mínima de transiciones de estado: `no_aplicar` sin fuerza no genera CV; con fuerza continúa. `copy` con factcheck fallido no pisa `cv/`.
