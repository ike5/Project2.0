# kubectl Cheatsheet

The commands you'll reach for constantly. `kubectl` is just an HTTP client for the
Kubernetes API — every command below is a request to the api-server.

> 💡 Set up an alias and autocompletion (one-time, in your `~/.zshrc`):
> ```bash
> alias k=kubectl
> source <(kubectl completion zsh)
> complete -o default -F __start_kubectl k
> export do="--dry-run=client -o yaml"   # generate manifests fast: kubectl run x --image=nginx $do
> ```

## Contexts & namespaces (where am I?)

```bash
kubectl config get-contexts                 # list clusters you can reach
kubectl config current-context              # which cluster am I pointed at?
kubectl config use-context kind-k8s-course  # switch cluster
kubectl get ns                              # list namespaces
kubectl config set-context --current --namespace=dev   # change default namespace
# or use kubens (from kubectx) to switch namespaces interactively
```

## Looking at things (`get` / `describe`)

```bash
kubectl get pods                       # in current namespace
kubectl get pods -A                    # ALL namespaces
kubectl get pods -o wide               # + node, IP
kubectl get pods -w                    # watch live
kubectl get pods -l app=web            # filter by label
kubectl get all                        # pods, services, deployments, etc.
kubectl get pod my-pod -o yaml         # full manifest of a live object
kubectl describe pod my-pod            # human-readable details + Events (read the Events!)
kubectl get events --sort-by=.lastTimestamp   # what just happened?
```

## Creating & changing (declarative — preferred)

```bash
kubectl apply -f manifest.yaml         # create or update from file
kubectl apply -f manifests/            # apply a whole directory
kubectl diff -f manifest.yaml          # preview what apply would change
kubectl delete -f manifest.yaml        # delete what's in the file
```

## Creating & changing (imperative — fast for experiments)

```bash
kubectl run web --image=nginx                       # quick throwaway pod
kubectl create deployment web --image=nginx --replicas=3
kubectl expose deployment web --port=80             # make a Service
kubectl scale deployment web --replicas=5
kubectl set image deployment/web nginx=nginx:1.27   # trigger a rolling update
kubectl edit deployment web                         # open live object in $EDITOR
kubectl delete pod web
```

> ⭐ **Pro move:** generate YAML instead of hand-writing it:
> ```bash
> kubectl create deployment web --image=nginx --dry-run=client -o yaml > deploy.yaml
> ```

## Rollouts (Deployments)

```bash
kubectl rollout status deployment/web      # wait for a rollout to finish
kubectl rollout history deployment/web     # past revisions
kubectl rollout undo deployment/web        # roll back to previous
kubectl rollout undo deployment/web --to-revision=2
kubectl rollout restart deployment/web     # restart all pods (e.g. to pick up new ConfigMap)
```

## Debugging (your daily bread)

```bash
kubectl logs my-pod                        # logs
kubectl logs my-pod -c container-name      # specific container in a multi-container pod
kubectl logs my-pod --previous             # logs from the crashed previous instance
kubectl logs -f my-pod                     # follow (tail)
kubectl exec -it my-pod -- sh              # shell into a container
kubectl exec my-pod -- env                 # run a one-off command
kubectl port-forward pod/my-pod 8080:80    # tunnel a pod port to localhost:8080
kubectl port-forward svc/web 8080:80       # tunnel a Service
kubectl debug -it my-pod --image=busybox --target=app   # ephemeral debug container
kubectl top pods                           # CPU/RAM usage (needs metrics-server)
kubectl top nodes
```

## Explaining the API (built-in docs!)

```bash
kubectl explain pod                        # what fields does a Pod have?
kubectl explain pod.spec.containers        # drill into nested fields
kubectl explain deployment --recursive     # the whole tree
kubectl api-resources                      # every object kind + its short name + apiVersion
```

## Labels, selectors, and quick edits

```bash
kubectl label pod my-pod tier=frontend     # add a label
kubectl label pod my-pod tier-             # remove a label (trailing dash)
kubectl annotate pod my-pod note="flaky"   # add an annotation
kubectl get pods --show-labels
```

## Cleanup

```bash
kubectl delete pod my-pod
kubectl delete deployment web
kubectl delete -f manifests/
kubectl delete ns dev                      # nukes everything in the namespace
```

## Field selectors & output tricks

```bash
kubectl get pods --field-selector status.phase=Running
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
kubectl get pods -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName
```

---
**Golden rule:** when something is wrong, run `kubectl describe` and
`kubectl get events` first — the answer is almost always in the Events.
