#!/usr/bin/env bash
# Sets up GitHub branch protection on main: requires a PR, no direct pushes.
set -euo pipefail

REPO="reivosar/ai-developer-kit"

gh api "repos/$REPO/branches/main/protection" \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  --field enforce_admins=true \
  --field required_status_checks=null \
  --field restrictions=null \
  --field 'required_pull_request_reviews={"required_approving_review_count":0,"dismiss_stale_reviews":false}'

echo "Branch protection enabled: direct pushes to main are now blocked."
