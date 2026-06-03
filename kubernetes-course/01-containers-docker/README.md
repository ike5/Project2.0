# Module 01 — Containers & Docker Primer

**Goal:** understand what containers *are*, build and run one yourself, and see
exactly why we need an orchestrator like Kubernetes.

⏱️ ~1.5 hours · 🎯 Prereq: Module 00 complete (Docker running).

> You're new to containers, so we start here. Kubernetes orchestrates containers —
> you can't reason about Kubernetes until containers feel concrete.

---

## 1. The problem containers solve

"It works on my machine" happens because an app depends on a specific OS,
libraries, language runtime, and config that differ between machines.

A **container** packages your app *with* its dependencies into one portable unit
that runs the same everywhere Docker (or any container runtime) runs.

It's **not** a virtual machine. A VM virtualizes hardware and runs a whole guest
OS (heavy, slow to boot). A container shares the host's kernel and isolates just
the process (lightweight, boots in milliseconds).

```
   VM model                         Container model
┌───────────────┐               ┌───────────────────────────┐
│ App A | App B │               │ App A  │ App B │ App C     │
│ Libs  | Libs  │               │ Libs   │ Libs  │ Libs      │
│ Guest | Guest │               ├────────┴───────┴───────────┤
│  OS   |  OS   │               │   Container runtime         │
├───────────────┤               ├─────────────────────────────┤
│  Hypervisor   │               │      Host OS kernel         │
├───────────────┤               ├─────────────────────────────┤
│   Hardware    │               │        Hardware             │
└───────────────┘               └───────────────────────────┘
  heavy, GBs, slow                 light, MBs, fast
```

## 2. Images vs containers (the key distinction)

- An **image** is a read-only template: your app + dependencies, built in **layers**.
- A **container** is a running instance of an image. One image → many containers.

Analogy: image = class, container = object. Or image = a recipe, container = the cooked dish.

Images are built from a **Dockerfile** (a recipe) and stored in a **registry**
(like Docker Hub) so they can be shared and pulled onto any machine.

## 3. Layers and caching (why build order matters)

Each instruction in a Dockerfile creates a **layer**. Layers are cached and shared:
- If a layer's inputs didn't change, Docker reuses the cached layer → fast rebuilds.
- That's why we `COPY requirements.txt` and `pip install` **before** copying
  `app.py`: changing your code doesn't bust the (slow) dependency layer.

## 4. Why orchestration? (the bridge to Kubernetes)

Running one container with `docker run` is easy. Now imagine production:

- You need **5 copies** for load → who starts/watches them?
- A container **crashes** at 3am → who restarts it?
- You deploy a **new version** → how do you do it with zero downtime?
- Traffic **spikes** → who adds more copies, then removes them?
- A **whole machine dies** → who moves its containers elsewhere?
- Containers need to **find each other** across machines → who does the networking?

Doing this by hand across many machines is impossible. **Kubernetes is the system
that does all of it for you**, continuously. That's the entire reason it exists.

---

## 5. Do the lab

Build the course's sample app image, run it, poke at it, and perform the crucial
step that bridges to Kubernetes: **loading a local image into kind**.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

image · container · layer · registry · Dockerfile · container runtime

**Next →** [Module 02: Kubernetes Fundamentals](../02-k8s-fundamentals/)
