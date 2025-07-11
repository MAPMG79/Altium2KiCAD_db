# Release Branch Usage

This is an example release branch named `release/v1.0.0`.

## Release Branch Naming Convention

Release branches should follow the naming convention:

```
release/vX.Y.Z
```

Where `X.Y.Z` follows semantic versioning:
- `X`: Major version (breaking changes)
- `Y`: Minor version (new features, non-breaking)
- `Z`: Patch version (bug fixes, non-breaking)

## Release Branch Workflow

1. Create a release branch from `develop` when you're ready to prepare a new release:
   ```
   git checkout develop
   git pull
   git checkout -b release/v1.2.3
   ```

2. Make final adjustments, version bumps, and release-specific changes:
   ```
   # Update version numbers in relevant files
   git add .
   git commit -m "Bump version to 1.2.3"
   ```

3. Push the release branch to remote:
   ```
   git push -u origin release/v1.2.3
   ```

4. Test thoroughly on the release branch, making any necessary bug fixes directly on this branch

5. When the release is ready, merge into both `main` and back into `develop`:
   ```
   # Merge to main
   git checkout main
   git merge --no-ff release/v1.2.3 -m "Release v1.2.3"
   git tag -a v1.2.3 -m "Version 1.2.3"
   git push origin main --tags
   
   # Merge back to develop
   git checkout develop
   git merge --no-ff release/v1.2.3 -m "Merge release v1.2.3 back to develop"
   git push origin develop
   ```

6. Delete the release branch after it has been merged:
   ```
   git branch -d release/v1.2.3
   git push origin --delete release/v1.2.3
   ```

## Release Branch Purpose

Release branches provide a dedicated space to prepare a new version for release, allowing:
- Last-minute bug fixes
- Version number updates
- Documentation finalization
- Final testing

Meanwhile, development can continue on the `develop` branch for the next release.