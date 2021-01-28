# -*- coding: utf-8 -*-

from os import path
from config import get_chain_names
import requests
from logger import sys

# WARNING: Make sure that the coin names are the same as .toml file names of Electric Capital
coin_names = get_chain_names().split()
ELECTRIC_CAPITAL_RAW_CONTENT_BASE_URL = "https://raw.githubusercontent.com/electric-capital/crypto-ecosystems/master/data/ecosystems"


def update_toml_data(coin_name):
    print("Try updating .toml file for %s ..." % coin_name)
    if len(coin_name) == 0:
        raise Exception("Invalid blockchain name")

    file_url = ELECTRIC_CAPITAL_RAW_CONTENT_BASE_URL + \
               '/' + coin_name[0] + '/' + coin_name + '.toml'
    r = requests.get(file_url)
    if r.status_code != 200:
        raise Exception("Failed to get the toml file for: ", coin_name)

    file_content = r.text

    dir_path = path.dirname(path.realpath(__file__))
    toml_file_path = path.join(dir_path, '.', 'protocols', coin_name + '.toml')
    with open(toml_file_path, 'w') as file:
        file.write(file_content)


if __name__ == "__main__":
    # Updates .toml files with the latest from electric capital
    # Data is updated only for the `coin_names` specified at the top
    for (_, coin_name) in enumerate(coin_names):
        try:
            update_toml_data(coin_name)
        except:
            pass