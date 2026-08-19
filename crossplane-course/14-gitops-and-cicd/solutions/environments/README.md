# Environments

```
dev      v1.1.0    ← new versions land here first
staging  v1.1.0    ← soaks for 48h
prod     v1.0.0    ← moves only by a reviewed pull request
```

Promotion:
```bash
sed -i 's|platform:v1.0.0|platform:v1.1.0|' environments/prod/configuration.yaml
git commit -am "Promote platform v1.1.0 to prod"
```

## Why a pinned version beats a branch

1. **A branch is a moving target.** "Prod tracks `release`" means prod runs whatever
   that branch pointed at when Argo CD last synced. Two clusters syncing minutes apart
   run different code, and neither can tell you which.
2. **Rollback is exact.** `v1.0.0` is an immutable artifact. "Whatever the branch
   looked like on Tuesday" is archaeology.
3. **The environment diff is legible.** `git diff environments/prod environments/staging`
   is one line. Comparing branches shows every commit between them.
4. **It survives a force-push.** Branches can be rewritten; a pushed OCI tag cannot.
5. **It records intent.** "Promote v1.1.0 to prod" has an author, a timestamp, and a
   reviewer. A branch merge is a side effect.
