#!/bin/bash
set -e

# ─── GitHub Stats Live Updater ─────────────────────────────────────────────
# Fetches live stats from GitHub API and patches dark_mode.svg / light_mode.svg
# ────────────────────────────────────────────────────────────────────────────

if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ GITHUB_TOKEN not set"
  exit 1
fi

USERNAME="shiv207"
AUTH="Authorization: token $GITHUB_TOKEN"
API="https://api.github.com"
SVG_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "⟳ Fetching stats for $USERNAME..."

# ─── User profile ──────────────────────────────────────────────────────────
USER_DATA=$(curl -sf -H "$AUTH" "$API/users/$USERNAME")
REPOS=$(echo "$USER_DATA" | jq -r '.public_repos')
FOLLOWERS=$(echo "$USER_DATA" | jq -r '.followers')

echo "  Repos:     $REPOS"
echo "  Followers: $FOLLOWERS"

# ─── Total stars (sum of stargazers_count across all repos) ────────────────
STARS=0
PAGE=1
while true; do
  REPOS_PAGE=$(curl -sf -H "$AUTH" "$API/users/$USERNAME/repos?per_page=100&page=$PAGE&type=public")
  COUNT=$(echo "$REPOS_PAGE" | jq 'length')
  [ "$COUNT" -eq 0 ] && break
  PAGE_STARS=$(echo "$REPOS_PAGE" | jq '[.[].stargazers_count] | add // 0')
  STARS=$((STARS + PAGE_STARS))
  PAGE=$((PAGE + 1))
done

echo "  Stars:     $STARS"

# ─── Total commits (via search API) ────────────────────────────────────────
COMMITS_DATA=$(curl -sf -H "$AUTH" "$API/search/commits?q=author:$USERNAME&per_page=1")
COMMITS=$(echo "$COMMITS_DATA" | jq -r '.total_count // 0')

# Format commits with comma separator
if [ "$COMMITS" -ge 1000 ]; then
  COMMITS_FMT=$(printf "%'d+" "$COMMITS")
else
  COMMITS_FMT="${COMMITS}+"
fi

echo "  Commits:   $COMMITS ($COMMITS_FMT)"

# ─── Update dark_mode.svg ──────────────────────────────────────────────────
DM="$SVG_DIR/dark_mode.svg"
sed -i "s/>[0-9]* public repositories</>$REPOS public repositories</g" "$DM"
sed -i "s/>[0-9]* developers</>$FOLLOWERS developers</g" "$DM"
sed -i "s/Repos:<tspan class=\"cc\"> [0-9]* </Repos:<tspan class=\"cc\"> $REPOS </g" "$DM"
sed -i "s/Stars:<tspan class=\"cc\"> [0-9]* </Stars:<tspan class=\"cc\"> $STARS </g" "$DM"
sed -i "s/Followers:<tspan class=\"cc\"> [0-9]* </Followers:<tspan class=\"cc\"> $FOLLOWERS </g" "$DM"
sed -i "s/Commits:<tspan class=\"cc\"> [0-9,+]*</Commits:<tspan class=\"cc\"> $COMMITS_FMT</g" "$DM"
echo "  ✓ dark_mode.svg updated"

# ─── Update light_mode.svg ─────────────────────────────────────────────────
LM="$SVG_DIR/light_mode.svg"
sed -i "s/>[0-9]* public repositories</>$REPOS public repositories</g" "$LM"
sed -i "s/>[0-9]* developers</>$FOLLOWERS developers</g" "$LM"
sed -i "s/Repos:<tspan class=\"cc\"> [0-9]* </Repos:<tspan class=\"cc\"> $REPOS </g" "$LM"
sed -i "s/Stars:<tspan class=\"cc\"> [0-9]* </Stars:<tspan class=\"cc\"> $STARS </g" "$LM"
sed -i "s/Followers:<tspan class=\"cc\"> [0-9]* </Followers:<tspan class=\"cc\"> $FOLLOWERS </g" "$LM"
sed -i "s/Commits:<tspan class=\"cc\"> [0-9,+]*</Commits:<tspan class=\"cc\"> $COMMITS_FMT</g" "$LM"
echo "  ✓ light_mode.svg updated"

echo "✅ Stats update complete"
