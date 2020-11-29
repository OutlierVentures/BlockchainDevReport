import seaborn as sns, pandas as pd, json, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from os import path

dir_path = path.dirname(path.realpath(__file__))

class Visualize:

    def __init__(self):
        self.chains = ['Binance-Chain', 'Bitcoin', 'Bitcoin-ABC', 'Bitcoin-SV', 'Corda', 'Cosmos', 'Crypto-Com', 'DashPay', 'DogeCoin', 'EOSio', 'Ethereum', 'EthereumClassic', 'HuobiGroup', 'Hyperledger', 'Input-Output-HK', 'IOTALedger', 'Litecoin-Project', 'MakerDAO', 'Monero-Project', 'NemProject', 'Neo-Project', 'OKEX', 'OntIO', 'ParityTech', 'Ripple', 'SmartContractKit', 'Stellar', 'ThetaToken', 'TronProtocol', 'VeChain', 'Zcash']
        self.target_names = ['Binance Chain', 'Bitcoin', 'Bitcoin Cash', 'Bitcoin SV', 'Corda', 'Cosmos', 'Crypto.Com', 'Dash', 'Dogecoin', 'EOS', 'Ethereum', 'Ethereum Classic', 'Huobi Chain', 'Hyperledger', 'Cardano', 'IOTA', 'Litecoin', 'MakerDAO', 'Monero', 'NEM', 'NEO', 'OKChain', 'Ontology', 'Polkadot', 'Ripple', 'Chainlink', 'Stellar', 'Theta', 'Tron', 'VeChain', 'Zcash']
        self.contributor_chains = ['bitcoin-cash', 'bitcoin', 'cardano', 'corda', 'cosmos', 'eos', 'ethereum', 'hyperledger', 'polkadot', 'ripple', 'stellar', 'tron']
        self.contributor_target_names = ['Bitcoin Cash', 'Bitcoin', 'Cardano', 'Corda', 'Cosmos', 'EOS', 'Ethereum', 'Hyperledger', 'Polkadot', 'Ripple', 'Stellar', 'Tron']
        self.xaxis = ['Jun 19', 'Jul 19', 'Aug 19', 'Sep 19', 'Oct 19', 'Nov 19', 'Dec 19', 'Jan 20', 'Feb 20', 'Mar 20', 'Apr 20', 'May 20']
        end = datetime.now()
        start = datetime.now() - relativedelta(years = 1)
        date_index = pd.date_range(start, end, freq = 'W')
        if len(date_index) > 52:
            date_index = date_index.drop(date_index[-1])
        self.commits = pd.DataFrame({'Date': date_index})
        self.churn = pd.DataFrame({'Date': date_index})
        for chain in self.chains:
            output_path = path.join(dir_path, 'output', chain + '_history.json')
            with open(output_path) as json_file:
                data = json.load(json_file)
            self.commits[chain] = data['weekly_commits']
            self.churn[chain] = data['weekly_churn'][-52:]
        sns.set(style = "darkgrid")
        sns.set(rc = {'figure.figsize': (16, 9)})

    def prep_code(self, commits_or_churn : str = 'commits'):
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
                print(commits_or_churn.capitalize() + ': ' + self.target_names[index] + ' averaged fewer than 10 changes per week and can be considered a dead protocol.')
                percentage_changes = percentage_changes[percentage_changes.Protocol != self.target_names[index]]
                continue
            try:
                # Average of first and last 8 weeks
                percentage_change = round(((sum(commits_or_churn_df[chain][-9:-1]) / sum(commits_or_churn_df[chain][0:8])) * 100) - 100)
            except:
                # None at the start of the year
                percentage_change = 0
            change_list.append(percentage_change)
            # Compute a 4-period MA to smooth data
            commits_or_churn_df[chain] = commits_or_churn_df[chain].rolling(4).mean()            
        commits_or_churn_df.columns = ['Date'] + self.target_names
        percentage_changes['Percentage change in ' + commits_or_churn] = change_list
        percentage_changes = percentage_changes.sort_values('Percentage change in ' + commits_or_churn)
        code = commits_or_churn_df.melt('Date', var_name = 'Protocol',  value_name = commits_or_churn)
        return code, percentage_changes

    def prep_devs(self):
        protocols_comparison = pd.DataFrame({'Month': self.xaxis})
        percentage_changes = pd.DataFrame({'Protocol': self.contributor_chains})
        change_list = []
        for chain in self.contributor_chains:
            monthly_active_dev_count = []
            with open(chain + '.json') as json_file:
                data = json.load(json_file)
            for month in data:
                monthly_active_dev_count.append(len(month))       
            protocols_comparison[chain] = monthly_active_dev_count
            percentage_change = round((((monthly_active_dev_count[-2] + monthly_active_dev_count[-1]) / (monthly_active_dev_count[0] + monthly_active_dev_count[1])) * 100) - 100)
            change_list.append(percentage_change)
        protocols_comparison.columns = ['Month'] + self.contributor_target_names
        percentage_changes['Protocol'] = self.contributor_target_names
        percentage_changes['Percentage change in active devs'] = change_list
        percentage_changes = percentage_changes.sort_values('Percentage change in active devs')
        protocols_comparison = protocols_comparison.melt('Month', var_name = 'Protocol', value_name = 'Monthly Active Devs')
        return protocols_comparison, percentage_changes

    # Each of the below is separate as seaborn requires plots to have different figure variable names and clearing memory completely is not possible.

    def plot_commits(self, code : pd.DataFrame, percentage_changes: pd.DataFrame):
        fig1 = sns.lineplot(x = "Date", y = 'commits', hue = 'Protocol', data = code)
        fig1.get_figure().savefig('commits.png')
        fig1.clear()
        fig2 = sns.barplot(y = "Protocol", x = "Percentage change in commits", data = percentage_changes, palette = "RdYlGn")
        fig2.get_figure().savefig('commits_change.png')
        fig2.clear()

    def plot_churn(self, code : pd.DataFrame, percentage_changes: pd.DataFrame):
        fig3 = sns.lineplot(x = "Date", y = 'churn', hue = 'Protocol', data = code)
        fig3.set_yscale("log")
        fig3.get_figure().savefig('churn.png')
        fig3.clear()
        fig4 = sns.barplot(y = "Protocol", x = "Percentage change in churn", data = percentage_changes, palette = "RdYlGn")
        fig4.get_figure().savefig('churn_change.png')
        fig4.clear()

    def plot_devs(self, protocols_comparison : pd.DataFrame, percentage_changes : pd.DataFrame):
        # Disable Seaborn sorting or months appear out of order
        fig5 = sns.lineplot(x = "Month", y = "Monthly Active Devs", hue = 'Protocol', data = protocols_comparison, sort = False, palette="Dark2_r")
        fig5.get_figure().savefig('devs.png')
        fig5.clear()
        fig6 = sns.barplot(y = "Protocol", x = "Percentage change in active devs", data = percentage_changes, palette = "RdYlGn")
        fig6.get_figure().savefig('devs_change.png')
        fig6.clear()
        
    def run(self):
        code, percentage_changes = self.prep_code('commits')
        self.plot_commits(code, percentage_changes)
        code, percentage_changes = self.prep_code('churn')
        self.plot_churn(code, percentage_changes)
        protocols_comparison, percentage_changes = self.prep_devs()
        self.plot_devs(protocols_comparison, percentage_changes)


if __name__ == '__main__':
    v = Visualize()
    v.run()
