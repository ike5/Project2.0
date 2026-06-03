# Challenge 06 — Reference Solution

### 1. Persistent web content
```yaml
# nginx-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata: { name: html }
spec:
  accessModes: ["ReadWriteOnce"]
  resources: { requests: { storage: 1Gi } }
---
apiVersion: apps/v1
kind: Deployment
metadata: { name: nginx-persist }
spec:
  replicas: 1
  selector: { matchLabels: { app: nginx-persist } }
  template:
    metadata: { labels: { app: nginx-persist } }
    spec:
      containers:
        - name: nginx
          image: nginx:1.27
          volumeMounts:
            - { name: html, mountPath: /usr/share/nginx/html }
      volumes:
        - name: html
          persistentVolumeClaim: { claimName: html }
```
```bash
kubectl apply -f nginx-pvc.yaml
POD=$(kubectl get pod -l app=nginx-persist -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- sh -c 'echo "<h1>Saved!</h1>" > /usr/share/nginx/html/index.html'
kubectl delete pod "$POD"      # Deployment makes a new one, same PVC
sleep 5
NEW=$(kubectl get pod -l app=nginx-persist -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$NEW" -- cat /usr/share/nginx/html/index.html   # <h1>Saved!</h1>
```

### 2. Shared scratch between containers
```yaml
# shared.yaml
apiVersion: v1
kind: Pod
metadata: { name: shared }
spec:
  containers:
    - name: writer
      image: busybox:1.36
      command: ["sh","-c","while true; do date >> /shared/log.txt; sleep 1; done"]
      volumeMounts: [{ name: s, mountPath: /shared }]
    - name: reader
      image: busybox:1.36
      command: ["sh","-c","sleep 3; tail -f /shared/log.txt"]
      volumeMounts: [{ name: s, mountPath: /shared }]
  volumes:
    - name: s
      emptyDir: {}
```
```bash
kubectl apply -f shared.yaml
kubectl logs shared -c reader --tail=5    # sees timestamps the writer container produced
```

### 3. Binding lifecycle
```bash
kubectl apply -f manifests/pvc.yaml
kubectl get pvc data            # Pending or Bound (depends on WaitForFirstConsumer)
kubectl get pv
kubectl get pv -o jsonpath='{.items[0].spec.persistentVolumeReclaimPolicy}{"\n"}'  # Delete
kubectl delete pvc data
kubectl get pv                  # PV is removed (Delete policy)
```

### 4. Stretch — RWO + multiple replicas
> **ReadWriteOnce** means the volume can be mounted read/write by **one node** at a
> time. A single-replica DB is fine. Scale the Deployment to 3 and all 3 Pods try to
> mount the *same* PVC — only Pods on the same node as the volume can attach, so the
> others get stuck `Pending`/`ContainerCreating`, and even if co-located, multiple
> writers to one volume corrupt data. For stateful, replicated workloads you use a
> **StatefulSet** (Module 07), which gives **each replica its own PVC** via
> `volumeClaimTemplates`.
```
```bash
kubectl delete -f nginx-pvc.yaml -f shared.yaml --ignore-not-found
```
