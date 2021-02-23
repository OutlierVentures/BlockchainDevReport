# -*- coding: utf-8 -*-

import asyncio
import json
from logger import sys
from os import path, remove, listdir
import csv
import requests
import toml
from gitTokenHelper import GithubPersonalAccessTokenHelper
from config import get_pats

dir_path = path.dirname(path.realpath(__file__))

class GitStats:
    def __init__(self, save_path: str):
        self.save_path = save_path
        # TODO: fix this to be an array
        self.gh_pat_helper = GithubPersonalAccessTokenHelper(get_pats())

    async def _get_access_token(self):
        res = self.gh_pat_helper.get_access_token()
        if "token" in res and res["token"] is not None:
            return res["token"]
        print('Going to sleep since no token exists with usable rate limit')
        await asyncio.sleep(res["sleep_time_secs"])
        return await self._get_access_token()

    # list all the repos of a protocol from toml 
    # Includes all the core github org/user repos and the repo urls listed in toml
    # Ensure protocol is same as name of toml file
    async def get_repos_for_protocol_from_toml(self, protocol):
        pat = await self._get_access_token()
        repos = set()
        toml_file_path = path.join(dir_path, 'protocols', protocol + '.toml')
        if not path.exists(toml_file_path):
            print(".toml file not found for %s in /protocols folder" % chain_name)
            sys.exit(1)
        try:
            with open(toml_file_path, 'r') as f:
                data = f.read()
            github_orgs = toml.loads(data)['github_organizations']
            repos_in_toml = toml.loads(data)['repo']
        except:
            print('Could not open toml file - check formatting!!')
            sys.exit(1)
        stars = 0
        forks = 0
        watchers = 0
        releases = 0
        for org in github_orgs:
            if not org.lower().startswith("https://github.com/"):
                continue
            org_name = org.split('https://github.com/')[1]
            try:
                # Get all repos 
                all_org_repos = []
                page = 1
                url = f"https://api.github.com/orgs/{org_name}/repos?page={page}&per_page=100"
                response = requests.get(url, headers={'Authorization': 'Token ' + pat})
                while len(response.json()) > 0:
                    for repo in response.json():
                        repo_details = {
                            "full_name": repo["full_name"],
                            "forks_count": repo["forks_count"],
                            "stargazers_count": repo["stargazers_count"],
                            "watchers_count": repo["watchers_count"],
                        }
                        all_org_repos.append(repo_details)
                    page += 1
                    url = f"https://api.github.com/orgs/{org_name}/repos?page={page}&per_page=100"
                    response = requests.get(url, headers={'Authorization': 'Token ' + pat})
                # Get forked repos
                forked_org_repos = []
                page = 1
                url = f"https://api.github.com/orgs/{org_name}/repos?type=forks&page={page}&per_page=100"
                response = requests.get(url, headers={'Authorization': 'Token ' + pat})
                while len(response.json()) > 0:
                    for repo in response.json():
                        repo_details = {
                            "full_name": repo["full_name"],
                            "forks_count": repo["forks_count"],
                            "stargazers_count": repo["stargazers_count"],
                            "watchers_count": repo["watchers_count"],
                        }
                        forked_org_repos.append(repo_details)
                    page += 1
                    url = f"https://api.github.com/orgs/{org_name}/repos?type=forks&page={page}&per_page=100"
                    response = requests.get(url, headers={'Authorization': 'Token ' + pat})
                # Find difference
                # unforked_repos = []
                for repo in all_org_repos:
                    if repo not in forked_org_repos:
                        page = 1
                        stars += repo["stargazers_count"]
                        forks += repo["forks_count"]
                        watchers += repo["watchers_count"]
                        # Getting releases
                        org_and_repo_name = repo["full_name"]
                        url = f"https://api.github.com/repos/{org_and_repo_name}/releases?page={page}&per_page=100"
                        response = requests.get(url, headers={'Authorization': 'Token ' + pat})
                        while len(response.json()) > 0:
                            releases += len(response.json())
                            page += 1
                            url = f"https://api.github.com/repos/{org_and_repo_name}/releases?page={page}&per_page=100"
                            response = requests.get(url, headers={'Authorization': 'Token ' + pat}) 
            except:
                # Core org is not org but a user
                # Get repos of user
                print("Exception")
                url = f"https://api.github.com/users/{org_name}/repos"
                response = requests.get(url, headers={'Authorization': 'Token ' + pat})
                for repo in response.json():
                    repos.add(repo["full_name"].lower())
        print("\nProtocol: ", protocol)
        print("Stars: ", stars)
        print("Forks: ", forks)
        print("Watchers: ", watchers)
        print("Releases: ", releases)
        with open('./res/git-stats.csv', 'a+', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([protocol, stars, forks, watchers, releases])


if __name__ == '__main__':
    if not (len(sys.argv) == 2):
        print('Usage: python3 git-stats.py [INPUTFILE.TOML]')
        sys.exit(1)
    gitstats = GitStats('./output')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(gitstats.get_repos_for_protocol_from_toml(sys.argv[1]))
