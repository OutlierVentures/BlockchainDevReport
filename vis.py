import seaborn as sns, pandas as pd, json
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Visualize:

    def __init__(self):
        self.chains = ['Binance-Chain', 'Bitcoin', 'Bitcoin-ABC', 'Bitcoin-SV', 'Corda', 'Cosmos', 'Crypto-Com', 'DashPay', 'DogeCoin', 'EOSio', 'Ethereum', 'EthereumClassic', 'HuobiGroup', 'Hyperledger', 'Input-Output-HK', 'IOTALedger', 'Litecoin-Project', 'MakerDAO', 'Monero-Project', 'NemProject', 'Neo-Project', 'OKEX', 'OntIO', 'ParityTech', 'Ripple', 'SmartContractKit', 'Stellar', 'ThetaToken', 'TronProtocol', 'VeChain', 'Zcash']
        self.target_names = ['Binance Chain', 'Bitcoin', 'Bitcoin Cash', 'Bitcoin SV', 'Corda', 'Cosmos', 'Crypto.Com', 'Dash', 'Dogecoin', 'EOS', 'Ethereum', 'Ethereum Classic', 'Huobi Chain', 'Hyperledger', 'Cardano', 'IOTA', 'Litecoin', 'MakerDAO', 'Monero', 'NEM', 'NEO', 'OKChain', 'Ontology', 'Polkadot', 'Ripple', 'Chainlink', 'Stellar', 'Theta', 'Tron', 'VeChain', 'Zcash']
        self.contributor_chains = ['bitcoin-cash', 'bitcoin', 'cardano', 'corda', 'cosmos', 'eos', 'ethereum', 'hyperledger', 'polkadot', 'ripple', 'stellar', 'tron']
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
        self.commits.columns = ['Date'] + self.target_names
        df1 = self.commits.melt('Date', var_name = 'Protocol',  value_name = 'Commits')
        fig1 = sns.lineplot(x = "Date", y = "Commits", hue = 'Protocol', data = df1)
        fig1.get_figure().savefig('commits.png')
        fig1.clear()
        
    def plot_churn(self):
        # Compute a 4-period MA to smooth data
        for chain in self.chains:
            self.churn[chain] = self.churn[chain].rolling(4).mean()
        self.churn.columns = ['Date'] + self.target_names
        df2 = self.churn.melt('Date', var_name = 'Protocol',  value_name = 'Churn')
        fig2 = sns.lineplot(x = "Date", y = "Churn", hue = 'Protocol', data = df2)
        fig2.set_yscale("log") # Large additions e.g. opening a repo makes the linear data hard to interpret
        fig2.get_figure().savefig('churn.png')
        fig2.clear()
    
    def plot_devs(self):
        protocols_comparison = pd.DataFrame({'Month': ['Jun 19', 'Jul 19', 'Aug 19', 'Sep 19', 'Oct 19', 'Nov 19', 'Dec 19', 'Jan 20', 'Feb 20', 'Mar 20', 'Apr 20', 'May 20']})
        for chain in self.contributor_chains:
            monthly_active_dev_count = []
            with open('protocols/protocols/' + chain + '.json') as json_file:
                data = json.load(json_file)
            for month in data:
                monthly_active_dev_count.append(len(month))
            protocols_comparison[chain] = monthly_active_dev_count
        protocols_comparison = protocols_comparison.melt('Month', var_name = 'Protocol', value_name = 'Monthly Active Devs')
        # Disable Seaborn sorting or months appear out of order
        fig3 = sns.lineplot(x = "Month", y = "Monthly Active Devs", hue = 'Protocol', data = protocols_comparison, sort = False)
        fig3.get_figure().savefig('devs.png')
        fig3.clear()
        
            
    
    def run(self):
        for chain in self.chains:
            self.load(chain)
        sns.set(style = "darkgrid")
        sns.set(rc = {'figure.figsize': (16, 9)})
        self.plot_churn()
        self.plot_commits()


if __name__ == '__main__':
    v = Visualize()
    sns.set(style = "darkgrid")
    sns.set(rc = {'figure.figsize': (16, 9)})
    v.plot_devs()
    #v.run()