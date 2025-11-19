# GitHub Workflows - Manual Setup Required

This directory contains CI/CD workflow configurations for GitHub Actions.

## Why Manual Setup?

GitHub's security model prevents automated tools (GitHub Apps) from creating or modifying workflow files (`.github/workflows/*.yml`) without explicit `workflows` permission. This is a security feature to prevent unauthorized code execution.

## How to Enable CI/CD

### Option 1: Manual File Creation (Recommended)

1. In your GitHub repository, click "Actions" tab
2. Click "New workflow" or "Set up a workflow yourself"
3. Copy the contents of `.github/workflows/ci.yml` from your local repository
4. Paste into the GitHub workflow editor
5. Commit directly to your branch

### Option 2: Push from Local Git (If you have access)

If you have direct repository access (not using GitHub App):

```bash
git add .github/workflows/ci.yml
git commit -m "Add CI/CD pipeline"
git push origin your-branch
```

### Option 3: Create Pull Request

1. Create a new branch locally
2. Add the workflow file
3. Push the branch
4. Create a Pull Request
5. Merge after review

## Included Workflows

- **ci.yml** - Complete CI/CD pipeline with:
  - Linting and formatting (ruff, black, isort, mypy)
  - Testing across Python 3.8-3.11
  - Code coverage reporting
  - Docker image building
  - Security scanning (Trivy, Bandit)
  - Automated deployment to staging/production

## Secrets Required

Configure these secrets in GitHub Settings → Secrets and variables → Actions:

- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token
- Additional secrets as needed for your deployment

## Testing Locally

You can test the workflow locally using [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run workflow locally
act -j test
act -j lint
```

## Next Steps

Once the workflow is set up, every push to `main` or `develop` will:
- Run automated tests
- Check code quality
- Build Docker images
- Deploy to staging (develop branch) or production (releases)

For more information, see the [GitHub Actions documentation](https://docs.github.com/en/actions).
