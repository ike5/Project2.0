# Glossary

Plain-English definitions of every term used in this course. Skim it now; come
back whenever a word trips you up.

## Containers & images

- **Image** — A read-only, packaged snapshot of an app + its dependencies + OS
  libraries. Like a class in programming.
- **Container** — A running instance of an image. Like an object. You can run many
  containers from one image.
- **Layer** — Images are built in stacked layers (one per build step). Shared
  layers are cached and reused, which makes builds and pulls fast.
- **Registry** — A server that stores images (e.g. Docker Hub, GHCR). You `push`
  images to it and `pull` images from it.
- **Dockerfile** — A recipe describing how to build an image, step by step.
- **Container runtime** — The software that actually runs containers on a node
  (e.g. containerd). Kubernetes talks to it via the CRI.

## Cluster anatomy

- **Cluster** — A set of machines (nodes) running Kubernetes together as one system.
- **Node** — A single machine (VM or, in kind, a Docker container) in the cluster.
- **Control plane** — The "brain" of the cluster. Makes global decisions and
  detects/responds to events.
- **kube-apiserver** — The front door to the cluster. *Everything* talks to it.
  `kubectl` is just an HTTP client for this API.
- **etcd** — The cluster's database. Stores all state (the "desired world").
- **scheduler** — Decides *which node* a new Pod should run on.
- **controller-manager** — Runs control loops that drive actual state toward
  desired state (the heart of reconciliation).
- **kubelet** — The agent on each node that starts/stops containers and reports health.
- **kube-proxy** — Maintains network rules on each node so Services work.
- **CNI (Container Network Interface)** — Plugin that gives Pods their networking
  (e.g. kindnet, Calico).

## Workload objects

- **Pod** — The smallest deployable unit. One or more containers that share network
  and storage. Usually one main container per Pod.
- **ReplicaSet** — Keeps a specified number of identical Pods running. You rarely
  create these directly.
- **Deployment** — Manages ReplicaSets to give you declarative updates, rollbacks,
  and scaling for stateless apps. **Your default workload type.**
- **StatefulSet** — Like a Deployment but for stateful apps: stable network IDs,
  ordered startup, and per-Pod persistent storage (e.g. databases).
- **DaemonSet** — Runs exactly one Pod on every (or selected) node. Used for
  agents like log collectors and monitoring.
- **Job** — Runs Pods to completion once (batch work).
- **CronJob** — Runs a Job on a schedule (like cron).

## Configuration & lifecycle

- **ConfigMap** — Stores non-secret config (key/value or files) you inject into Pods.
- **Secret** — Like a ConfigMap but for sensitive data. **Base64-encoded, not
  encrypted by default** — handle with care.
- **Probe** — A health check Kubernetes runs against a container:
  - **liveness** — "Is it alive?" If it fails, the container is restarted.
  - **readiness** — "Can it serve traffic?" If it fails, it's removed from Services.
  - **startup** — "Has it finished booting?" Protects slow-starting apps.
- **Requests** — The resources (CPU/RAM) a Pod is *guaranteed*. Used for scheduling.
- **Limits** — The maximum resources a Pod may use. Exceeding RAM = `OOMKilled`.

## Networking

- **Service** — A stable virtual IP + DNS name that load-balances traffic to a set
  of Pods (Pods are ephemeral; Services are not).
  - **ClusterIP** — Internal-only (default).
  - **NodePort** — Exposes the Service on a port on every node.
  - **LoadBalancer** — Asks the cloud (or a local emulator) for an external IP.
- **Ingress** — HTTP/HTTPS routing rules ("send `/api` to this Service") handled by
  an **Ingress Controller** (e.g. ingress-nginx).
- **NetworkPolicy** — Firewall rules for Pod-to-Pod traffic. Needs a CNI that
  enforces them (e.g. Calico).

## Storage

- **Volume** — Storage attached to a Pod. Some types vanish with the Pod; others persist.
- **PersistentVolume (PV)** — A piece of real storage in the cluster.
- **PersistentVolumeClaim (PVC)** — A request for storage by a Pod ("I need 1Gi").
  Bound to a PV.
- **StorageClass** — Describes a *type* of storage and enables **dynamic
  provisioning** (PVs created automatically on demand).

## Organization & access

- **Namespace** — A virtual cluster-within-a-cluster for isolating and grouping
  resources (e.g. `dev`, `prod`).
- **Label** — A key/value tag on objects (e.g. `app=web`). Used to select/group.
- **Selector** — A query that matches objects by their labels (how Services find Pods).
- **Annotation** — Like a label but for non-identifying metadata (notes, tool config).
- **ServiceAccount** — An identity for *processes in Pods* to talk to the API.
- **RBAC (Role-Based Access Control)** — Who can do what:
  - **Role / ClusterRole** — A set of permissions (namespaced / cluster-wide).
  - **RoleBinding / ClusterRoleBinding** — Grants a Role to a user/group/ServiceAccount.

## Operations

- **Manifest** — A YAML (or JSON) file describing a desired object.
- **Declarative** — You describe the desired end state; Kubernetes makes it so
  (`kubectl apply`). The opposite of **imperative** (`kubectl run`, step commands).
- **Reconciliation** — The control loop: observe actual state → compare to desired
  → act to close the gap. Repeat forever. This is Kubernetes' core idea.
- **Rolling update** — Replacing Pods gradually so there's no downtime.
- **HPA (Horizontal Pod Autoscaler)** — Automatically adds/removes Pod replicas
  based on metrics like CPU.
- **Helm** — A package manager for Kubernetes; installs apps as templated "charts".
- **Kustomize** — A template-free way to customize manifests per environment using overlays.
- **GitOps** — Git is the source of truth; a controller (e.g. Argo CD) continuously
  syncs the cluster to match the repo.
