# Challenge 13: Production-Grade CI/CD for a Unity Game

**Time**: 4 hours
**Goal**: Build a complete CI/CD pipeline for a multi-platform Unity game. From `git push` to build artifact on TestFlight, internal testing on Play Console, and a Docker image of the dedicated server. The pipeline includes size tracking, symbol upload, integration tests, and a fastlane submission.

## Scope

A small turn-based multiplayer game (same scope as the module 11 challenge). Targets: iOS, Android, Windows, Linux dedicated server. CI runs on every commit to main, on every PR, and nightly for the full test suite.

The pipeline:
1. On PR: run unit tests, build Android (fast feedback).
2. On main: run unit tests, build all platforms, run integration tests, submit iOS to TestFlight, submit Android to Play Internal.
3. Nightly: run all tests, run 30-minute soak test, profile the game, generate a daily report.
4. On tag: build release artifacts, submit to stores.

## Requirements

### 1. Build script

A `BuildScript.cs` with:
- `BuildAndroid()`: AAB, ARM64, IL2CPP, High stripping.
- `BuildIOS()`: Xcode project, ARM64, IL2CPP, High stripping.
- `BuildWindows()`: Windows x64 player, IL2CPP, High stripping.
- `BuildLinuxServer()`: Linux server, IL2CPP, High stripping, Server subtarget.
- `BuildAddressables()`: builds the Addressables content for the current target.
- `WriteBuildReport()`: writes `build-report.json` with platform, size, time, errors, warnings, stripping info.
- `UploadSymbols()`: post-build step, uploads the IL2CPP symbols to your crash reporting backend (Firebase Crashlytics, Sentry, or similar).

### 2. CI provider: GitHub Actions

Workflows:
- `.github/workflows/pr.yml`: PR validation. Runs unit tests + Android build.
- `.github/workflows/main.yml`: Main branch. Runs unit tests + integration tests + all platform builds + size check + symbol upload.
- `.github/workflows/nightly.yml`: Nightly. Runs full test suite + soak test + profile capture.
- `.github/workflows/release.yml`: On tag. Builds release artifacts, runs fastlane to submit to TestFlight and Play Internal.

The workflows use the `game-ci/unity-builder` action with caching. Library is cached for 30 days.

### 3. Tests

Unit tests use Unity Test Framework (`com.unity.test-framework`). The pipeline runs:
- Edit mode tests: pure logic, no Play mode.
- Play mode tests: scene-based, run in batch mode with rendering.

The pipeline runs tests with `-runTests -testPlatform editmode` and `-runTests -testPlatform playmode`. The results are saved as NUnit XML and uploaded as artifacts.

### 4. Integration tests

A test scene that:
- Starts the host.
- Connects a client.
- Plays 100 turns.
- Verifies state consistency.

The integration test runs in nightly, takes 5-10 minutes, and verifies the server-client contract.

### 5. Size tracking

After every build, write the size to a file. CI compares against the previous main. Alert if > 10% growth.

A more sophisticated version tracks size per platform and per build type (debug, release). The size is graphed in a dashboard.

### 6. Symbol upload

The build script generates the IL2CPP symbols and uploads them to the crash reporting backend. The post-build step runs after every Android and iOS build on main.

For Crashlytics:
```bash
firebase crashlytics:symbols:upload \
  --app=1:1234567890:android:abcdef \
  builds/arenagame/symbols.zip
```

For Sentry:
```bash
sentry-cli upload-dif \
  --org=myorg --project=arenagame \
  builds/arenagame/symbols.zip
```

### 7. fastlane submission

`fastlane/Fastfile`:
```ruby
default_platform(:ios)

platform :ios do
  lane :beta do
    build_app(
      workspace: "Unity-iPhone.xcworkspace",
      scheme: "Unity-iPhone",
      configuration: "Release",
      export_method: "app-store",
      output_directory: "./builds/ios"
    )
    upload_to_testflight(skip_waiting_for_build_processing: true)
  end
end

platform :android do
  lane :internal do
    upload_to_play_store(
      track: "internal",
      aab: "./builds/android/arenagame.aab",
      json_key: "./fastlane/play-store-key.json"
    )
  end
end
```

