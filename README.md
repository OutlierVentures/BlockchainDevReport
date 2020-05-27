# Blockchain Dev Report

Report on blockchain developer trends in 2020.

## Install

Requires Python.

```sh
pip3 install pygithub seaborn
```

## Usage

```sh
python3 dev.py [ORGANISATION_NAME]
```

The results are for the entire organisation (i.e. summed across repositories) and for all branches. Results are written to 2 files:

`[ORGANISATION_NAME]_stats.py`: Latest stats, such as star count and code churn in the last month.

`[ORGANISATION_NAME]_history.py`: Historical commits and code churn on a week-by-week basis.


## Methodology

### Historical commits and code changes

*For the Q2 2020 report, data was pulled 27-28 May 2020.*

Commits and code changes are pulled directly from the GitHub API. These are pulled per-repository, and then summed for all repositories in a given organisation.

The data points used are the total number of commits and total number of code changes (additions + deletions) each week across all branches.

In the visualisation, a 4-week moving average is taken to smooth the data.

The data collection is in `dev.py` and the visualization is in `viz.py`.

## TODO

1. Unlimit contributor count. The GitHub API has a 100-dev limit on returning contributors, will find a way around this.
2. Estimate the number of devs building on a protocol - this is very difficult to compute accurately. Could count the number of projects using the `web3.js`-equivalent package (or SDK), as this component is used by virtually all developers, regardless of blockchain client choice.
3. Use data from https://coincodecap.com/coins.