# Blockchain Dev Report

Report on blockchain developer trends in 2020.

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

## Core protocol progress

```sh
python3 dev.py [ORGANISATION_NAME]
```

The results are for the entire organisation (i.e. summed across repositories) and for all branches. Results are written to 2 files:

`[ORGANISATION_NAME]_stats.py`: Latest stats, such as star count and code churn in the last month.

`[ORGANISATION_NAME]_history.py`: Historical commits and code churn on a week-by-week basis.

## Total devs building on a chain

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

## Methodology

*For the Q2 2020 report, data was pulled 27-31 May 2020. The source files used for repositories analysed for the total developer count are in the `protocols` folder.*

### Core protocol progress: historical commits and code changes

Commits and code changes are pulled directly from the GitHub API. These are pulled per-repository, and then summed for all repositories in a given organisation.

The data points used are the total number of commits and total number of code changes (additions + deletions) each week across all branches.

In the visualisation, a 4-week moving average is taken to smooth the data.

The data collection is in `dev.py` and the visualization is in `viz.py`.

### Total devs building on a chain

The list of repos building on a given chain is specified in a `.toml` (format above), and data is pulled from [Electric Capital's Crypto Ecosystems repo](https://github.com/electric-capital/crypto-ecosystems), which catalogues the repos building on a given blockchain.

All commits are pulled from each repo and the date as well as the author (GitHub username) returned. Any commits with a date from more than one year in the past are filtered out. The process is repeated for all repos in the `.toml` file, with the resulting list of contributors combined and de-duplicated.

## TODO

1. Use data from https://coincodecap.com/coins.