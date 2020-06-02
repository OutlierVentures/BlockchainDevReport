# Blockchain Dev Report

Source code and full methodology for Outlier Ventures' Blockchain Developer Reports.

## Install

Requires Python.

```sh
pip3 install pandas pygithub seaborn toml
```

## Usage

For all large data pulling operations, a [Github Personal Access Token (PAT)](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line) is required.

```sh
export PAT=[YOUR_GITHUB_PAT]
```

### Core protocol progress

```sh
python3 dev.py [ORGANISATION_NAME]
```

The results are for the entire organisation (i.e. summed across repositories) and for all branches. Results are written to 2 files:

`[ORGANISATION_NAME]_stats.json`: Latest stats, such as star count and code churn in the last month.

`[ORGANISATION_NAME]_history.json`: Historical commits and code churn on a week-by-week basis.

### Total devs building on a chain

Repos to search are loaded from a toml file of the following format:
```toml
[[repo]]
url = "https://github.com/org1/repo1"

[[repo]]
url = "https://github.com/org2/repo2"
```

This is compatible with [Electric Capital's Crypto Ecosystems repo](https://github.com/electric-capital/crypto-ecosystems), which catalogues the repos building on a given blockchain.

```sh
python3 contr.py yourfilename.toml
```

The total number active in the past year is printed, and the usernames written to `yourfilename.json`. If an error occurs, progress is written to this file and the latest viewed repo is printed (the one on which it failed). To restart, delete all repos in the toml file before but not including the last repo printed.

### Visualizing results

Once you have run both of the above, you can visualize results:

```sh
python3 vis.py
```

Results are written to files `commits.png`, `commits_change.png`, `churn.png`, `churn_change.png`, `devs.png` and `devs_change.png`. Note that churn refers to the number of code changes.

## Methodology

*For the Q2 2020 report, data was pulled 27 May - 1 June 2020. The source files used for repositories analysed for the total developer count are in the `protocols` folder.*

### Core protocol progress: historical commits and code changes

Commits and code changes are pulled directly from the GitHub API. These are pulled per-repository, and then summed for all repositories in a given organisation.

The data points used are the total number of commits and total number of code changes (additions + deletions) each week across all branches.

In the visualisation, a 4-week moving average is taken to smooth the data.

The data collection is in `dev.py` and the visualization is in `vis.py`.

### Total devs building on a chain

The list of repos building on a given chain is specified in a `.toml` (format above), and data is pulled from [Electric Capital's Crypto Ecosystems repo](https://github.com/electric-capital/crypto-ecosystems), which catalogues the repos building on a given blockchain.

All commits are pulled from each repo and the date as well as the author (GitHub username) returned. Any commits with a date from more than one year in the past are filtered out. The process is repeated for all repos in the `.toml` file, with the resulting list of contributors combined and de-duplicated.

The data collection is in `contr.py` and the visualization is in `vis.py`.

### Visualization, including growth calculation

Commit and churn charts are visualised using a 4-week moving average to smooth data. Therefore, the curve lags by approximately 2 weeks.

Developer activity charts display the raw data.

Growth charts (percentage change) take an average of the last 8 weeks of the year and compare this figure to the first 8 weeks of the year, rounding to the nearest whole percentage point. This applies to all growth charts: commit, churn and developer activity.

### Dapp metrics, such as daily active users

Dapp data was taken from State of the Dapps, which reads directly from the relevant blockchains. The data source can be found [here](https://www.stateofthedapps.com/stats).

The daily active users data was extracted and visualized in Seaborn using the same method as in `vis.py`. The raw data is displayed.

The share of smart contracts and dapps data was extracted and visualised in MatPlotLib using the following code (as Seaborn does not provide pie charts):

```py
from matplotlib import pyplot as plt

labels = ['Ethereum', 'EOS', 'etc.']
number_of_contracts_or_dapps = [4500, 500, 450]
fig1, ax1 = plt.subplots()
ax1.pie(dapps, labels = labels, startangle = 90,autopct = '%1.1f%%', pctdistance = 0.8)
ax1.axis('equal') # Equal aspect ratio ensures that pie is drawn as a circle.
plt.savefig('myfile.png')
```

### Survey and Defi data (further reading)

Survey data for the Q2 2020 report was taken from the [Embark Labs Developer Survey 2020](https://blog.embarklabs.io/news/2020/03/04/2020-Blockchain-Developer-Survey/). Enterprise data for the Q2 2020 report was taken from the [Deloitte Blockchain Trends Report 2020](https://www2.deloitte.com/content/dam/Deloitte/ie/Documents/Consulting/Blockchain-Trends-2020-report.pdf). DeFi data for the Q2 2020 report was taken from the [Alethio Analytics Ethereum Decentralized Finance Report 2020](https://pages.consensys.net/ethereum-decentralized-finance-report-alethio).