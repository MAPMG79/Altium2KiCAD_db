# Feature Branch Usage

This is an example feature branch named `feature/example`.

## Feature Branch Naming Convention

Feature branches should follow the naming convention:

```
feature/<feature-name>
```

Where `<feature-name>` is a brief, descriptive name of the feature being developed.

## Feature Branch Workflow

1. Create a feature branch from `develop`:
   ```
   git checkout develop
   git pull
   git checkout -b feature/my-feature
   ```

2. Make changes, commit them, and push to remote:
   ```
   git add .
   git commit -m "Implement feature X"
   git push -u origin feature/my-feature
   ```

3. When the feature is complete, create a pull request to merge into `develop`

4. After review and approval, merge the feature branch into `develop`

5. Delete the feature branch after it has been merged:
   ```
   git branch -d feature/my-feature
   git push origin --delete feature/my-feature