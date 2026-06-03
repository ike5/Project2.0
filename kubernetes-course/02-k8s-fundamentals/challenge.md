# Challenge 02 — Read the Cluster

Answer using `kubectl` (not Google). Solutions in [`solutions/`](./solutions/).

## Tasks

1. **Find the busiest node.** Which worker node is currently running the most Pods
   (across all namespaces)? Use a single `kubectl get pods` invocation with the
   right flags.

2. **Explain a field.** Without leaving the terminal, find out what the
   `spec.containers.imagePullPolicy` field does and its allowed values.

3. **Prove the difference.** Create a bare Pod named `solo` and a Deployment named
   `managed` (both `nginx:1.27`). Delete one Pod from each. Show that `managed`
   recovers and `solo` does not, and explain *which controller* recreated the
   managed Pod.

4. **Namespace isolation.** Create a namespace `team-a`. Run an nginx Pod in it.
   From the `default` namespace, retrieve that Pod's IP using a single command
   (hint: `-n` and `-o wide` or jsonpath).

5. **Stretch:** Use `kubectl get pod <name> -o yaml` to find the `nodeName` the
   scheduler assigned and the Pod's `status.phase`.

## Success criteria
- [ ] You identified the node with the most Pods from one command.
- [ ] You used `kubectl explain` to answer about `imagePullPolicy`.
- [ ] You demonstrated reconciliation (managed recovers, solo doesn't) and named
      the responsible controller (ReplicaSet).
- [ ] You read a Pod's IP from another namespace in one command.
