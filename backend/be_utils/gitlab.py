import requests
import threading

class GitlabAPI:
    browse_url = None
    private_token = None

    def __init__(self, repo_url, repo_auth_key):
        self.browse_url = repo_url
        self.private_token = repo_auth_key

    def _get(self, url):
        response = requests.get(url, verify=False)
        data = response.json()
        return data, response

    def check_branch_name(self, branch_name):
        """call to gitlab api to get the list of repo branches

        :return: str[] list of all branches
        """
        data, res = self._get(
            "{}/branches/{}?private_token={}".format(self.browse_url, branch_name, self.private_token))
        return res.ok

    def get_all_branches(self):
        """call to gitlab api to get the list of repo branches

        :return: str[] list of all branches
        """
        data, _ = self._get(
            "{}/branches?private_token={}".format(self.browse_url, self.private_token))
        return [branch["name"] for branch in data]

    def get_list_files_sub_dir(self, dir_name, branch, list_of_files):
        page = 1
        fetch_pages = True
        while fetch_pages:
            last_gitlab_request = \
                self._get("{}/tree?ref={}&path={}&recursive=1&per_page=100&page={}&private_token={}" \
                        .format(self.browse_url, branch, dir_name, page, self.private_token))[0]
            if isinstance(last_gitlab_request, list):
                list_of_files += last_gitlab_request
            if not isinstance(last_gitlab_request, list) or len(last_gitlab_request) == 0:
                fetch_pages = False
            else:
                page = page + 1

    def list_files(self, dir_name, branch):
        """call to gitlab api to get the list api for directory name under browse_url

        :param str dir_name: directory name after the url
        :param str branch: branch name under the project
        :return: str[] list of files from the directory
        """
        list_of_files = []
        sub_dir_thread = []

        sub_folder_branch_list = \
                self._get("{}/tree?ref={}&path={}&private_token={}" \
                          .format(self.browse_url, branch, dir_name, self.private_token))[0]
        
        for sub_folder_dict in sub_folder_branch_list: 
            sub_folder_dir_name = sub_folder_dict.get('path', '/')
            thread = threading.Thread(target=self.get_list_files_sub_dir, args=(sub_folder_dir_name, branch, list_of_files,))
            sub_dir_thread.append(thread)
        
        for th in sub_dir_thread:   
            th.start()

        for th in sub_dir_thread:        
            th.join()

        if len(list_of_files) == 0:
            return []
        return [blob_file for blob_file in list_of_files if blob_file["type"] == "blob"]

    def get_test_last_update(self, test_path, branch):
        """call to gitlab api to get the commits of a certain test in a ceratin branch

        :return: the timestamp of the last commit
        """

        url = "{}/commits?path={}&ref_name={}&private_token={}".format(self.browse_url, test_path, branch, self.private_token)
        data, _ = self._get(url)
        if type(data) is list and len(data) > 0:
            # Extract the timestamp of the last commit
            return data[0]["committed_date"]
        return
    
    def get_file_content(self, file_path, branch):
        """Fetch the content of a file from GitLab.

        :param str file_path: Path of the file
        :param str branch: Branch name
        :return: File content as a string
        """
        url = f"{self.browse_url}/repository/files/{file_path}?ref={branch}&private_token={self.private_token}"
        data, response = self._get(url)
        if response.ok and "content" in data:
            import base64
            # Decode the base64-encoded content returned by GitLab
            return base64.b64decode(data["content"]).decode("utf-8")
        raise ValueError(f"Unable to fetch content for file: {file_path}")
