import configparser as ConfigParser
from dotenv import load_dotenv
import os

load_dotenv()

config = ConfigParser.RawConfigParser(allow_no_value=True)
config.read('config.ini')

def get_chain_names():
    return config['chains']['names']

def get_chain_targets():
    return config['chains']['targets']

def remove_chain_from_config(chain):
    chain_names_arr = config['chains']['names'].split()
    chain_index = chain_names_arr.index(chain)
    del chain_names_arr[chain_index]
    config['chains']['names'] = ' '.join(chain_names_arr)
    
    chains_targets_arr = config['chains']['targets'].split(", ")
    del chains_targets_arr[chain_index]
    config['chains']['targets'] = ', '.join(chains_targets_arr)

def get_pats():
    return os.getenv('GITHUB_PATS').split(" ")