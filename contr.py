import os, sys, requests, datetime

# Python client only allows the first 100 contributors to be returned, so use vanilla HTTP to get contributors
class Contributors:

    def __init__(self, save_path : str):
        self.save_path = save_path
        if 'PAT' in os.environ:
            self.pat = os.environ.get('PAT')
        else:
            self.pat = 'fff'


    def get_total_contributors(self, org_then_slash_then_repo : str):
        data = ['exists']
        page = 1
        contributors = []
        while len(data):
            print(page)
            data = requests.get('https://api.github.com/repos/' + org_then_slash_then_repo + '/contributors?page='
                                + str(page) + '&per_page=100', headers = {'Authorization': 'Token ' + self.pat}).json()
            for item in data:
                try:
                    contributors.append(item['login'])
                    print(item)
                except Exception as e:
                    print(e)
                    sys.exit(1)
            page += 1
            
        print(len(contributors))
        return contributors


    def get_contributors_in_last_year(self, org_then_slash_then_repo : str):
        # Commits are not chronological, so need to pull all and filter
        data = ['exists']
        page = 1
        commits = []
        while len(data):
            print(page)
            data = requests.get('https://api.github.com/repos/' + org_then_slash_then_repo + '/commits?page='
                                + str(page) + '&per_page=100', headers = {'Authorization': 'Token ' + self.pat}).json()
            try:
                commits.extend(data)
            except Exception as e:
                print(e)
                sys.exit(1)
            page += 1
        # Remove older commits
        year_ago = datetime.datetime.now() - datetime.timedelta(days = 365) # Use 366 for leap years
        contributors = []
        for item in commits:
            try:
                date_string = item['commit']['author']['date']
                date = datetime.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
                if date > year_ago:
                    if item['author']: # Can be null (user not logged in)
                        contributors.append(item['author']['login'])
            except Exception as e:
                print(e)
                sys.exit(1)
        # De-duplicate commiters
        deduplicated_contributors = list(set(contributors))    
        print(len(deduplicated_contributors))
        return deduplicated_contributors



# Get last commit from JSON response, and create one list of all active in the past year, and one list of all contributors ever
# Write to file every n repos + repos viewed to not lose progress

if __name__ == '__main__':
    c = Contributors('./')
    c.get_contributors_in_last_year(sys.argv[1])

