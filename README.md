# Blockchain Development Report

Source code and full methodology for Outlier Ventures' Blockchain Development Reports. Latest one can be found [here](https://outlierventures.io/research/blockchain-developer-trends-2021/)

## Setup 

### Install

Requires Python.

```sh
pip3 install -r requirements.txt
```

### Add GitHub PATs
For all large data pulling operations from GitHub, [GitHub Personal Access Tokens (PAT)](https://help.github.com/en/github/authenticating-to-github/creating-a-personal-access-token-for-the-command-line) are required as user to GitHub server requests are rate-limited at 5000 requests per hour per authenticated user. No scope/access is required for the tokens.
PS: If you have private repos, be sure to use a token that only has the `public_repo` scope.
Create a .env (refer to env.sample) to store all the GitHub PATs in a single space seperated list. These PATs will be used in round robin to access the various GitHub Organisations and Repositories. 

### Update Config (optional)
In the `config.ini` file, there are three categories of protocols/projects namely, 
- Blockchain
- DeFi 
- NFT (& Metaverse)

Each category contains the protocols/projects analysed for the [Blockchain Development Trends 2021 Report](https://outlierventures.io/research/blockchain-developer-trends-2021/). 
To run for a particular category, uncomment the corresponding section and run script(s) for Blockchian/DeFi/NFT protocols/projects. You can also add protocols/projects you want the scripts to analyse. 

### Update Protocols (optional)
The analysis is based on core repositories for each protocol with the [Electric Capital’s crowdsourced Crypto Ecosystems](https://github.com/electric-capital/crypto-ecosystems) index being used as the base, where we have manually curated relevant organisations per ecosystem based on thorough research. Therefore, we would **advise against** updating protocol toml as it would overwrite the manual curation of organisations. 

All of the ecosystems are specified in TOML configuration files. To update TOML files of the protocols/projects added for comparision by you to the config, you can follow either of the two steps: 
- **Automated:** Comment all categories of protocols/projects in the `config.ini`, create a new variable called `chains` in the `config.ini` containing their names in a single space seperated list. Ensure that their names are the same as .toml file names of the corresponding Electric Capital Crypto Ecosytems. Then run the following command,
```sh
python3 updateProtocols.py
```
- **Manual:** Create a file in the `protocols` sub-folder with the same name as that of the TOML files corresponding to the protocols/projects in the Electric Capital Crypto Ecosytems and copy and paste the contents in it.

## Usage

### Protocol core development
```sh
python3 dev.py [PROTOCOL_NAME]
```

This analyses historical commits, code changes and statistics for the each of the GitHub organisations belonging to the protocol, summed across repositories for the default branch (main/master). Results are written to 2 files:

`[PROTOCOL_NAME]_stats.json`: Latest stats, such as star count and code churn in the last month.

`[PROTOCOL_NAME]_history.json`: Historical commits and code churn (additions and deletions) on a week-by-week basis.

### Protocol core contributing developers
```sh
python3 contr.py ./protcocols/[PROTOCOL_NAME].toml
```

The total number active in the past year is printed, and the usernames written to `[PROTOCOL_NAME]_contributors_.json`. It saves all the seen repositories in the `[PROTOCOL_NAME]_repos_seen.txt`. If an error occurs, rerunning this script will start analysing from the point where it crashed (ignoring all seen repos). 

### Visualizing results
Once you have run both of the above run for all the protocols/projects, you can visualize results using the following command.
```sh
python3 vis.py
```

Results are written to files `commits.csv`, `commits.png`, `commits_change.png`, `churn.csv`,`churn.png`, `churn_change.png`, `devs.csv`, `devs.png` and `devs_change.png`. Note that churn refers to the number of code changes.

### One stop shell script

## Methodology

We have based our analsysis on core repositories for each protocol using [Electric Capital’s crowdsourced Crypto Ecosystems](https://github.com/electric-capital/crypto-ecosystems) index as the base, with manual curation of relevant organisations per ecosystem. 

All the core repositories of each of the GitHub organizations of a protocol were taken and the forked repositories, when marked as such on GitHub, were ignored. Forking repositories is very common practice, and leads to the development activity of one ecosystem being included in another. Including all forks in the analysis adds a lot more noise than signal. For similar reasons, only activity for the default branch (main or master) of each repository was included. In these ‘unforked’ repositories, all commits to the default branch were indexed and analyzed.

We attribute the development activity for each organization on GitHub to a single protocol, and don’t
include individual repositories outside of those organizations, to most accurately show development
activity to the core development of protocols.

For the Blockchain Development Trends 2021 report, GitHub data was pulled for the duration of 27 January - 31 December 2020. The TOML configuration files used for organisations and repositories analysed for the core development and developer count are in the `protocols` folder.

### Core protocol development: historical commits and code changes

Commits and code changes are pulled directly from the GitHub API. These are pulled per-repository, and then summed for all repositories in a given organisation for their default branch (main/master).

The data points used are the total number of commits and total number of code changes (additions + deletions) each week across all branches.

In the visualisation, a 4-week moving average is taken to smooth the data.

The data collection is in `dev.py` and the visualization is in `vis.py`.

### Core developer contributing to a protocol

All commits are pulled from each repo and the date as well as the author (GitHub username) returned. Any commits with a date from more than one year in the past are filtered out. The process is repeated for all repos in the `.toml` file, with the resulting list of contributors combined and de-duplicated.

The data collection is in `contr.py` and the visualization is in `vis.py`.

### GitHub Statistics
A measurement of the sum total of Stars, Forks and Releases of each of the core repositories of the protocols’ GitHub organization indicating in some way its popularity and activity.

### Visualization, including growth calculation

Commit and churn charts are visualised using a 4-week moving average to smooth data. Therefore, the curve lags by approximately 2 weeks.

Developer activity charts display the raw data.

Growth charts (percentage change) take an average of the last 8 weeks of the year and compare this figure to the first 8 weeks of the year, rounding to the nearest whole percentage point. This applies to all growth charts: commit, churn and developer activity.
