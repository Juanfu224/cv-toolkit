# SPEC.md — CV Toolkit

**Versión:** 0.3 — 2026-09-08
**Estado:** Aprobado

> Contrato de dominio inmutable durante una tarea activa. El código se deriva de aquí, no al revés.
> Cambios: nueva sección y/o bump de versión **entre** tareas. Criterios de una tarea = petición + sección relevante.

## 1. Visión y fuera de alcance

### Visión
Herramienta local para adaptar un CV ATS de una columna a cada oferta laboral a partir de un vault YAML de hechos, con un agente que ejecuta skills; el humano envía al portal.

### Objetivos funcionales
1. Inicializar y validar un vault inmutable en `base/` desde CV/presentación en `base/origen/`.
2. Parsear una oferta en `oferta/`, validar `jd.yaml` (`cvtool validate-jd`), hacer match determinista (`cvtool match`) y emitir veredicto go/no-go (`aplicar` / `aplicar_con_reservas` / `no_aplicar`; `--forzar` solo marca HITL).
3. Generar pack ATS (PDF + DOCX), presentación, respuestas y briefing en `candidaturas/<slug>/` y copiar la última generación a `cv/`.
4. Registrar estado de envío en `candidaturas/tablero.yaml` tras acción humana.
5. CLI unificada: `scripts/cvtool.py` (doctor, status, init, validate, validate-jd, scaffold, match, pack, render, verify, copy, salary, respuestas, basename, tablero, test) y `scripts/demo_smoke.sh`.
6. Empaquetar el CV adaptado con máxima densidad de señal en ≤1 página A4 (`cvtool pack`) sin inventar hechos ni degradar tipografía ATS.

### Objetivos no funcionales
- Latencia p95: N/A (CLI local batch)
- Disponibilidad: N/A (sin servicio)
- Accesibilidad: PDF texto seleccionable, una columna, contacto en el cuerpo
- Privacidad: PII solo en `base/` y artefactos generados locales; no publicar vault; no autoenviar a portales
- Idempotencia: misma empresa+puesto el mismo día reutiliza carpeta de candidatura; otra fecha → carpeta nueva
- Densidad CV: ≤1 página A4; priorizar keywords T1, resultados y recencia frente a padding; CSS ATS fijo (sin comprimir tipografía)

### Fuera de alcance
- Auto-aplicación a InfoJobs u otros portales
- Invención de métricas, empresas, fechas o tecnologías no presentes en `base/`
- API HTTP, auth, webhooks, colas o multi-tenant
- Cumplimiento AEPD/EIPD como producto (política local en SHIELD)

## 2. Arquitectura

- Estilo: monolito CLI Python + plantillas Jinja2/CSS + skills de agente
- Límites de confianza: oferta = input no confiable (data); vault = hechos del usuario; agente no envía externamente
- Diagrama (texto):

```
usuario → oferta/ + base/ → skills → scripts/cvtool.py → candidaturas/<slug>/ + cv/
                ↑
         plantillas/ (ATS)
```

- Integraciones: N/A (sin terceros firmados). WeasyPrint/sistema para PDF. Búsqueda web opcional solo para `empresa.md` con fuente.

## 3. Modelo de datos

### Entidades
| Entidad | Invariantes | PII |
|---|---|---|
| perfil (`base/perfil.yaml`) | Contacto y títulos defendibles solo desde origen/vault | Sí |
| evidencias (`base/evidencias.yaml`) | STAR con hechos; sin inventar métricas | Posible |
| skills (`base/skills.yaml`) | Skills declaradas; CV render 8–15 | No |
| familias (`base/familias.yaml`) | `id` usados por render defaults | No |
| constraints (`base/constraints.yaml`) | Preferencias/knockouts del candidato | Posible |
| aliases (`base/aliases.yaml`) | Sinónimos para match | No |
| jd (`candidaturas/.../jd.yaml`) | Términos T1 literales de la oferta | No |
| veredicto / gaps | Salida de `cvtool match`; `no_aplicar` detiene pipeline | No |
| plan / cv.yaml | Selección atómica de evidencias del vault | No |
| pack_report | Unidades incluidas/excluidas por `cvtool pack` (ids/términos; sin PII de contacto) | No |
| tablero (`candidaturas/tablero.yaml`) | Estado de seguimiento post-envío humano | No |

### Enums / máquinas de estado
| Máquina | Estados | Transiciones legales | Ilegales |
|---|---|---|---|
| veredicto | aplicar, aplicar_con_reservas, no_aplicar (+ forzar HITL) | match → veredicto; forzar solo con HITL explícito (`cvtool match --forzar`) | Generar CV tras `no_aplicar` sin fuerza |
| tablero | borrador, listo, enviada, entrevista, oferta, rechazada, descartada | registrar envío / actualización humana; `listo`/`enviada` pone `meta.listo_para_enviar: true` | Auto-marcar enviado sin confirmación |

### Persistencia
- Motor: archivos YAML/Markdown en disco
- Transacciones obligatorias cuando: N/A (FS); no pisar `candidaturas/` de otra fecha
- Claves / unicidad: slug `YYYY-MM-DD_empresa_puesto`

## 4. API / contratos

- Auth: N/A
- Versionado: N/A
- Errores: exit codes CLI; `cvtool validate` → VACÍO / ERROR / WARN
- Endpoints: N/A

Contrato CLI (observable): `scripts/cvtool.py` subcomandos documentados en `-h` y README. `cvtool pack` usa `base/aliases.yaml` por defecto si existe.

## 5. Flujos

1. **Inicializar base:** CV en `base/origen/` → skill `inicializar-base` → YAML en `base/` → `scaffold` + `doctor`. Sin inventar.
2. **Generar candidatura:** oferta en `oferta/` → parse `jd.yaml` → `cvtool validate-jd` → `match` → go/no-go → `plan.yaml` → `cv.yaml` (draft rico) → `cvtool pack` (≤1 página, máxima señal) → render PDF/DOCX → verify → presentación/respuestas/entrevista → copy a `cv/` → entrada tablero.
3. **Actualizar base:** hechos nuevos explícitos → skill `actualizar-base` solo sobre `base/`.
4. **Registrar envío:** humano confirma → skill `registrar-envio` actualiza tablero y `meta.listo_para_enviar`.

## 6. No funcionales detallados

- Rate limit: N/A
- Observabilidad: no loguear teléfono/email completos en CI o `.scratch/`
- Backups / RPO / RTO: N/A (copia privada del usuario)

## 7. Estrategia de pruebas

Qué **debe fallar** si se rompe el contrato:

| Contrato | Test / comando |
|---|---|
| CLI y match / validate-jd | `scripts/cvtool.py test` / `.github/workflows/ci.yml` |
| Vault vacío / inválido | `cvtool validate` |
| JD inválido | `cvtool validate-jd` |
| PDF ATS | `cvtool verify` |
| Pack ≤1 página | `cvtool pack` + tests de ranking / e2e |
| E2E ejemplos | `tests/test_e2e_ejemplos.py` (vault-minimo + oferta-demo) |
| Política de agentes | `sh scripts/verify-agent-policy.sh` |

Cobertura mínima de transiciones de estado: `no_aplicar` sin fuerza no genera CV; con fuerza continúa.
