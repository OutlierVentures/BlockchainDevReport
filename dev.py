import json
import multiprocessing
import os
import re
from logger import sys
import time
from collections import Counter
from itertools import zip_longest
from os import path
import optparse
import toml
from github import Github
from joblib import Parallel, delayed
from gitTokenHelper import GithubPersonalAccessTokenHelper
from config import get_pats, remove_chain_from_config
import requests
import datetime

dir_path = path.dirname(path.realpath(__file__))


def element_wise_addition_lists(list1, list2):
    return [sum(x) for x in zip_longest(list1, list2, fillvalue=0)]


def get_single_repo_stats_json_file_path(org_then_slash_then_repo):
    return os.path.abspath("./output/" + org_then_slash_then_repo.split("/")[1] + "_single_repo_stats.json")


def get_commits(pat, org_then_slash_then_repo, page=1, year_count=1, date_since=None, date_until=None):
    url = 'https://api.github.com/repos/' + org_then_slash_then_repo + \
        '/commits?page=' + str(page) + '&per_page=100'
    if date_since:
        url += '&since=' + date_since
    if date_until:
        url += '&until=' + date_until
    r = requests.get(url=url,
                     headers={'Authorization': 'Token ' + pat})
    if r.status_code == 200:
        data = r.json()
        rate_limit_remaining = int(r.headers['X-RateLimit-Remaining'])
        total_pages = None
        if "link" in r.headers:
            pages_link = r.headers['link']
            last_page_link = pages_link.split(",")[1]
            re_match = re.search(
                'page=(.*)&per_page=100>; rel="last"', last_page_link)
            if re_match:
                total_pages = int(re_match.group(1))
        return {
            "error": None,
            "error_code": None,
            "data": data,
            "total_pages": total_pages,
            "rate_limit_remaining": rate_limit_remaining
        }
    return {
        "error": r.content,
        "error_code": r.status_code
    }


'''
FLOW
__main__ -> get_and_save_full_stats -> _read_orgs_for_chain_from_toml -> for each org:
    _get_repo_data_for_org -> _make_org_repo_list and for each repo of org:
        _get_single_repo_data
    _get_stats_for_org_from_repo_data -> for repo data of each repo of org:
        _analyse_repo_data_for_churn_and_commits_4w
    _get_historical_progress -> for repo data of each repo of org:
        _get_weekly_churn_and_commits_of_repo
    _combine_hist_data
'''


