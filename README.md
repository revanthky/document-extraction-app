# Helm chart repository

This branch is a Helm chart repository index for `document-extraction`, generated with
`helm package` + `helm repo index`. It is not meant to be checked out for development — see
the `main` branch for the actual application and chart source
(`charts/document-extraction/`).

## Use it

```bash
helm repo add document-extraction \
  https://raw.githubusercontent.com/revanthky/document-extraction-app/gh-pages/
helm repo update
helm install document-extraction document-extraction/document-extraction
```

(Enabling GitHub Pages for this branch would additionally make it reachable at
`https://revanthky.github.io/document-extraction-app/`, if preferred over the raw URL above.)

## Regenerating

From a fresh checkout of this branch, after a new chart version is cut on `main`:

```bash
helm package ../main-checkout/charts/document-extraction -d .
helm repo index . --url https://raw.githubusercontent.com/revanthky/document-extraction-app/gh-pages/
git add . && git commit -m "Add document-extraction <version>" && git push
```

`helm repo index --merge index.yaml` (pointing at the existing file) preserves prior chart
versions instead of overwriting them, once there is more than one.
