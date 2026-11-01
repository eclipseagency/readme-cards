"""Minimal GitHub API client. Standard library only, no dependencies."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

API = "https://api.github.com/graphql"
REST = "https://api.github.com"


class GitHubError(RuntimeError):
    pass


@dataclass
class Stats:
    login: str
    name: str
    total_contributions: int = 0
    commits: int = 0
    pull_requests: int = 0
    reviews: int = 0
    issues: int = 0
    repositories: int = 0
    stars: int = 0
    followers: int = 0
    restricted: int = 0
    calendar: list[tuple[str, int]] = field(default_factory=list)
    languages: dict[str, int] = field(default_factory=dict)

    @property
    def active_days(self) -> int:
        return sum(1 for _, c in self.calendar if c > 0)

    def streaks(self) -> tuple[int, int]:
        """(current, longest) streak in days.

        The final day is allowed to be empty without ending the current
        streak: the calendar includes today, and a day you have not committed
        in yet is still in progress. Any earlier gap ends it.
        """
        longest = run = 0
        for _, count in self.calendar:
            run = run + 1 if count else 0
            longest = max(longest, run)

        days = list(reversed(self.calendar))
        if days and days[0][1] == 0:
            days = days[1:]          # today is still in progress
        current = 0
        for _, count in days:
            if not count:
                break
            current += 1
        return current, longest


class Client:
    def __init__(self, token: str, retries: int = 3):
        if not token:
            raise GitHubError("a GitHub token is required")
        self.token = token
        self.retries = retries

    def _request(self, url: str, data: bytes | None = None) -> dict:
        req = urllib.request.Request(url, data=data)
        req.add_header("Authorization", f"bearer {self.token}")
        req.add_header("User-Agent", "readme-cards")
        req.add_header("Accept", "application/vnd.github+json")
        if data:
            req.add_header("Content-Type", "application/json")
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    return json.loads(resp.read().decode())
            except urllib.error.HTTPError as exc:
                if exc.code in (403, 429, 502, 503) and attempt < self.retries - 1:
                    time.sleep(2 ** attempt)
                    last = exc
                    continue
                raise GitHubError(f"{url} returned {exc.code}: {exc.read()[:200]!r}") from exc
            except urllib.error.URLError as exc:
                last = exc
                if attempt < self.retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise GitHubError(f"could not reach {url}: {exc}") from exc
        raise GitHubError(str(last))

    def graphql(self, query: str, **variables) -> dict:
        payload = json.dumps({"query": query, "variables": variables}).encode()
        body = self._request(API, payload)
        if "errors" in body:
            raise GitHubError(json.dumps(body["errors"])[:400])
        return body["data"]

    # ---------------------------------------------------------------- queries

    _PROFILE = """
    query($login:String!){
      user(login:$login){
        login name followers{totalCount}
        repositories(ownerAffiliations:OWNER, isFork:false){ totalCount }
        contributionsCollection{
          totalCommitContributions
          totalPullRequestContributions
          totalPullRequestReviewContributions
          totalIssueContributions
          restrictedContributionsCount
          contributionCalendar{
            totalContributions
            weeks{ contributionDays{ date contributionCount } }
          }
        }
      }
    }"""

    _REPOS = """
    query($login:String!,$cursor:String){
      user(login:$login){
        repositories(first:100, after:$cursor, ownerAffiliations:OWNER, isFork:false){
          pageInfo{ hasNextPage endCursor }
          nodes{
            name stargazerCount
            languages(first:20, orderBy:{field:SIZE, direction:DESC}){
              edges{ size node{ name } }
            }
          }
        }
      }
    }"""

    def stats(self, login: str, exclude_languages: set[str]) -> Stats:
        data = self.graphql(self._PROFILE, login=login)["user"]
        if data is None:
            raise GitHubError(f"user {login!r} not found, or the token cannot see it")
        cc = data["contributionsCollection"]
        cal = [
            (d["date"], d["contributionCount"])
            for w in cc["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]
        ]
        s = Stats(
            login=data["login"],
            name=data["name"] or data["login"],
            total_contributions=cc["contributionCalendar"]["totalContributions"],
            commits=cc["totalCommitContributions"],
            pull_requests=cc["totalPullRequestContributions"],
            reviews=cc["totalPullRequestReviewContributions"],
            issues=cc["totalIssueContributions"],
            repositories=data["repositories"]["totalCount"],
            followers=data["followers"]["totalCount"],
            # Contributions the viewer may not attribute to a repository.
            # Non-zero means "Include private contributions on my profile" is
            # OFF, so the public graph understates this user. Zero proves
            # nothing on its own: a user with no private work also reports 0.
            restricted=cc["restrictedContributionsCount"],
        )

        cursor, langs, stars = None, {}, 0
        while True:
            page = self.graphql(self._REPOS, login=login, cursor=cursor)["user"]["repositories"]
            for repo in page["nodes"]:
                stars += repo["stargazerCount"]
                for edge in repo["languages"]["edges"]:
                    name = edge["node"]["name"]
                    if name not in exclude_languages:
                        langs[name] = langs.get(name, 0) + edge["size"]
            if not page["pageInfo"]["hasNextPage"]:
                break
            cursor = page["pageInfo"]["endCursor"]

        s.languages = dict(sorted(langs.items(), key=lambda kv: -kv[1]))
        s.stars = stars
        s.calendar = cal
        return s
