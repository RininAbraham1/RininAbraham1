"""Build the profile's stats and language cards from live GitHub data.

Runs in the update-stats workflow. Uses GITHUB_TOKEN (public data only) or,
if set, a STATS_TOKEN personal access token so private work is counted too.
"""
import json
import os
import sys
import urllib.request
from html import escape

LOGIN = os.environ.get("GH_LOGIN", "RininAbraham1")
OUT = os.environ.get("OUT_DIR", "assets")

QUERY = """
query($login: String!) {
  user(login: $login) {
    name
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
    pullRequests { totalCount }
    merged: pullRequests(states: MERGED) { totalCount }
    issues { totalCount }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
    }
    repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) {
      totalCount
    }
  }
}
"""

# Next tier thresholds for the Pull Shark achievement.
PULL_SHARK = [2, 16, 128, 1024]

STYLE = """
<style>
  .bg { fill: #ffffff; }
  .title { font: 600 18px 'Segoe UI', Ubuntu, sans-serif; fill: #c77dff; }
  .label { font: 600 14px 'Segoe UI', Ubuntu, sans-serif; fill: #444441; }
  .value { font: 700 14px 'Segoe UI', Ubuntu, sans-serif; fill: #444441; }
  .hint  { font: 400 12px 'Segoe UI', Ubuntu, sans-serif; fill: #8a8a86; }
  .icon  { fill: #52b788; }
  @media (prefers-color-scheme: dark) {
    .bg { fill: #0d1117; }
    .label, .value { fill: #e6edf3; }
    .hint { fill: #8b949e; }
  }
</style>
"""


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        data = json.load(resp)
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


def summarize(user):
    repos = user["repositories"]["nodes"]
    langs = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            entry = langs.setdefault(name, {"size": 0, "color": edge["node"]["color"] or "#888888"})
            entry["size"] += edge["size"]
    cc = user["contributionsCollection"]
    merged = user["merged"]["totalCount"]
    next_tier = next((t for t in PULL_SHARK if t > merged), None)
    return {
        "name": user["name"] or LOGIN,
        "stars": sum(r["stargazerCount"] for r in repos),
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "prs": user["pullRequests"]["totalCount"],
        "merged": merged,
        "next_tier": next_tier,
        "issues": user["issues"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "langs": sorted(langs.items(), key=lambda kv: kv[1]["size"], reverse=True),
    }


def stats_svg(s):
    rows = [
        ("Total Stars Earned", s["stars"]),
        ("Commits (last year)", s["commits"]),
        ("Pull Requests", s["prs"]),
        ("Merged PRs", s["merged"]),
        ("Issues", s["issues"]),
        ("Contributed to (last year)", s["contributed"]),
    ]
    width, row_h, top = 420, 26, 62
    height = top + row_h * len(rows) + 30
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', STYLE,
           f'<rect class="bg" x="0.5" y="0.5" rx="6" width="{width - 1}" height="{height - 1}"/>',
           f'<text class="title" x="25" y="36">{escape(s["name"])}\'s GitHub Stats</text>']
    for i, (label, value) in enumerate(rows):
        y = top + i * row_h
        out.append(f'<circle class="icon" cx="31" cy="{y - 5}" r="4"/>')
        out.append(f'<text class="label" x="45" y="{y}">{label}:</text>')
        out.append(f'<text class="value" x="{width - 30}" y="{y}" text-anchor="end">{value:,}</text>')
    hint = (f"Pull Shark next tier: {s['merged']}/{s['next_tier']} merged PRs"
            if s["next_tier"] else "Pull Shark: max tier reached")
    out.append(f'<text class="hint" x="25" y="{height - 18}">{hint}</text>')
    out.append("</svg>")
    return "\n".join(out)


def langs_svg(s, top_n=6):
    langs = s["langs"][:top_n]
    total = sum(v["size"] for _, v in langs) or 1
    width, bar_w = 420, 370
    rows = (len(langs) + 1) // 2
    height = 95 + rows * 26
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', STYLE,
           f'<rect class="bg" x="0.5" y="0.5" rx="6" width="{width - 1}" height="{height - 1}"/>',
           '<text class="title" x="25" y="36">Most Used Languages</text>',
           '<clipPath id="bar"><rect x="25" y="52" rx="4" width="370" height="8"/></clipPath>',
           '<g clip-path="url(#bar)">']
    x = 25.0
    for name, v in langs:
        w = bar_w * v["size"] / total
        out.append(f'<rect x="{x:.2f}" y="52" width="{w:.2f}" height="8" fill="{v["color"]}"/>')
        x += w
    out.append("</g>")
    for i, (name, v) in enumerate(langs):
        col, row = i % 2, i // 2
        cx, cy = 30 + col * 190, 88 + row * 26
        pct = 100 * v["size"] / total
        out.append(f'<circle cx="{cx}" cy="{cy - 5}" r="5" fill="{v["color"]}"/>')
        out.append(f'<text class="label" x="{cx + 12}" y="{cy}">{escape(name)} <tspan class="hint">{pct:.1f}%</tspan></text>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    if len(sys.argv) > 1:  # local preview: python stats.py sample.json
        with open(sys.argv[1]) as f:
            user = json.load(f)
    else:
        token = os.environ.get("STATS_TOKEN") or os.environ["GITHUB_TOKEN"]
        user = fetch(token)
    s = summarize(user)
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "stats.svg"), "w") as f:
        f.write(stats_svg(s))
    with open(os.path.join(OUT, "langs.svg"), "w") as f:
        f.write(langs_svg(s))
    print(json.dumps({k: v for k, v in s.items() if k != "langs"}))


if __name__ == "__main__":
    main()
