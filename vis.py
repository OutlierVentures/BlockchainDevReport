import seaborn as sns, pandas as pd, json
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Visualize:

    def __init__(self):
        self.chains = ['fetchai', 'ethereum']
        end = datetime.now()
        start = datetime.now() - relativedelta(years = 1)
        date_index = pd.date_range(start, end, freq = 'W')
        self.df = pd.DataFrame({'date': date_index})

    def load(self, name : str):
        with open(name + '_history.json') as json_file:
            data = json.load(json_file)
        self.df[name] = data['weekly_commits']

    def plot(self):
        sns.set(style="darkgrid")
        df = self.df.melt('date', var_name = 'protocol',  value_name = 'commits')
        fig = sns.lineplot(x = "date", y = "commits", hue = 'protocol', data = df)
        fig.get_figure().savefig('commits.png')
    
    def run(self):
        for chain in self.chains:
            self.load(chain)
        self.plot()


if __name__ == '__main__':
    v = Visualize()
    v.run()