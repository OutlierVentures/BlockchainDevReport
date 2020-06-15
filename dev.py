from joblib import Parallel, delayed
from itertools import zip_longest
from collections import Counter
from github import Github
import os, sys, shutil, multiprocessing, json


class DevOracle:

    def __init__(self, save_path : str):
        self.save_path = save_path
        if 'PAT' in os.environ:
            self.gh = Github(os.environ.get('PAT'))
        else:
            self.gh = Github()
    
    def single_repo_stats(self, org_then_slash_then_repo : str):
        try:
            repo = self.gh.get_repo(org_then_slash_then_repo)
            weekly_add_del = repo.get_stats_code_frequency()
            weekly_commits = repo.get_stats_participation().all
            contributors = repo.get_stats_contributors()
            releases = repo.get_releases()
        except:
            print('Could not find data for ' + org_then_slash_then_repo)
            return {}
        churn_4w = 0
        commits_4w = 0
        if weekly_add_del and weekly_commits:
            for i in range(1, 5):
                try:
                    # Deletions is negative
                    churn_4w += (weekly_add_del[-i]._rawData[1] - weekly_add_del[-i]._rawData[2])
                    commits_4w += weekly_commits[-i]
                except:
                    break
        num_contributors = len(contributors) if contributors else 0            
        stats = {
            'churn_4w': churn_4w,
            'commits_4w': commits_4w,
            'contributors': num_contributors,
            'stars': repo.stargazers_count,
            'forks': repo.forks_count,
            'num_releases': releases.totalCount
        }
        ''' FUTURE USE: dev distribution. FIXME efficient adding of these dicts for org_stats()
        contributor_distribution = []
        for dev in contributors:
            this_dev_churn = 0
            for week in dev.weeks:
                this_dev_churn += week.a + week.d
            this_dev = {
                'name': dev.author.login,
                'commits': dev.total,
                'churn': this_dev_churn
            }
            contributor_distribution.append(this_dev)
        ''' 
        return stats#, contributor_distribution

    def org_stats(self, org_name : str):
        org_repos = self.make_org_repo_list(org_name)
        # GitHub API can hit spam limit
        number_of_hyperthreads = multiprocessing.cpu_count()
        n_jobs = 2 if number_of_hyperthreads > 2 else number_of_hyperthreads
        repo_count_list = Parallel(n_jobs = n_jobs)(delayed(self.single_repo_stats)(repo) for repo in org_repos)
        stats_counter = Counter()
        for repo_stats in repo_count_list:
            stats_counter += Counter(repo_stats)
        sc_dict = dict(stats_counter)
        max_contributors = 0
        # FIXME find an efficient way to count distinct devs. This is a good lower bound number.
        for dictionary in repo_count_list:
            try:
                this_contributors = dictionary['contributors']
            except:
                this_contributors = 0
            max_contributors = this_contributors if this_contributors > max_contributors else max_contributors
        # GitHub API only returns up to 100 contributors FIXME FIX THIS ====================================================================================================
        sc_dict['contributors'] = max_contributors
        sc_dict['num_releases'] = 0 if 'num_releases' not in sc_dict else sc_dict['num_releases']
        return sc_dict

    def make_org_repo_list(self, org_name : str):
        org_repos = []
        try:
            entity = self.gh.get_organization(org_name)
        except:
            entity = self.gh.get_user(org_name)
        for repo in entity.get_repos():
            org_repos.append(repo.name)
        org_repos = [org_name + '/{0}'.format(repo) for repo in org_repos]
        return org_repos
    
    def get_and_save_full_stats(self, github_org : str):
        stats = self.org_stats(github_org)
        hist = self.historical_progress(github_org)
        path_prefix = self.save_path + '/' + github_org
        with open(path_prefix + '_stats.json', 'w') as outfile:
            outfile.write(json.dumps(stats))
        with open(path_prefix + '_history.json', 'w') as outfile:
            outfile.write(json.dumps(hist))

    def get_churn_and_commits(self, org_then_slash_then_repo : str):
        try:
            # For front-end app use, combining this github API call with that for single_repo_stats would be beneficial
            repo = self.gh.get_repo(org_then_slash_then_repo)
            weekly_commits = repo.get_stats_participation().all
            weekly_add_del = repo.get_stats_code_frequency()
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
                'weekly_churn': weekly_churn,
                'weekly_commits': weekly_commits,
                'repo': org_then_slash_then_repo
            }
            return stats

    def historical_progress(self, github_org : str):
        org_repos = self.make_org_repo_list(github_org)
        # GitHub API can hit spam limit
        number_of_hyperthreads = multiprocessing.cpu_count()
        n_jobs = 2 if number_of_hyperthreads > 2 else number_of_hyperthreads
        repo_count_list = Parallel(n_jobs = n_jobs)(delayed(self.get_churn_and_commits)(repo) for repo in org_repos)
        churns = []
        commits = []
        for repo in repo_count_list:
            this_churn = repo['weekly_churn']
            this_commits = repo['weekly_commits']
            churns.append(this_churn[::-1])
            commits.append(this_commits[::-1])
        churns = [sum(x) for x in zip_longest(*churns, fillvalue = 0)][::-1]
        commits = [sum(x) for x in zip_longest(*commits, fillvalue = 0)][::-1]
        #churns = churns[-52:]
        #assert len(churns) == len(commits)
        weeks_ago = list(range(len(churns)))[::-1]
        sc_dict = {
            'weekly_churn': churns,
            'weekly_commits': commits,
            'weeks_ago': weeks_ago
        }
        return sc_dict
    

if __name__ == '__main__':
    if 'PAT' not in os.environ:
        print('This requires a GitHub PAT to do anything interesting.')
        print('Usage: python3 dev.py [GITHUB_ORG]]')
        sys.exit(1)
    if len(sys.argv) != 2 or '/' in sys.argv[1]:
        print('Usage: python3 dev.py [GITHUB_ORG]]')
        sys.exit(1)
    do = DevOracle('./')
    do.get_and_save_full_stats(sys.argv[1])
