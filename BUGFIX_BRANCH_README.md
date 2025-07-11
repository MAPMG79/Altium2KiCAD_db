# Bugfix Branch Usage

This is an example bugfix branch named `bugfix/example`.

## Bugfix Branch Naming Convention

Bugfix branches should follow the naming convention:

```
bugfix/<issue-description>
```

Where `<issue-description>` is a brief description of the bug being fixed.

## Bugfix Branch Workflow

1. Create a bugfix branch from `develop`:
   ```
   git checkout develop
   git pull
   git checkout -b bugfix/issue-description
   ```

2. Make changes to fix the bug, commit them, and push to remote:
   ```
   git add .
   git commit -m "Fix issue with X"
   git push -u origin bugfix/issue-description
   ```

3. When the bug is fixed, create a pull request to merge into `develop`

4. After review and approval, merge the bugfix branch into `develop`

5. Delete the bugfix branch after it has been merged:
   ```
   git branch -d bugfix/issue-description
   git push origin --delete bugfix/issue-description
   ```

## Hotfix vs Bugfix

- **Bugfix**: Fixes issues in the development branch (`develop`) that haven't been released to production yet
- **Hotfix**: Fixes critical issues in the production branch (`main`) that need immediate attention