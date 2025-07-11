# Hotfix Branch Usage

This is an example hotfix branch named `hotfix/v1.0.1`.

## Hotfix Branch Naming Convention

Hotfix branches should follow the naming convention:

```
hotfix/vX.Y.Z
```

Where `X.Y.Z` follows semantic versioning, typically incrementing the patch version:
- `X`: Major version (breaking changes)
- `Y`: Minor version (new features, non-breaking)
- `Z`: Patch version (bug fixes, non-breaking)

## Hotfix Branch Workflow

1. Create a hotfix branch directly from `main` when a critical issue is found in production:
   ```
   git checkout main
   git pull
   git checkout -b hotfix/v1.0.1
   ```

2. Make the necessary fixes to address the critical issue:
   ```
   # Fix the critical issue
   git add .
   git commit -m "Fix critical issue with X"
   ```

3. Update version numbers in relevant files:
   ```
   # Update version numbers
   git add .
   git commit -m "Bump version to 1.0.1"
   ```

4. Push the hotfix branch to remote:
   ```
   git push -u origin hotfix/v1.0.1
   ```

5. When the hotfix is complete, merge into both `main` and `develop`:
   ```
   # Merge to main
   git checkout main
   git merge --no-ff hotfix/v1.0.1 -m "Hotfix v1.0.1"
   git tag -a v1.0.1 -m "Version 1.0.1"
   git push origin main --tags
   
   # Merge to develop
   git checkout develop
   git merge --no-ff hotfix/v1.0.1 -m "Merge hotfix v1.0.1 into develop"
   git push origin develop
   ```

6. Delete the hotfix branch after it has been merged:
   ```
   git branch -d hotfix/v1.0.1
   git push origin --delete hotfix/v1.0.1
   ```

## Hotfix vs Bugfix

- **Hotfix**: Fixes critical issues in the production branch (`main`) that need immediate attention
- **Bugfix**: Fixes issues in the development branch (`develop`) that haven't been released to production yet

## When to Use Hotfix Branches

Use hotfix branches when:
- A critical bug is discovered in the production version
- The fix cannot wait for the next regular release cycle
- The issue must be addressed immediately to minimize impact

Hotfixes should be kept as small and focused as possible, addressing only the critical issue without introducing new features.