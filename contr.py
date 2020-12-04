# -*- coding: utf-8 -*-

import asyncio
import datetime as dt
import json
import os
import re
import sys
from asyncio import get_event_loop, ensure_future

import toml
from aiohttp import ClientSession
from gitTokenHelper import GithubPersonalAccessTokenHelper


async def get_commits(session, pat, org_then_slash_then_repo, page):
    async with session.get(url='https://api.github.com/repos/' + org_then_slash_then_repo + '/commits?page='
                               + str(page) + '&per_page=100',
                           headers={'Authorization': 'Token ' + pat}) as r:
        if r.status == 200:
            data = await r.json()
            rate_limit_remaining = int(r.headers['X-RateLimit-Remaining'])
            total_pages = None
            if "link" in r.headers:
                pages_link = r.headers['link']
                last_page_link = pages_link.split(",")[1]
                re_match = re.search('page=(.*)&per_page=100>; rel="last"', last_page_link)
                if re_match:
                    total_pages = int(re_match.group(1))
            return {
                "error": None,
                "error_code": None,
                "data": data,
                "total_pages": total_pages,
                "rate_limit_remaining": rate_limit_remaining
            }
        err_message = await r.text()
        return {
            "error": "{0} {1}".format(r.reason, err_message),
            "error_code": r.status
        }


