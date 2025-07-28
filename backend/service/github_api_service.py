import requests
import json
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import os
from bs4 import BeautifulSoup


class GitHubAPIService:
    """
    Service class responsible for communication with the GitHub API
    """

    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API service

        Args:
            token (Optional[str]): GitHub Personal Access Token
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = self._get_headers()

    def _get_headers(self) -> Dict[str, str]:
        """Generate headers for GitHub API requests."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-Market-Service",
        }

        if self.token:
            headers["Authorization"] = f"token {self.token}"

        return headers

    def get_repo_info(self, github_link: str) -> Optional[Dict[str, str]]:
        """
        Extract repository information from a GitHub URL.

        Args:
            github_link (str): GitHub repository URL

        Returns:
            Optional[Dict[str, str]]: {'owner': 'username', 'repo': 'repository_name'}
        """
        try:
            parsed = urlparse(github_link)
            path_parts = parsed.path.strip("/").split("/")

            if len(path_parts) >= 2:
                return {"owner": path_parts[0], "repo": path_parts[1]}
        except Exception as e:
            print(f"Error parsing GitHub URL: {str(e)}")

        return None

    def get_repo_files(
        self, owner: str, repo: str, path: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Get the list of files in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            path (str): Path (default: root)

        Returns:
            List[Dict[str, Any]]: List of files
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get repo files: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error getting repo files: {str(e)}")
            return []

    def get_file_content(self, owner: str, repo: str, file_path: str) -> Optional[str]:
        """
        Get the content of a file in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            file_path (str): File path

        Returns:
            Optional[str]: File content
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                import base64

                content = response.json().get("content", "")
                return base64.b64decode(content).decode("utf-8")
            else:
                print(f"Failed to get file content: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error getting file content: {str(e)}")
            return None

    def get_readme_content(self, owner: str, repo: str) -> Optional[str]:
        """
        Get the content of README.md in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name

        Returns:
            Optional[str]: README.md content
        """
        try:
            # Try README.md in the main branch
            readme_content = self.get_file_content(owner, repo, "README.md")
            if readme_content:
                return readme_content

            # Try README.md in the master branch
            url = f"{self.base_url}/repos/{owner}/{repo}/readme"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                import base64

                content = response.json().get("content", "")
                return base64.b64decode(content).decode("utf-8")

            return None

        except Exception as e:
            print(f"Error getting README content: {str(e)}")
            return None

    def search_repo_files(
        self, owner: str, repo: str, patterns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search for files matching specific patterns.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            patterns (List[str]): File patterns to search

        Returns:
            List[Dict[str, Any]]: List of matching files
        """
        try:
            files = self.get_repo_files(owner, repo)
            matched_files = []

            for file_info in files:
                file_name = file_info.get("name", "")

                for pattern in patterns:
                    if re.match(pattern, file_name, re.IGNORECASE):
                        matched_files.append(file_info)
                        break

            return matched_files

        except Exception as e:
            print(f"Error searching repo files: {str(e)}")
            return []

    def get_repo_info_api(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """
        Get repository information via GitHub API.

        Args:
            owner (str): Repository owner
            repo (str): Repository name

        Returns:
            Optional[Dict[str, Any]]: Repository information
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get repo info: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error getting repo info: {str(e)}")
            return None

    def get_repo_languages(self, owner: str, repo: str) -> List[str]:
        """
        Get the list of programming languages used in the repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name

        Returns:
            List[str]: List of languages
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return list(response.json().keys())
            else:
                print(f"Failed to get repo languages: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error getting repo languages: {str(e)}")
            return []

    def get_repo_topics(self, owner: str, repo: str) -> List[str]:
        """
        Get the list of topics in the repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name

        Returns:
            List[str]: List of topics
        """
        try:
            url = f"{self.base_url}/repos/{owner}/{repo}/topics"
            headers = self.headers.copy()
            headers["Accept"] = "application/vnd.github.mercy-preview+json"

            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                return response.json().get("names", [])
            else:
                print(f"Failed to get repo topics: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error getting repo topics: {str(e)}")
            return []

    def scrape_repo_page(self, github_link: str) -> Optional[str]:
        """
        Scrape the GitHub repository page.

        Args:
            github_link (str): GitHub repository URL

        Returns:
            Optional[str]: Page HTML content
        """
        try:
            response = requests.get(github_link)

            if response.status_code == 200:
                return response.text
            else:
                print(f"Failed to scrape repo page: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error scraping repo page: {str(e)}")
            return None

    def get_raw_file_content(
        self, owner: str, repo: str, file_path: str, branch: str = "main"
    ) -> Optional[str]:
        """
        Get the raw content of a file in a GitHub repository.

        Args:
            owner (str): Repository owner
            repo (str): Repository name
            file_path (str): File path
            branch (str): Branch (default: main)

        Returns:
            Optional[str]: File content
        """
        try:
            url = (
                f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
            )
            response = requests.get(url)

            if response.status_code == 200:
                return response.text
            else:
                # If not the main branch, try the master branch
                if branch == "main":
                    return self.get_raw_file_content(owner, repo, file_path, "master")
                else:
                    print(f"Failed to get raw file content: {response.status_code}")
                    return None

        except Exception as e:
            print(f"Error getting raw file content: {str(e)}")
            return None

    def check_rate_limit(self) -> Dict[str, Any]:
        """
        Check the status of GitHub API rate limits.

        Returns:
            Dict[str, Any]: Rate limit information
        """
        try:
            url = f"{self.base_url}/rate_limit"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to check rate limit: {response.status_code}")
                return {}

        except Exception as e:
            print(f"Error checking rate limit: {str(e)}")
            return {}

    def is_authenticated(self) -> bool:
        """
        Check GitHub API authentication status.

        Returns:
            bool: Authentication status
        """
        try:
            url = f"{self.base_url}/user"
            response = requests.get(url, headers=self.headers)

            return response.status_code == 200

        except Exception as e:
            print(f"Error checking authentication: {str(e)}")
            return False
