import seaborn as sns
import pandas as pd
import json
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from os import path
import shutil
import glob
from config import get_chain_names, get_chain_targets

dir_path = path.dirname(path.realpath(__file__))


class Visualize:

    def __init__(self):
        self.chains = get_chain_names().split(" ")
        self.target_names = get_chain_targets().split(", ")
        self.xaxis = ['Jan 2020', 'Feb 2020', 'Mar 2020', 'Apr 2020', 'May 2020',
                      'Jun 2020', 'Jul 2020', 'Aug 2020', 'Sep 2020', 'Oct 2020', 'Nov 2020', 'Dec 2020']
        end = datetime.now()
        start = datetime.now() - relativedelta(years=1)
        date_index = pd.date_range(start, end, freq='W')
        if len(date_index) > 52:
            date_index = date_index.drop(date_index[-1])
        self.commits = pd.DataFrame({'Date': date_index})
        self.churn = pd.DataFrame({'Date': date_index})
        for chain in self.chains:
            output_path = path.join(
                dir_path, 'output', chain + '_history.json')
            try:
                with open(output_path) as json_file:
                    data = json.load(json_file)
                self.commits[chain] = data['weekly_commits']
                self.churn[chain] = data['weekly_churn'][-52:]
            except:
                print('Not found history output for ' + chain +
                      ', please remove from config and rerun')
        sns.set(style="darkgrid")
        sns.set(rc={'figure.figsize': (24, 14)})

    def prep_code(self, commits_or_churn: str = 'commits'):
        if commits_or_churn == 'commits':
            commits_or_churn_df = self.commits
        elif commits_or_churn == 'churn':
            commits_or_churn_df = self.churn
        else:
            print('Usage: plot_code must be called on commits or churn.')
            sys.exit(1)
        percentage_changes = pd.DataFrame({'Protocol': self.target_names})
        change_list = []
        for index, chain in enumerate(self.chains):
            if commits_or_churn_df[chain].mean() < 10:
                # Negligible commits or churn, dead protocol
                print(commits_or_churn.capitalize(
                ) + ': ' + self.target_names[index] + ' averaged fewer than 10 changes per week and can be considered a dead protocol.')
                percentage_changes = percentage_changes[percentage_changes.Protocol !=
                                                        self.target_names[index]]
                continue
            try:
                # Average of first and last 8 weeks
                percentage_change = round(
                    ((sum(commits_or_churn_df[chain][-9:-1]) / sum(commits_or_churn_df[chain][0:8])) * 100) - 100)
            except:
                # None at the start of the year
                percentage_change = 0
            change_list.append(percentage_change)
            # Compute a 4-period MA to smooth data
            commits_or_churn_df[chain] = commits_or_churn_df[chain].rolling(
                4).mean()
        commits_or_churn_df.columns = ['Date'] + self.target_names
        percentage_changes['Percentage change in ' +
                           commits_or_churn] = change_list
        percentage_changes = percentage_changes.sort_values(
            'Percentage change in ' + commits_or_churn)
        code = commits_or_churn_df.melt(
            'Date', var_name='Protocol',  value_name=commits_or_churn)
        return code, percentage_changes

    def prep_devs(self):
        protocols_comparison = pd.DataFrame({'Month': self.xaxis})
        percentage_changes = pd.DataFrame({'Protocol': self.chains})
        change_list = []
        for chain in self.chains:
            monthly_active_dev_count = []
            output_path = path.join(
                dir_path, 'output', chain + '_contributors.json')
            with open(output_path) as json_file:
                data = json.load(json_file)
            for month in data:
                monthly_active_dev_count.append(len(month))
            protocols_comparison[chain] = monthly_active_dev_count
            try:
                percentage_change = round((((monthly_active_dev_count[-2] + monthly_active_dev_count[-1]) / (
                    monthly_active_dev_count[0] + monthly_active_dev_count[1])) * 100) - 100)
            except:
                percentage_change = 0
            change_list.append(percentage_change)
        protocols_comparison.columns = ['Month'] + self.target_names
        percentage_changes['Protocol'] = self.target_names
        percentage_changes['Percentage change in active devs'] = change_list
        percentage_changes = percentage_changes.sort_values(
            'Percentage change in active devs')
        protocols_comparison = protocols_comparison.melt(
            'Month', var_name='Protocol', value_name='Monthly Active Devs')
        return protocols_comparison, percentage_changes

    # Each of the below is separate as seaborn requires plots to have different figure variable names and clearing memory completely is not possible.

    def plot_commits(self, code: pd.DataFrame, percentage_changes: pd.DataFrame):
        code.to_csv('commits.csv')
        fig1 = sns.lineplot(x="Date", y='commits', hue='Protocol', data=code)
        fig1.get_figure().savefig('commits.png')
        fig1.clear()
        fig2 = sns.barplot(y="Protocol", x="Percentage change in commits",
                           data=percentage_changes, palette="RdYlGn")
        fig2.get_figure().savefig('commits_change.png')
        fig2.clear()

    def plot_churn(self, code: pd.DataFrame, percentage_changes: pd.DataFrame):
        code.to_csv('churn.csv')
        fig3 = sns.lineplot(x="Date", y='churn', hue='Protocol', data=code)
        fig3.set_yscale("log")
        fig3.get_figure().savefig('churn.png')
        fig3.clear()
        fig4 = sns.barplot(y="Protocol", x="Percentage change in churn",
                           data=percentage_changes, palette="RdYlGn")
        fig4.get_figure().savefig('churn_change.png')
        fig4.clear()

    def plot_devs(self, protocols_comparison: pd.DataFrame, percentage_changes: pd.DataFrame):
        protocols_comparison.to_csv('devs.csv')
        # Disable Seaborn sorting or months appear out of order
        fig5 = sns.lineplot(x="Month", y="Monthly Active Devs", hue='Protocol',
                            data=protocols_comparison, sort=False, palette="Dark2_r")
        fig5.get_figure().savefig('devs.png')
        fig5.clear()
        fig6 = sns.barplot(y="Protocol", x="Percentage change in active devs",
                           data=percentage_changes, palette="RdYlGn")
        fig6.get_figure().savefig('devs_change.png')
        fig6.clear()

    def run(self):
        code, percentage_changes = self.prep_code('commits')
        self.plot_commits(code, percentage_changes)
        code, percentage_changes = self.prep_code('churn')
        self.plot_churn(code, percentage_changes)
        protocols_comparison, percentage_changes = self.prep_devs()
        self.plot_devs(protocols_comparison, percentage_changes)
        for file in glob.glob('./*.png'):
            shutil.move(file, './res')
        for file in glob.glob('./*.csv'):
            shutil.move(file, './res')


if __name__ == '__main__':
    v = Visualize()
    v.run()
