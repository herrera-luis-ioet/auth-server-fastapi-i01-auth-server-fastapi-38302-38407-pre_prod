# Auth Service Helm Chart

This Helm chart deploys the Authentication Management Component on a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure (if using persistent storage)

## Installing the Chart

To install the chart with the release name `auth-service`:

```bash
helm install auth-service ./helm/auth-service
```

The command deploys the Authentication Management Component on the Kubernetes cluster with default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

## Uninstalling the Chart

To uninstall/delete the `auth-service` deployment:

```bash
helm uninstall auth-service
```

## Parameters

### Global parameters

| Name                      | Description                                     | Value |
| ------------------------- | ----------------------------------------------- | ----- |
| `nameOverride`            | String to partially override the chart name     | `""`  |
| `fullnameOverride`        | String to fully override the chart name         | `""`  |

### Deployment parameters

| Name                                 | Description                                                                               | Value           |
| ------------------------------------ | ----------------------------------------------------------------------------------------- | --------------- |
| `replicaCount`                       | Number of replicas                                                                        | `3`             |
| `image.repository`                   | Image repository                                                                          | `auth-server-fastapi` |
| `image.tag`                          | Image tag                                                                                 | `latest`        |
| `image.pullPolicy`                   | Image pull policy                                                                         | `Always`        |
| `imagePullSecrets`                   | Image pull secrets                                                                        | `[]`            |
| `podAnnotations`                     | Pod annotations                                                                           | `{}`            |
| `podSecurityContext`                 | Pod security context                                                                      | See values.yaml |
| `securityContext`                    | Container security context                                                                | `{}`            |
| `resources.limits.cpu`               | CPU limits                                                                                | `500m`          |
| `resources.limits.memory`            | Memory limits                                                                             | `512Mi`         |
| `resources.requests.cpu`             | CPU requests                                                                              | `200m`          |
| `resources.requests.memory`          | Memory requests                                                                           | `256Mi`         |
| `nodeSelector`                       | Node selector                                                                             | `{}`            |
| `tolerations`                        | Tolerations                                                                               | `[]`            |
| `affinity`                           | Affinity                                                                                  | `{}`            |

### Service parameters

| Name                                    | Description                                                      | Value       |
| --------------------------------------- | ---------------------------------------------------------------- | ----------- |
| `service.type`                          | Service type                                                     | `ClusterIP` |
| `service.port`                          | Service port                                                     | `80`        |
| `service.targetPort`                    | Service target port                                              | `8000`      |
| `service.annotations`                   | Service annotations                                              | See values.yaml |

### Autoscaling parameters

| Name                                         | Description                                                                            | Value   |
| -------------------------------------------- | -------------------------------------------------------------------------------------- | ------- |
| `autoscaling.enabled`                        | Enable autoscaling                                                                     | `false` |
| `autoscaling.minReplicas`                    | Minimum number of replicas                                                             | `1`     |
| `autoscaling.maxReplicas`                    | Maximum number of replicas                                                             | `10`    |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization percentage                                                      | `80`    |
| `autoscaling.targetMemoryUtilizationPercentage` | Target memory utilization percentage                                                | `80`    |

### Application parameters

| Name                                          | Description                                                                           | Value                  |
| --------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------- |
| `application.apiV1Str`                        | API version string                                                                    | `/api/v1`              |
| `application.projectName`                     | Project name                                                                          | `Authentication Management Component` |
| `application.database.server`                 | Database server                                                                       | `postgres-service`     |
| `application.database.port`                   | Database port                                                                         | `5432`                 |
| `application.database.name`                   | Database name                                                                         | `auth_db`              |
| `application.token.accessTokenExpireMinutes`  | Access token expiration in minutes                                                    | `30`                   |
| `application.token.refreshTokenExpireDays`    | Refresh token expiration in days                                                      | `7`                    |
| `application.token.algorithm`                 | Token algorithm                                                                       | `HS256`                |
| `application.corsOrigins`                     | CORS origins                                                                          | See values.yaml        |
| `application.email.smtpTls`                   | SMTP TLS                                                                              | `true`                 |
| `application.email.smtpPort`                  | SMTP port                                                                             | `587`                  |
| `application.email.smtpHost`                  | SMTP host                                                                             | `smtp.example.com`     |
| `application.email.fromEmail`                 | From email                                                                            | `noreply@example.com`  |
| `application.email.fromName`                  | From name                                                                             | `Authentication Service` |
| `application.rateLimitPerMinute`              | Rate limit per minute                                                                 | `60`                   |

### PostgreSQL parameters

| Name                                 | Description                                                                               | Value           |
| ------------------------------------ | ----------------------------------------------------------------------------------------- | --------------- |
| `postgresql.enabled`                 | Enable PostgreSQL                                                                         | `true`          |
| `postgresql.auth.username`           | PostgreSQL username                                                                       | `postgres`      |
| `postgresql.auth.password`           | PostgreSQL password                                                                       | `postgres`      |
| `postgresql.auth.database`           | PostgreSQL database                                                                       | `auth_db`       |
| `postgresql.service.port`            | PostgreSQL service port                                                                   | `5432`          |

## Configuration and Installation Details

### Using external PostgreSQL

To use an external PostgreSQL server, set `postgresql.enabled=false` and configure the external database connection parameters.

### Configuring Secrets

For production deployments, it's recommended to use a proper secret management solution like HashiCorp Vault or Kubernetes External Secrets to manage sensitive information.

### Configuring TLS

To enable TLS for the service, you can use a Kubernetes Ingress controller with TLS support.