import os
import csv
import json

with open('./res/stats.csv', 'w+', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Protocol", "Stars", "Forks", "Releases"])
    for filename in os.listdir('./output'):
        print(filename)
        if '_stats.json' not in filename:
            continue
        with open("./output/" + filename, 'r') as stats_json:
            protocol_stats = json.load(stats_json)
        protocol = filename.split('_')
        stars = protocol_stats['stars'] if "stars" in protocol_stats else 0
        forks = protocol_stats['forks'] if "forks" in protocol_stats else 0
        releases = protocol_stats['num_releases'] if "num_releases" in protocol_stats else 0
        writer.writerow([protocol[0], stars, forks, releases])
