# Documentation Build Directory

This directory contains the raw build output of the Sphinx documentation for the Altium2KiCAD_db project.

## Purpose

This directory serves as a temporary storage location for documentation builds, particularly useful for:

1. **ReadTheDocs.org Build Issues**: When experiencing build issues with ReadTheDocs.org, you can build the documentation locally and access it directly.

2. **GitHub Pages Deployment**: The GitHub Actions workflow `docs_build.yml` automatically builds and deploys the documentation to GitHub Pages.

3. **Local Documentation Testing**: Use the `scripts/build_docs.py` script to build documentation locally and view it without needing to set up a web server.

## How to Use

### Automatic Build (GitHub Actions)

The documentation is automatically built and deployed to GitHub Pages when changes are pushed to the `main` branch that affect the documentation files. You can view the deployed documentation at:

`https://[your-username].github.io/Altium2KiCAD_db/docs-build/`

### Manual Build

To manually build the documentation:

```bash
# Using the provided Python script
python scripts/build_docs.py

# Or using Sphinx directly
cd docs
make html
```

The built documentation will be available in the `docs_build/html` directory. Open `docs_build/html/index.html` in your browser to view it.

## Note

This directory is excluded from version control via `.gitignore`. Only the README file is tracked.