# Sample application

A ~50-line Flask app whose only job is to prove that the connection details
Crossplane generated actually reached the Pod.

`GET /` reports which database environment variables arrived, whether the database
is reachable, and **whether a password is present — never its value**. An app that
logs its own credentials would undo the security the platform provides.

## Build and load it into kind

```bash
cd 06-composing-applications/manifests/app
docker build -t xp-course/sample-app:1.0 .
kind load docker-image xp-course/sample-app:1.0 --name xp-course
```

`kind load` is required because the image exists only on your machine — the
cluster's nodes have no registry to pull it from. Forgetting this step is the
number one cause of `ImagePullBackOff` on kind.
