# Blockchain Dev Report

Report on blockchain developer trends in 2020.

## Install

Requires Python.

```sh
pip3 install pygithub
```

## Usage

```sh
python3 dev.py [ORGANISATION_NAME]
```

The results are for the enitre organisation (i.e. summed across repositories) and for all branches. Results are written to 2 files:

`[ORGANISATION_NAME]_stats.py`: Latest stats, such as star count and code churn in the last month.

`[ORGANISATION_NAME]_history.py`: Historical commits and code churn on a week-by-week basis.

## TODO

1. Unlimit contributor count. The GitHub API has a 100-dev limit on returning contributors, will find a way around this.
2. Estimate the number of devs building on a protocol - this is very difficult to compute accurately. Could count the number of projects using the `web3.js`-equivalent package, as this component is used by virtually all developers, regardless of blockchain client choice.