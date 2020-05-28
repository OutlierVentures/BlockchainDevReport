import os, sys, requests, datetime, toml, json

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
            if type(data) == dict:
                return [] # Repo doesn't exist
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
            data = requests.get('https://api.github.com/repos/' + org_then_slash_then_repo + '/commits?page='
                                + str(page) + '&per_page=100', headers = {'Authorization': 'Token ' + self.pat}).json()
            if type(data) == dict:
                return [] # Repo doesn't exist
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
        #print(len(deduplicated_contributors))
        return deduplicated_contributors

    def get_year_contr_from_toml(self, toml_file : str):
        out_file_name = toml_file.replace('.toml', '') + '.json'
        if not os.path.exists(out_file_name):
            with open(out_file_name, 'w') as outfile:
                json.dump([], outfile)
        try:
            with open(toml_file, 'r') as f:
                data = f.read()
            repos = toml.loads(data)['repo']
        except:
            print('Could not open toml file - check formatting.')
            sys.exit(1)
        # Don't thread this - API limit
        for repo in repos:
            if 'url' in repo:
                url = repo['url'].lower()
                org_then_slash_then_repo = url.split('github.com/')[1]
                if org_then_slash_then_repo[-1] == '/':
                    org_then_slash_then_repo = org_then_slash_then_repo[:-1]
                print('Analysing ' + org_then_slash_then_repo)
                contributors = self.get_contributors_in_last_year(org_then_slash_then_repo)
                # Save progress in case of failure
                try:
                    with open(out_file_name) as json_file:
                        data = json.load(json_file)
                    data.extend(contributors)
                    with open(out_file_name, 'w') as outfile:
                        json.dump(data, outfile)
                except Exception as e:
                    print(e)
                    sys.exit(1)
        try:
            with open(out_file_name) as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(e)
            sys.exit(1)
        deduplicated_contributors = list(set(data))
        print('Total active developers in the past year: ' + str(len(deduplicated_contributors)))
        with open(out_file_name, 'w') as outfile:
            json.dump(deduplicated_contributors, outfile)
        return deduplicated_contributors


# Get last commit from JSON response, and create one list of all active in the past year, and one list of all contributors ever
# Write to file every n repos + repos viewed to not lose progress

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 contr.py [INPUTFILE.TOML]')
        sys.exit(1)
    c = Contributors('./')
    c.get_year_contr_from_toml(sys.argv[1])

