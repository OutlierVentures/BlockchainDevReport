# -*- coding: utf-8 -*-
import datetime
from github import Github, GithubException


class GithubPersonalAccessTokenHelper():
    def __init__(self, pats):
        if not isinstance(pats, list):
            raise Exception("PATs must be an array")
        self.pats = []
        self._initialize_pats(pats)
        self.last_sent_token = 'fff'

    def _initialize_pats(self, pats):
        for (_, pat) in enumerate(pats):
            try:
                gh = Github(pat)
                rate_limit = gh.get_rate_limit()

                self.pats.append(pat)
            except GithubException as e:
                # Probably a bad access token
                print("Error while querying for personal access token")
                print(e)
                continue
        # Need atleast one valid personal access token
        assert len(self.pats) > 0

    def get_access_token(self):
        min_sleep_time_secs = None
        for (_, token) in enumerate(self.pats):
            gh = Github(token)
            rate_limit = gh.get_rate_limit()
            if rate_limit.core.remaining > 0 and self.last_sent_token != token:
                self.last_sent_token = token
                return {
                    'token': token
                }
            rate_limit_reset_time = rate_limit.core.reset
            time_delta = abs(rate_limit_reset_time - datetime.datetime.utcnow())
            if min_sleep_time_secs is None:
                min_sleep_time_secs = time_delta.total_seconds()
                continue
            if min_sleep_time_secs < time_delta.total_seconds():
                min_sleep_time_secs = time_delta.total_seconds()

        print("All access tokens have been rate limited")
        print("Min sleep time: ", min_sleep_time_secs)
        return {
            'token': None,
            'sleep_time_secs': min_sleep_time_secs
        }