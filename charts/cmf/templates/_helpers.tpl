{{/* vim: set filetype=mustache: */}}

{{- define "cmf.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "cmf.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if contains $name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "cmf.labels" -}}
app.kubernetes.io/name: {{ include "cmf.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "cmf.componentLabels" -}}
{{- include "cmf.labels" .ctx }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "cmf.image" -}}
{{- $registry := .ctx.Values.global.imageRegistry -}}
{{- $repo := .image.repository -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repo .image.tag -}}
{{- else -}}
{{- printf "%s:%s" $repo .image.tag -}}
{{- end -}}
{{- end -}}

{{- define "cmf.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets -}}
imagePullSecrets:
{{- toYaml . | nindent 2 }}
{{- end -}}
{{- end -}}

{{- define "cmf.serviceName" -}}
{{/* Plain component names ("server", "ui", "mcp", ...) to match the DNS names
     baked into the federcmf images' nginx.conf and MCP CMF_BASE_URL defaults
     (identical to docker-compose-server.yml service names). Services are
     namespace-scoped, so releases in separate namespaces don't collide. */}}
{{- .component -}}
{{- end -}}

{{- define "cmf.pvcName" -}}
{{/* PVCs keep the release-prefixed name to avoid collisions across releases
     in the same namespace (only the Service names must match the images). */}}
{{- printf "%s-%s" (include "cmf.fullname" .ctx) .name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/* Storage for a given PVC spec: renders volumes entry (persistentVolumeClaim or hostPath) */}}
{{- define "cmf.volumeSource" -}}
{{- $storage := .ctx.Values.storage -}}
{{- if eq $storage.mode "hostPath" -}}
hostPath:
  path: {{ printf "%s/%s" (trimSuffix "/" $storage.hostPath.base) .subpath }}
  type: DirectoryOrCreate
{{- else -}}
persistentVolumeClaim:
  claimName: {{ include "cmf.pvcName" (dict "ctx" .ctx "name" .name) }}
{{- end -}}
{{- end -}}
