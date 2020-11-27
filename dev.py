import json
import multiprocessing
import os
import sys
from collections import Counter
from itertools import zip_longest
from os import path
import optparse
import toml
from github import Github
from joblib import Parallel, delayed
from itertools import zip_longest
from collections import Counter
from itertools import zip_longest
from os import path
import toml
from github import Github
from joblib import Parallel, delayed

dir_path = path.dirname(path.realpath(__file__))

def element_wise_addition_lists(list1, list2):
    return [sum(x) for x in zip_longest(list1, list2, fillvalue=0)]


class DevOracle:

    def __init__(self, save_path: str, PAT, frequency):
        self.save_path = save_path
        self.gh = Github(PAT)
        # churn, commit frequency
        self.frequency = frequency
    
    # get repo data using a repo URL in the form of `org/repo`
    def _get_single_repo_data(self, org_then_slash_then_repo: str):
        try:
            repo = self.gh.get_repo(org_then_slash_then_repo)
            weekly_add_del = repo.get_stats_code_frequency()
            weekly_commits = repo.get_stats_participation().all
            # TODO: Remove contributor specific code
            contributors = repo.get_stats_contributors()
            releases = repo.get_releases()
            return {
                "name": org_then_slash_then_repo,
                "repo": repo,
                "weekly_add_del": weekly_add_del,
                "weekly_commits": weekly_commits,
                "contributors": contributors,
                "releases": releases
            }
        except:
            print('Could not find data for ' + org_then_slash_then_repo)
            return {}

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
    
    def get_and_save_full_stats(self, chain_name: str):
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
            org_repo_data_list = self._get_repo_data_for_org(org)
            print("Fetching stats(stargazers, forks, releases, churn_4w) for", org_url)
            stats_counter += self._get_stats_for_org_from_repo_data(org_repo_data_list)
            hist_data_for_org = self._get_historical_progress(org_repo_data_list)
            print("Combining hist data ...")
            hist_data = self._combine_hist_data(hist_data, hist_data_for_org)

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
                    weekly_churn.append(weekly_add_del[i]._rawData[1] - weekly_add_del[i]._rawData[2])
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
    
    # get the data for all the repos of a github organization
    def _get_repo_data_for_org(self, org_name: str):
        org_repos = self._make_org_repo_list(org_name)
        # GitHub API can hit spam limit
        number_of_hyperthreads = multiprocessing.cpu_count()
        n_jobs = 2 if number_of_hyperthreads > 2 else number_of_hyperthreads
        repo_data_list = Parallel(n_jobs=n_jobs)(delayed(self._get_single_repo_data)(repo) for repo in org_repos)
        return repo_data_list

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
                    churn_4w += (weekly_add_del[-i]._rawData[1] - weekly_add_del[-i]._rawData[2])
                    commits_4w += weekly_commits[-i]
                except:
                    break
        # TODO: remove contributor specific data
        num_contributors = len(contributors) if contributors else 0
        stats = {
            'churn_4w': churn_4w,
            'commits_4w': commits_4w,
            'contributors': num_contributors,
            'stars': repo.stargazers_count,
            'forks': repo.forks_count,
            'num_releases': releases.totalCount
        }
        return stats

if __name__ == '__main__':
    p = optparse.OptionParser()
    p.add_option('--PAT', type='string', dest='PAT', help='GitHub Personal Access Token')
    p.add_option('--frequency', type='int', dest='frequency', help='Enter churn, commit frequency')

    options, arguments = p.parse_args()
    if not options.PAT:
        print('This requires a GitHub PAT to do anything interesting.')
        sys.exit(1)
    if not options.frequency:
        options.frequency = 4
    
    do = DevOracle('./', options.PAT, options.frequency)
    do.get_and_save_full_stats(sys.argv[1])
