import seaborn as sns, pandas as pd, json
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Visualize:

    def __init__(self):
        self.chains = ['fetchai', 'ethereum', 'bitcoin']
        end = datetime.now()
        start = datetime.now() - relativedelta(years = 1)
        date_index = pd.date_range(start, end, freq = 'W')
        self.commits = pd.DataFrame({'Date': date_index})
        self.churn = pd.DataFrame({'Date': date_index})

    def load(self, name : str):
        with open(name + '_history.json') as json_file:
            data = json.load(json_file)
        self.commits[name] = data['weekly_commits']
        self.churn[name] = data['weekly_churn'][-52:]

    def plot_commits(self):
        # Compute a 4-period MA to smooth data
        for chain in self.chains:
            self.commits[chain] = self.commits[chain].rolling(4).mean()
        df1 = self.commits.melt('Date', var_name = 'Protocol',  value_name = 'Commits')
        fig1 = sns.lineplot(x = "Date", y = "Commits", hue = 'Protocol', data = df1)
        fig1.get_figure().savefig('commits.png')
        fig1.clear()
        
    def plot_churn(self):
        # Compute a 4-period MA to smooth data
        for chain in self.chains:
            self.churn[chain] = self.churn[chain].rolling(4).mean()
        df2 = self.churn.melt('Date', var_name = 'Protocol',  value_name = 'Churn')
        fig2 = sns.lineplot(x = "Date", y = "Churn", hue = 'Protocol', data = df2)
        fig2.set_yscale("log") # Large additions e.g. opening a repo makes the linear data hard to interpret
        fig2.get_figure().savefig('churn.png')
        fig2.clear()
    
    def run(self):
        for chain in self.chains:
            self.load(chain)
        sns.set(style="darkgrid")
        self.plot_churn()
        self.plot_commits()
        


if __name__ == '__main__':
    v = Visualize()
    v.run()