The fastlane runs in the release workflow, after the Unity build.

### 8. Docker image for the server

A `Dockerfile`:
```dockerfile
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y libglu1-mesa libxi6 libxrandr2 libxcursor1 libxinerama1
COPY Builds/LinuxServer /server
WORKDIR /server
EXPOSE 7777
ENTRYPOINT ["./Server.x86_64", "-batchmode", "-nographics", "-port", "7777"]
```

The CI builds the Docker image and pushes to a registry (Docker Hub, AWS ECR, GitHub Container Registry).

### 9. Notifications

Slack webhook on:
- Build failure.
- Build size regression > 10%.
- Test failure.
- Successful release deployment.

### 10. Documentation

`CICD.md` describing:
- The pipeline architecture.
- How to add a new platform.
- How to rotate the Unity license.
- How to add a new test.
- The on-call runbook for build failures.

## Deliverables

1. The Unity project with all build scripts.
2. The GitHub Actions workflows.
3. The fastlane setup.
4. The Dockerfile.
5. The `CICD.md` documentation.
6. A screenshot of the Actions tab showing green builds.
7. A screenshot of the size tracking dashboard (or the size history as a CSV).

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| PR workflow runs and reports status | required |
| Main workflow builds all platforms | required |
| Nightly workflow runs all tests | required |
| Release workflow submits to TestFlight | required |
| Release workflow submits to Play Internal | required |
| Build size tracked over time | required |
| Symbols uploaded to crash reporting | required |
| Server Docker image built and pushed | required |
| Slack notifications on failure | required |
| CICD.md documents the pipeline | required |

## Grading rubric

- **Pipeline correctness (30%)**: every workflow runs and succeeds.
- **Build size tracking (20%)**: trend is visible, regression is caught.
- **Symbol upload (15%)**: crash reports are deobfuscated.
- **Submission automation (20%)**: TestFlight and Play Internal work.
- **Documentation (15%)**: CICD.md is clear and complete.

## Senior notes

The pipeline is a product. It has users (the team), it has features (new platforms, new tests), it has bugs (it breaks when you change Unity version). Treat it as a product. The same engineering discipline you apply to the game applies to the pipeline.

Test the pipeline. The pipeline that has never been tested is the pipeline that fails on the day you need it. Run a dry-run release to TestFlight in week 1, even if the game is empty. Find the bugs early.

The license file is the most fragile part. Unity rotates the license format every 2-3 years. The license server is sometimes down. The license is sometimes bound to a machine ID. Plan for the license to break. Have a runbook for "the license is broken, here's what to do."

The cache invalidation is fragile. The Library cache is invalidated on `Assets/**` changes, which is too aggressive. Use a more stable cache key: `Packages/manifest.json` + `ProjectSettings/**` + a project hash. The cache should survive most asset changes.

The size tracking is a feature, not a debug tool. The dashboard that shows "we went from 80 MB to 88 MB in 3 weeks, here's the diff" is a real time-saver. The diff is the leading indicator of "we forgot to optimize this."

The symbol upload is a feature, not a debug tool. The crash report that says `PlayerMotor.cs:42` instead of `0x4a8f3c` saves hours per crash. Multiply by 100 crashes per week. The symbol upload pays for itself in a month.

The fastlane submission is a feature, not a debug tool. The 30-minute "push to TestFlight" workflow that used to take 2 days of manual work is the difference between "we can ship a hotfix" and "we can't ship this week."

The Docker image is a feature, not a debug tool. The containerized server that deploys with `kubectl apply` is the difference between "we can scale to 1000 players" and "we can only run on the one machine we set up."

The Slack notifications are a feature, not a debug tool. The team that knows about the build failure in 30 seconds is the team that ships on time. The team that finds out the next day is the team that misses the deadline.

Ship it.
