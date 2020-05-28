import os, sys, requests

# Python client only allows the first 100 contributors to be returned, so use vanilla HTTP to get contributors
class Contributors:

    def __init__(self, save_path : str):
        self.save_path = save_path
        if 'PAT' in os.environ:
            self.pat = os.environ.get('PAT')
        else:
            self.pat = 'fff'


    def get_contributors(self, org_then_slash_then_repo : str):
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
                except Exception as e:
                    print(e)
            page += 1
            
        print(contributors)
        return contributors

if __name__ == '__main__':
    c = Contributors('./')
    c.get_contributors(sys.argv[1])

