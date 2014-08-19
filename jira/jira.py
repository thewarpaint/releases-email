from requests.auth import HTTPBasicAuth

import json

import requests


class JiraError(Exception):
    pass

class Jira(object):
    def __init__(self, username, password, api_base):
    	self.api_base = api_base
        self.auth = HTTPBasicAuth(username, password)

    def call(self, url, method='get', **data):
        if data:
            r = getattr(requests, method)(self.api_base + url, data, auth=self.auth)
        else:
            r = getattr(requests, method)(self.api_base + url, auth=self.auth)

        if r.status_code == 401:
            raise JiraError("Authentication error")
        elif r.status_code == 404:
            return (404, None)
        else:
            try:
                return (r.status_code, json.loads(r.content))
            except ValueError:
                raise JiraError("Invalid JSON from API")

    def get_issue(self, issue_id):
        return self.call("issue/" + issue_id + ".json")
