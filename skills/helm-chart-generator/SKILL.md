---
name: helm-chart-generator
description: Use when deploying a service to Kubernetes and you want a clean, reusable Helm chart instead of hand-written manifests. Generates a chart (Chart.yaml, values.yaml, templated Deployment, Service, Ingress, HPA, ConfigMap, Secret refs) with sane production defaults: resource requests/limits, liveness/readiness probes, rolling updates, pod security context (non-root), and per-environment values files. Trigger when the user asks to deploy to Kubernetes/EKS, create a Helm chart, write k8s manifests, or set up values for dev/staging/prod.
license: MIT
---

# Helm Chart Generator

Generate a Helm chart that a DevOps team would accept — or that a solo developer can ship directly.
Production defaults baked in; per-environment overrides via values files.

## When to use
- "Deploy this to Kubernetes/EKS" / "create a Helm chart"
- "Write k8s manifests" / "set up dev/staging/prod values"

## Chart layout
```
<service>/
├── Chart.yaml
├── values.yaml                 # defaults
├── values-staging.yaml         # overrides
├── values-prod.yaml            # overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    ├── hpa.yaml
    ├── configmap.yaml
    └── _helpers.tpl
```

## Production defaults (apply these)
- **Probes**: `livenessProbe` → `/healthz`, `readinessProbe` → `/readyz` with sensible delays/timeouts.
- **Resources**: set `requests` and `limits` for cpu/memory (don't ship without requests — it breaks scheduling/HPA).
- **Rolling updates**: `maxUnavailable: 0`, `maxSurge: 1` for zero-downtime; set `minReadySeconds`.
- **Security context**: `runAsNonRoot: true`, drop all capabilities, read-only root FS where possible.
- **Config**: non-secret config via ConfigMap; secrets via existing `Secret` refs / external-secrets —
  never inline secret values in the chart.
- **HPA**: optional autoscaler on CPU/custom metrics with min/max replicas.
- **Labels**: standard `app.kubernetes.io/*` labels via `_helpers.tpl`.
- **Image**: `repository` + `tag` (default to chart `appVersion`); `pullPolicy: IfNotPresent`.

## values.yaml shape (excerpt)
```yaml
image: { repository: ghcr.io/org/service, tag: "", pullPolicy: IfNotPresent }
replicaCount: 2
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits:   { cpu: 500m, memory: 512Mi }
probes:
  liveness:  { path: /healthz, initialDelaySeconds: 10 }
  readiness: { path: /readyz,  initialDelaySeconds: 5 }
ingress: { enabled: false, host: "", tls: false }
autoscaling: { enabled: false, minReplicas: 2, maxReplicas: 6, targetCPUUtilizationPercentage: 70 }
```

## Steps
1. Ask for service name, port, image repo, and whether it needs Ingress/HPA/secrets.
2. Generate the chart with the defaults above and three values files (default/staging/prod).
3. Validate with `helm lint` and `helm template` mentally; include README with
   `helm upgrade --install <name> ./<chart> -f values-prod.yaml`.

Pairs with `dockerfile-optimizer` and `ci-pipeline-generator` for an end-to-end ship path.