class DevOracle:

    def __init__(self, save_path: str, frequency):
        self.save_path = save_path
        self.gh_pat_helper = GithubPersonalAccessTokenHelper(get_pats())
        self.PAT = self._get_access_token()
        self.gh = Github(self.PAT)
        # churn, commit frequency
        self.frequency = frequency

    def _get_access_token(self):
        res = self.gh_pat_helper.get_access_token()
        if "token" in res and res["token"] is not None:
            return res["token"]
        print('Going to sleep since no token exists with usable rate limit')
        time.sleep(res["sleep_time_secs"])
        return self._get_access_token()

    def get_and_save_full_stats(self, chain_name: str, year_count):
        github_orgs = self._read_orgs_for_chain_from_toml(chain_name)

        stats_counter = Counter()
        hist_data = None

        for org_url in github_orgs:
            if not org_url.startswith("https://github.com/"):
                # TODO: If Gitlab repo then use Gitlab APIs
                print("%s is not a github repo...Skipping" % org_url)
                continue
            org = org_url.split("https://github.com/")[1]
            print("Fetching repo data for", org)
            org_repo_data_list = self._get_repo_data_for_org(org, year_count)
            print("Fetching stats(stargazers, forks, releases, churn_4w) for", org_url)
            stats_counter += self._get_stats_for_org_from_repo_data(
                org_repo_data_list)
            hist_data_for_org = self._get_historical_progress(
                org_repo_data_list)
            print("Combining hist data ...")
            hist_data = self._combine_hist_data(hist_data, hist_data_for_org)

        if hist_data == None or stats_counter == {}:
            remove_chain_from_config(chain_name)
            print('No data found for organisation in toml file')
            sys.exit(1)

        path_prefix = self.save_path + '/' + chain_name
        with open(path_prefix + '_stats.json', 'w') as outfile:
            outfile.write(json.dumps(dict(stats_counter)))
        with open(path_prefix + '_history.json', 'w') as outfile:
            outfile.write(json.dumps(dict(hist_data)))

    # list all the repos of a github org/user
    # Ensure chain_name is same as name of toml file
    def _read_orgs_for_chain_from_toml(self, chain_name):
        toml_file_path = path.join(dir_path, 'protocols', chain_name + '.toml')
        if not path.exists(toml_file_path):
            print(".toml file not found for %s in /protocols folder" % chain_name)
            sys.exit(1)
        try:
            with open(toml_file_path, 'r') as f:
                data = f.read()
            print("Fetching organizations for %s from toml file ..." % chain_name)
            github_orgs = toml.loads(data)['github_organizations']
            return github_orgs
        except:
            print('Could not open toml file - check formatting.')
            sys.exit(1)

    # get the data for all the repos of a github organization
    def _get_repo_data_for_org(self, org_name: str, year_count=1):
        org_repos = self._make_org_repo_list(org_name)
        forked_repos = []
        page = 1
        url = f"https://api.github.com/orgs/{org_name}/repos?type=forks&page={page}&per_page=100"
        response = requests.get(
            url, headers={'Authorization': 'Token ' + self.PAT})
        while len(response.json()) > 0:
            for repo in response.json():
                forked_repos.append(repo["full_name"])
            page += 1
            url = f"https://api.github.com/orgs/{org_name}/repos?type=forks&page={page}&per_page=100"
            response = requests.get(
                url, headers={'Authorization': 'Token ' + self.PAT})
        unforked_repos = list(set(org_repos) - set(forked_repos))
        # GitHub API can hit spam limit
        # number_of_hyperthreads = multiprocessing.cpu_count()
        number_of_hyperthreads = 1
        n_jobs = 2 if number_of_hyperthreads > 2 else number_of_hyperthreads
        print("Fetching single repo data ...")
        repo_data_list = Parallel(n_jobs=n_jobs)(delayed(
            self._get_single_repo_data)(repo, year_count) for repo in unforked_repos)
        return repo_data_list

    # given the org_name, return list of organisation repos
    def _make_org_repo_list(self, org_name: str):
        org_repos = []
        try:
            entity = self.gh.get_organization(org_name)
        except:
            entity = self.gh.get_user(org_name)
        for repo in entity.get_repos():
            org_repos.append(repo.name)
        org_repos = [org_name + '/{0}'.format(repo) for repo in org_repos]
        return org_repos

    def _get_single_repo_data(self, org_then_slash_then_repo: str, year_count: int = 1):
        try:
            out_file_name_with_path = get_single_repo_stats_json_file_path(
                org_then_slash_then_repo)
            if path.exists(out_file_name_with_path):
                with open(out_file_name_with_path, 'r') as single_repo_data_json:
                    return json.load(single_repo_data_json)

            repo_data = self._get_single_repo_data_from_api(
                org_then_slash_then_repo, year_count)
            with open(out_file_name_with_path, 'w') as single_repo_data_json:
                single_repo_data_json.write(json.dumps(dict(repo_data)))
            return repo_data
        except Exception as e:
            print(f"Exception occured while fetching single repo data {e}")
            sys.exit(1)

    # get repo data using a repo URL in the form of `org/repo`
    def _get_single_repo_data_from_api(self, org_then_slash_then_repo: str, year_count: int = 1):
        print('Fetching repo data for ', org_then_slash_then_repo)
        try:
            repo = self.gh.get_repo(org_then_slash_then_repo)
            weekly_add_del = repo.get_stats_code_frequency()
            weekly_commits = self._get_weekly_commits(
                self.PAT, org_then_slash_then_repo, year_count)
            # TODO: Remove contributor specific code
            weekly_add_del = [{"additions": code_freq_obj._rawData[1],
                               "deletions": code_freq_obj._rawData[2]} for code_freq_obj in weekly_add_del]
            contributors = [
                contributor.author.login for contributor in repo.get_stats_contributors()]
            return {
                "name": org_then_slash_then_repo,
                "repo": {
                    "stargazers_count": repo.stargazers_count,
                    "forks_count": repo.forks_count
                },
                "weekly_add_del": weekly_add_del,
                "weekly_commits": weekly_commits,
                "contributors": contributors,
                "releases": repo.get_releases().totalCount
            }
        except Exception as e:
            if e.status == 403:
                print("Token rate limit reached, switching tokens")
                PAT = self._get_access_token()
                self.gh = Github(PAT)
                return self._get_single_repo_data(org_then_slash_then_repo, year_count)
            raise e

    def _get_weekly_commits(self, pat, org_then_slash_then_repo, year_count):
        weekly_commits = []
        date_until = datetime.datetime.now()
        WEEKS_PER_YEAR = 52

        for week in range(1, WEEKS_PER_YEAR * year_count):
            curr_week_commits_count = 0
            page = 1

            # Set date since to one week from date until
            date_since = date_until - datetime.timedelta(days=6)

            date_since_formatted = date_since.strftime('%Y-%m-%dT%H:%M:%S%zZ')
            date_until_formatted = date_until.strftime('%Y-%m-%dT%H:%M:%S%zZ')
            while True:
                resp = get_commits(
                    pat,
                    org_then_slash_then_repo,
                    page,
                    year_count,
                    date_since_formatted,
                    date_until_formatted
                )
                if resp["error_code"] == 403:
                    print("Token rate limit reached, switching tokens")
                    pat = self._get_access_token()
                    continue
                if resp["error_code"]:
                    print("Error code: ", resp["error_code"])
                    raise Exception(
                        f"Error occured while fetching weekly commits for {org_then_slash_then_repo}")
                count = len(resp["data"])

                # No more commits for the curr. week range
                if count == 0:
                    break
                curr_week_commits_count += count
                page += 1

            # Update the total weekly commits count
            weekly_commits.insert(0, curr_week_commits_count)

            # Set date_until to a day before the last computed week date
            date_until = date_until - datetime.timedelta(days=7)

        return weekly_commits

    # given a list of repo_data of org, analyze for churn_4w, commits_4w, stars, releases
    def _get_stats_for_org_from_repo_data(self, org_repo_data_list):
        number_of_hyperthreads = multiprocessing.cpu_count()
        n_jobs = 2 if number_of_hyperthreads > 2 else number_of_hyperthreads
        repo_stats_list = Parallel(n_jobs=n_jobs)(
            delayed(self._analyse_repo_data_for_churn_and_commits_4w)(repo_data) for repo_data in org_repo_data_list)
        stats_counter = Counter()
        for repo_stats in repo_stats_list:
            stats_counter += Counter(repo_stats)
        sc_dict = dict(stats_counter)
        max_contributors = 0

        sc_dict['num_releases'] = 0 if 'num_releases' not in sc_dict else sc_dict['num_releases']
        # TODO: remove contributor specific data
        # FIXME find an efficient way to count distinct devs. This is a good lower bound number.
        for dictionary in repo_stats_list:
            try:
                this_contributors = dictionary['contributors']
            except:
                this_contributors = 0
            max_contributors = this_contributors if this_contributors > max_contributors else max_contributors
        # GitHub API only returns up to 100 contributors FIXME FIX THIS ====================================================================================================
        sc_dict['contributors'] = max_contributors
        sc_dict['num_releases'] = 0 if 'num_releases' not in sc_dict else sc_dict['num_releases']
        return sc_dict

    # analyse churn, commits from a git repo data for 'self.frequency' number of weeks
    # TODO: change 4w to make it more generic
    # analyses for latest 4w currently
    def _analyse_repo_data_for_churn_and_commits_4w(self, repo_data: dict):
        repo = repo_data["repo"]
        weekly_add_del = repo_data["weekly_add_del"]
        weekly_commits = repo_data["weekly_commits"]
        # TODO: remove contributor specific data
        contributors = repo_data["contributors"]
        releases = repo_data["releases"]

        churn_4w = 0
        commits_4w = 0
        if weekly_add_del and weekly_commits:
            for i in range(1, self.frequency + 1):
                try:
                    # weekly-add_del [<Week In UNIX Timestamp>, <additions>, <deletions with neg symbol>]
                    # Deletions is negative, so churn is being calculated as #additions - #deletions
                    churn_4w += (weekly_add_del[-i]["additions"] -
                                 weekly_add_del[-i]["deletions"])
                    commits_4w += weekly_commits[-i]
                except:
                    break
        # TODO: remove contributor specific data
        num_contributors = len(contributors) if contributors else 0
        stats = {
            'churn_4w': churn_4w,
            'commits_4w': commits_4w,
            'contributors': num_contributors,
            'stars': repo["stargazers_count"],
            'forks': repo["forks_count"],
            'num_releases': releases
        }
        return stats

    # given a list of repo_data for org, analyze for
    # weekly_commits and weekly_churn for all weeks till now;
    # Weekly commit, churn serve as indicators for historical progress
    def _get_historical_progress(self, org_repo_data_list: list):
        # GitHub API can hit spam limit
        number_of_hyperthreads = multiprocessing.cpu_count()
        n_jobs = 2 if number_of_hyperthreads > 2 else number_of_hyperthreads
        repo_count_list = Parallel(n_jobs=n_jobs)(
            delayed(self._get_weekly_churn_and_commits_of_repo)(repo_data) for repo_data in org_repo_data_list)
        churns = []
        commits = []
        for repo in repo_count_list:
            this_churn = repo['weekly_churn']
            this_commits = repo['weekly_commits']
            # Reverse churn and commits array to show latest week data first
            churns.append(this_churn[::-1])
            commits.append(this_commits[::-1])
        # Element wise addition of list of lists
        # Re-reverse churn and commits array to show oldesr week data first
        churns = [sum(x) for x in zip_longest(*churns, fillvalue=0)][::-1]
        commits = [sum(x) for x in zip_longest(*commits, fillvalue=0)][::-1]
        # churns = churns[-52:]
        # TODO: figure out why this assert is failing
        # assert len(churns) == len(commits)

        # Reversed weeks_ago based on the length of churn/commit weeks
        weeks_ago = list(range(len(churns)))[::-1]
        sc_dict = {
            'weekly_churn': churns,
            'weekly_commits': commits,
            'weeks_ago': weeks_ago
        }
        return sc_dict

    def _get_weekly_churn_and_commits_of_repo(self, repo_data: dict):
        org_then_slash_then_repo = repo_data["name"]
        weekly_commits = repo_data["weekly_commits"]
        weekly_add_del = repo_data["weekly_add_del"]
        try:
            # For front-end app use, combining this github API call with that for single_repo_stats would be beneficial
            weekly_churn = []
            if weekly_add_del:
                for i in range(len(weekly_add_del)):
                    # Deletions is negative
                    weekly_churn.append(
                        weekly_add_del[i]["additions"] - weekly_add_del[i]["deletions"])
            stats = {
                'weekly_churn': weekly_churn,
                'weekly_commits': weekly_commits,
                'repo': org_then_slash_then_repo
            }
            return stats
        except Exception as e:
            print(e)
            stats = {
                'weekly_churn': [],
                'weekly_commits': weekly_commits,
                'repo': org_then_slash_then_repo
            }
            return stats

    # Do element wise addition for `weekly_churn`, `weekly_commits`, `weeks_ago` lists
    # to get the cumulative historical data for a given chain
    def _combine_hist_data(self, cumulative_hist_data, hist_data_for_org):
        if cumulative_hist_data is None:
            cumulative_hist_data = hist_data_for_org
        else:
            cumulative_hist_data["weekly_churn"] = \
                element_wise_addition_lists(
                    cumulative_hist_data["weekly_churn"][::-1],
                    hist_data_for_org["weekly_churn"][::-1]
            )[::-1]
            cumulative_hist_data["weekly_commits"] = \
                element_wise_addition_lists(
                    cumulative_hist_data["weekly_commits"][::-1],
                    hist_data_for_org["weekly_commits"][::-1]
            )[::-1]
            cumulative_hist_data["weeks_ago"] = \
                element_wise_addition_lists(
                    cumulative_hist_data["weeks_ago"][::-1],
                    hist_data_for_org["weeks_ago"][::-1]
            )[::-1]
        return cumulative_hist_data


if __name__ == '__main__':
    p = optparse.OptionParser()
    p.add_option('--frequency', type='int', dest='frequency',
                 help='Enter churn, commit frequency')

    options, arguments = p.parse_args()
    if not options.frequency:
        options.frequency = 4

    years_count = int(sys.argv[2]) if sys.argv[2] else 1

    do = DevOracle('./output', options.frequency)
    do.get_and_save_full_stats(sys.argv[1], years_count)
