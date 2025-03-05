import requests
from backend.be_utils.git.git import AbstractAPI

class GithubAPI(AbstractAPI):
    def __init__(self, repo_owner, repo_name, auth_token):
        base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        repo_url = f"https://github.com/{repo_owner}/{repo_name}"
        super().__init__(base_url, repo_url, {"Authorization": f"token {auth_token}"})

    def _get_headers(self):
        return self.auth

    def _parse_response(self, response):
        """GitHub always returns JSON, so we just return parsed JSON."""
        try:
            return response.json(), response.headers
        except requests.exceptions.JSONDecodeError:
            raise ValueError("GitHub API returned an invalid JSON response.")
        
    def _build_list_files_url(self, branch):
        """Return the full repository tree for a specific branch."""
        return self._build_url(f"git/trees/{branch}", {"recursive": 1})  

    def _build_file_content_url(self, file_path_encoded, branch):
        return self._build_url(f"contents/{file_path_encoded}", {"ref": branch})

    def _decode_file_content(self, data):
        import base64
        return base64.b64decode(data.json()["content"]).decode("utf-8")

    def list_files(self, dir_name, branch):
        """Retrieve all files from a specific directory or the entire repository, handling errors properly."""
        url = self._build_list_files_url(branch)
        response, _ = self._get(url, headers=self._get_headers())
        if isinstance(response, dict) and "error" in response:
            raise ValueError(response["error"])

        if not isinstance(response, dict) or "tree" not in response:
           raise ValueError("Invalid response format or missing 'tree' key.")

        if not dir_name:
            return [item for item in response["tree"] if self._is_valid_file(item)]

        filtered_files = [
            item for item in response["tree"]
            if item["path"].startswith(f"{dir_name}/") and self._is_valid_file(item)
        ]

        if filtered_files:
            return filtered_files
        else:
            raise ValueError(f"❌ No files found in the specified directory: {dir_name}")