# Python client only allows the first 100 contributors to be returned, so use vanilla HTTP to get contributors
class Contributors:

    def __init__(self, save_path: str):
        self.save_path = save_path
        # TODO: fix this to be an array
        self.gh_pat_helper = GithubPersonalAccessTokenHelper(['add', 'tokens', 'here'])

    async def _get_access_token(self):
        res = self.gh_pat_helper.get_access_token()
        if "token" in res and res["token"] is not None:
            return res["token"]
        print('Going to sleep since no token exists with usable rate limit')
        await asyncio.sleep(res["sleep_time_secs"])
        return await self._get_access_token()

    async def get_contributors_of_repo_in_last_year(self, org_then_slash_then_repo: str):
        # Commits are not chronological, so need to pull all and filter
        commits = []

        # get personal access token
        pat = await self._get_access_token()

        async with ClientSession() as session:
            initial_request = await get_commits(session, pat, org_then_slash_then_repo, page=1)
            # Repo doesn't exist
            if initial_request["error"] or (type(initial_request["data"]) == dict and initial_request["data"].message == 'Not Found'):
                return []  
            if isinstance(initial_request["data"], list) and len(initial_request["data"]) == 0:
                return []
            commits.extend(initial_request["data"])

            rate_limit_remaining = initial_request["rate_limit_remaining"]
            remaining_requests_to_be_made = 0
            if initial_request["total_pages"]:
                remaining_requests_to_be_made = initial_request["total_pages"] - 1

            # starting page
            batch_start = 2
            while remaining_requests_to_be_made > 0:
                if remaining_requests_to_be_made > min(rate_limit_remaining, 200):
                    batch_end = batch_start + min(rate_limit_remaining, 200)
                else:
                    batch_end = batch_start + remaining_requests_to_be_made

                print("Start", batch_start, "End", batch_end)

                # get data for page from batch_start to batch_end
                tasks = []
                for page in range(batch_start, batch_end + 1):
                    task = ensure_future(
                        get_commits(session, pat, org_then_slash_then_repo, page)
                    )
                    tasks.append(task)

                responses = await asyncio.gather(*tasks)
                if len(responses) == 0:
                    sys.exit(1)

                successful_responses_count = 0
                rate_limit_exceeded = False
                for response in responses:
                    if response["error"]:
                        if response["error_code"] == 403:
                            print("Rate limit trigger detected")
                            rate_limit_exceeded = True
                            break
                        # Printing unhandled error and exiting
                        print(response)
                        sys.exit(1)

                    if not isinstance(response["data"], list):
                        print(response["error"])
                        sys.exit(1)
                    successful_responses_count += 1
                    commits.extend(response["data"])

                if rate_limit_exceeded:
                    print("Hourly rate limit exceeded for current token")
                    pat = await self._get_access_token()

                print("Successful reqs: ", successful_responses_count)
                remaining_requests_to_be_made -= successful_responses_count
                rate_limit_remaining -= successful_responses_count
                batch_start += successful_responses_count

        # Remove older commits
        year_ago_date = dt.datetime.now() - dt.timedelta(days=365)  # Use 366 for leap years
        contributors = []
        for item in commits:
            try:
                date_string = item['commit']['author']['date']
                date = dt.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
                if date > year_ago_date:
                    if item['author']:  # Can be null (user not logged in)
                        contributors.append(item['author']['login']) # GitHub username
            except Exception as e:
                print(e)
                sys.exit(1)
        # De-duplicate commiters
        deduplicated_contributors = list(set(contributors))
        # print(len(deduplicated_contributors))
        return deduplicated_contributors

    async def get_monthly_contributors_of_repo_in_last_year(self, org_then_slash_then_repo: str):
        # Commits are not chronological, so need to pull all and filter
        commits = []

        # get personal access token
        pat = await self._get_access_token()

        async with ClientSession() as session:
            initial_request = await get_commits(session, pat, org_then_slash_then_repo, page=1)
            # Repo doesn't exist
            if initial_request["error"] or (type(initial_request["data"]) == dict and initial_request["data"].message == 'Not Found'):
                return [[], [], [], [], [], [], [], [], [], [], [], []] 
            if isinstance(initial_request["data"], list) and len(initial_request["data"]) == 0:
                return [[], [], [], [], [], [], [], [], [], [], [], []]
            commits.extend(initial_request["data"])

            rate_limit_remaining = initial_request["rate_limit_remaining"]
            remaining_requests_to_be_made = 0
            if initial_request["total_pages"]:
                remaining_requests_to_be_made = initial_request["total_pages"] - 1

            # starting page
            batch_start = 2
            while remaining_requests_to_be_made > 0:
                if remaining_requests_to_be_made > min(rate_limit_remaining, 200):
                    batch_end = batch_start + min(rate_limit_remaining, 200)
                else:
                    batch_end = batch_start + remaining_requests_to_be_made

                print("Start", batch_start, "End", batch_end)

                # get data for page from batch_start to batch_end
                tasks = []
                for page in range(batch_start, batch_end + 1):
                    task = ensure_future(
                        get_commits(session, pat, org_then_slash_then_repo, page)
                    )
                    tasks.append(task)

                responses = await asyncio.gather(*tasks)
                if len(responses) == 0:
                    sys.exit(1)

                successful_responses_count = 0
                rate_limit_exceeded = False
                for response in responses:
                    if response["error"]:
                        if response["error_code"] == 403:
                            print("Rate limit trigger detected")
                            rate_limit_exceeded = True
                            break
                        # Printing unhandled error and exiting
                        print(response)
                        sys.exit(1)

                    if not isinstance(response["data"], list):
                        print(response["error"])
                        sys.exit(1)
                    successful_responses_count += 1
                    commits.extend(response["data"])

                if rate_limit_exceeded:
                    print("Hourly rate limit exceeded for current token")
                    pat = await self._get_access_token()

                print("Successful reqs: ", successful_responses_count)
                remaining_requests_to_be_made -= successful_responses_count
                rate_limit_remaining -= successful_responses_count
                batch_start += successful_responses_count

        # If wanting to create a record of every repo's commits, uncomment this
        # with open(org_then_slash_then_repo + '_commits.json', 'w+') as outfile:
        #    json.dump(commits, outfile)
        # Remove older commits
        month_start_dates = [dt.datetime.now()]  # Include final end date for later use
        for month in range(1, 13):  # Generate 12 months of start dates
            month_start_dates.append(month_start_dates[-1] - dt.timedelta(days=30))  # 12 'months' is 360 days
        month_start_dates.reverse()
        # Explicity def rather than []*12 as this uses same memory ref, thus append to one element means append to all
        contributors = [[], [], [], [], [], [], [], [], [], [], [], []]
        for item in commits:
            try:
                date_string = item['commit']['author']['date']
                date = dt.datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%SZ')
                # FIXME find a more efficient way to do this
                for index, (start, end) in enumerate(zip(month_start_dates, month_start_dates[1:])):
                    if date >= start and date < end and item['author']:  # Can be null (user not logged in)
                        contributors[index].append(item['author']['login'])
            except Exception as e:
                print('Failed to get monthly contributors for ' + org_then_slash_then_repo)
                print(e)
                sys.exit(1)
        # De-duplicate commiters
        for index, month_of_contributors in enumerate(contributors):
            deduplicated_contributors = list(set(month_of_contributors))
            contributors[index] = deduplicated_contributors
        return contributors

    async def get_contr_from_toml(self, toml_file: str, monthly: bool = True):
        toml_file_without_protocols = toml_file.split('protocols/')[1]
        out_file_name = toml_file_without_protocols.replace('.toml', '_contributors.json')
        out_file_name_with_path = self.save_path + '/' + out_file_name
        # Useful if left running e.g. over weekend - if failed, re-run INCLUDING last repo listed
        progress_file_name = toml_file.replace('.toml', '_repos_seen.txt')

        stats = None
        if os.path.exists(out_file_name):
            with open(out_file_name, 'r') as stats_json:
                stats = json.load(stats_json)

        seen_repos = []
        if os.path.exists(progress_file_name):
            progress_file = open(progress_file_name, 'r')
            progress_repos_list = progress_file.readlines()
            for (_, repo_name_with_line_term) in enumerate(progress_repos_list):
                repo_name = repo_name_with_line_term.split("\n")[0]
                seen_repos.append(repo_name)

        if stats:
            core_array = stats
        elif monthly:
            # Explicity def, see above
            # TODO: change this length to make it configurable 
            core_array = [[], [], [], [], [], [], [], [], [], [], [], []]
        else:
            # yearly
            core_array = []
        with open(out_file_name_with_path, 'w') as outfile:
            json.dump(core_array, outfile)
        try:
            with open(toml_file, 'r') as f:
                data = f.read()
            repos = toml.loads(data)['repo']
        except:
            print('Could not open toml file - check formatting.')
            sys.exit(1)
        # Don't thread this - API limit
        for repo in repos:
            if 'url' in repo:
                url = repo['url'].lower()
                # check if repo is github repo
                org_then_slash_then_repo = url.split('github.com/')[1]
                if org_then_slash_then_repo[-1] == '/':
                    org_then_slash_then_repo = org_then_slash_then_repo[:-1]
                print('Analysing ' + org_then_slash_then_repo)
                with open(progress_file_name, 'a') as f:
                    f.write(org_then_slash_then_repo + '\n')

                if org_then_slash_then_repo in seen_repos:
                    continue
                if monthly:
                    contributors = await self.get_monthly_contributors_of_repo_in_last_year(org_then_slash_then_repo)
                else:
                    contributors = await self.get_contributors_of_repo_in_last_year(org_then_slash_then_repo)
                # Save progress in case of failure
                try:
                    with open(out_file_name_with_path) as json_file:
                        data = json.load(json_file)
                    if monthly:
                        # FIXME efficiency, note np.concatenate on axis 1 doesn't play well with our core array
                        for index, item in enumerate(data):
                            item.extend(contributors[index])
                    else:
                        data.extend(contributors)
                    with open(progress_file_name, 'a') as progress_file:
                        progress_file.write(org_then_slash_then_repo + '\n')
                    with open(out_file_name_with_path, 'w') as outfile:
                        json.dump(data, outfile)
                except Exception as e:
                    print('Failed to collate monthly contributors for all repos in toml file')
                    print(e)
                    sys.exit(1)
        try:
            with open(out_file_name_with_path) as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(e)
            sys.exit(1)
        if monthly:
            print('Monthly active developers in the past year:')
            for index, month_of_contributors in enumerate(data):
                deduplicated_monthly_contributors = list(set(month_of_contributors))
                data[index] = deduplicated_monthly_contributors
                print('Month ' + str(index + 1) + ': ' + str(len(deduplicated_monthly_contributors)))
            deduplicated_contributors = data
        else:
            deduplicated_contributors = list(set(data))
            print('Total active developers in the past year: ' + str(len(deduplicated_contributors)))
        with open(out_file_name_with_path, 'w') as outfile:
            json.dump(deduplicated_contributors, outfile)
        return deduplicated_contributors


# Get last commit from JSON response, and create one list of all active in the past year, and one list of all contributors ever
# Write to file every n repos + repos viewed to not lose progress

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python3 contr.py [INPUTFILE.TOML]')
        sys.exit(1)
    loop = get_event_loop()
    try:
        c = Contributors('./output')
        loop.run_until_complete(c.get_contr_from_toml(sys.argv[1]))
    finally:
        loop.close()
