{{- define "document-extraction.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "document-extraction.fullname" -}}
{{- default .Release.Name .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "document-extraction.labels" -}}
app.kubernetes.io/name: {{ include "document-extraction.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end -}}

{{- define "document-extraction.selectorLabels" -}}
app.kubernetes.io/name: {{ include "document-extraction.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}
