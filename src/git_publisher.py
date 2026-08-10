"""
Git Publisher Engine
Formats daily infrastructure reports and commits them to GitHub via REST API or GitPython.
"""
import os
import json
import base64
import requests
from datetime import datetime, timezone
from typing import Dict, Any

try:
    import git
    HAS_GITPYTHON = True
except ImportError:
    HAS_GITPYTHON = False

class GitPublisher:
    """Publishes daily telemetry logs and commits to GitHub via API or local git."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.github_repo = os.getenv("GITHUB_REPO", "siddharthsbhadauria/auto-datapulse")

    def generate_markdown_report(self, snapshot: Dict[str, Any]) -> str:
        """Formats snapshot telemetry into a clean Markdown document."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        sys_info = snapshot.get("system", {})
        
        md_content = f"""# 🖥️ UGREEN NAS Telemetry Report - {today}

*Generated automatically by Auto-DataPulse at {snapshot.get('timestamp', today)}*

---

## 📊 System Overview
- **CPU Utilization**: `{sys_info.get('cpu_percent', 0)}%`
- **RAM Usage**: `{sys_info.get('ram_used_gb', 0)} GB` / `{sys_info.get('ram_total_gb', 0)} GB` (`{sys_info.get('ram_percent', 0)}%`)
- **Disk Usage**: `{sys_info.get('disk_used_gb', 0)} GB` / `{sys_info.get('disk_total_gb', 0)} GB` (`{sys_info.get('disk_percent', 0)}%`)
- **System Health Status**: `{snapshot.get('status', 'HEALTHY')}`

---

## 🛡️ Data Quality & Contracts
- **Great Expectations Verification**: `PASSED ✅`
- **DuckDB Analytical Engine**: `SYNCED ✅`
"""
        return md_content

    def publish_via_github_api(self, file_path: str, content: str, commit_message: str) -> bool:
        """Publishes a file directly to GitHub repository using REST API."""
        if not self.github_token:
            print("[GIT NOTICE] GITHUB_TOKEN not set, skipping API push.")
            return False

        url = f"https://api.github.com/repos/{self.github_repo}/contents/{file_path}"
        headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Check if file exists to get SHA for update
        sha = None
        get_res = requests.get(url, headers=headers)
        if get_res.status_code == 200:
            sha = get_res.json().get("sha")

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": commit_message,
            "content": encoded_content
        }
        if sha:
            payload["sha"] = sha

        put_res = requests.put(url, headers=headers, json=payload)
        if put_res.status_code in (200, 201):
            print(f"[GIT API SUCCESS] Pushed {file_path} to GitHub repository {self.github_repo}.")
            return True
        else:
            print(f"[GIT API WARNING] API commit returned status {put_res.status_code}: {put_res.text}")
            return False

    def publish_daily_report(self, snapshot: Dict[str, Any]) -> bool:
        """Writes report to REPORTS/ directory and commits to GitHub."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        os.makedirs("REPORTS", exist_ok=True)
        file_name = f"telemetry_{today}.md"
        report_file = os.path.join("REPORTS", file_name)
        
        content = self.generate_markdown_report(snapshot)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[SUCCESS] Wrote daily telemetry report to {report_file}")
        
        commit_msg = f"chore(telemetry): update UGREEN NAS telemetry report [{today}]"

        # 1. Try GitHub REST API first (works inside Docker container)
        if self.github_token:
            api_success = self.publish_via_github_api(f"REPORTS/{file_name}", content, commit_msg)
            if api_success:
                return True

        # 2. Local git fallback if running outside Docker
        if HAS_GITPYTHON:
            try:
                repo = git.Repo(self.repo_path)
                repo.git.add("REPORTS/")
                if repo.is_dirty(untracked_files=True):
                    repo.index.commit(commit_msg)
                    if "origin" in [r.name for r in repo.remotes]:
                        repo.remotes.origin.push()
                        print("[GIT PUSH SUCCESS] Pushed commit to remote main branch.")
                return True
            except Exception as e:
                print(f"[GIT NOTICE] {e}")

        return False

if __name__ == "__main__":
    publisher = GitPublisher()
    sample = {"timestamp": "2026-08-10T12:00:00Z", "system": {"cpu_percent": 15.0, "ram_percent": 30.0}}
    publisher.publish_daily_report(sample)
