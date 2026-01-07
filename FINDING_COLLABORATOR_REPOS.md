# How to See What Repositories You Are a Collaborator On

This guide explains multiple ways to see which GitHub repositories you are a collaborator on.

## Method 1: Using the Python Script (Recommended)

We've created a Python script that uses the GitHub API to list all repositories where you are a collaborator.

### Prerequisites

1. Install Python 3.6 or higher
2. Install the `requests` library:
   ```bash
   pip install requests
   ```

3. Create a GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token" → "Generate new token (classic)"
   - Give it a name (e.g., "Repo Finder")
   - Select the `repo` scope (for full repository access)
   - Click "Generate token" and copy the token

### Usage

1. Set your GitHub token as an environment variable:
   ```bash
   export GITHUB_TOKEN=your_token_here
   ```

2. Run the script:
   ```bash
   python list_collaborator_repos.py
   ```

3. Choose what you want to see:
   - Option 1: Repositories where you are a collaborator (not owner)
   - Option 2: All repositories (owned, collaborator, organization)
   - Option 3: Only repositories you own
   - Option 4: Only organization repositories

### Example Output

```
================================================================================
Found 5 repository(ies) where you are a collaborator
================================================================================

1. teamowner/project-alpha
   🔒 Private
   Description: Trading algorithm project
   URL: https://github.com/teamowner/project-alpha
   Last updated: 2026-01-05
   Permissions: push, pull

2. organization/shared-repo
   🌐 Public
   Description: Shared research repository
   URL: https://github.com/organization/shared-repo
   Last updated: 2026-01-02
   Permissions: admin, push, pull
```

## Method 2: Using GitHub CLI (gh)

If you have the [GitHub CLI](https://cli.github.com/) installed:

```bash
# List all your repositories
gh repo list --limit 100

# List repositories for a specific user/organization
gh repo list username --limit 100

# Filter by various criteria
gh repo list --json name,owner,isPrivate,pushedAt --template '{{range .}}{{.owner.login}}/{{.name}} - {{.isPrivate}} - {{.pushedAt}}{{"\n"}}{{end}}'
```

## Method 3: Using GitHub Web Interface

1. Go to https://github.com
2. Click on your profile picture (top right) → "Your repositories"
3. Use the filter dropdown to select different views:
   - Sources (repositories you created)
   - Forks (forked repositories)
   - Archived (archived repositories)
   - Can be contributed to (repositories where you have write access)

Note: The web interface doesn't have a direct "collaborator" filter, which is why the script or CLI methods are better.

## Method 4: Using GitHub API Directly

You can use the GitHub API with curl or any HTTP client:

```bash
# Set your token
export GITHUB_TOKEN=your_token_here

# Get repositories where you are a collaborator
curl -H "Authorization: token $GITHUB_TOKEN" \
     "https://api.github.com/user/repos?affiliation=collaborator&per_page=100"

# Get all repositories (owned, collaborator, organization)
curl -H "Authorization: token $GITHUB_TOKEN" \
     "https://api.github.com/user/repos?affiliation=owner,collaborator,organization_member&per_page=100"
```

## Method 5: Using Git Configuration

If you've cloned repositories locally, you can search your filesystem:

```bash
# Find all git repositories in your home directory
find ~ -name ".git" -type d 2>/dev/null | while read gitdir; do
    cd "$gitdir/.."
    echo "Repository: $(git remote get-url origin 2>/dev/null || echo 'No remote')"
    pwd
    echo "---"
done
```

## Troubleshooting

### "No repositories found"

- Make sure your GitHub token has the correct permissions (`repo` scope)
- Verify you are actually a collaborator on repositories
- Check that the token hasn't expired

### "401 Unauthorized" Error

- Your token may be invalid or expired
- Generate a new token and try again

### Rate Limiting

- GitHub API has rate limits (5000 requests/hour for authenticated users)
- If you hit the limit, wait an hour or use a different method

## Additional Resources

- [GitHub API Documentation](https://docs.github.com/en/rest/repos/repos)
- [GitHub CLI Documentation](https://cli.github.com/manual/)
- [Managing Repository Access](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-teams-and-people-with-access-to-your-repository)

## Security Note

⚠️ **Never commit your GitHub token to a repository!** Always use environment variables or secure credential storage.
