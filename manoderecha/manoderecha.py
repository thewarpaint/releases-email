import json

import requests

from auth import ManoderechaAuth

API_BASE = 'http://manoderecha.net/md/index.php/api/v1/'


class ManoderechaError(Exception):
    pass


class Manoderecha(object):
    def __init__(self, user, password):
        self.auth = ManoderechaAuth(user, password)

    def call(self, url, method='get', **data):
        if data:
            r = getattr(requests, method)(API_BASE + url, data, auth=self.auth)
        else:
            r = getattr(requests, method)(API_BASE + url, auth=self.auth)
        if r.status_code != 404:
            try:
                return (r.status_code, json.loads(r.content))
            except ValueError:
                raise ManoderechaError("Invalid JSON from API")
        else:
            return (404, None)

    def get_task(self, task_id):
        return self.call('tasks/' + task_id)[1]

    def get_tasks(self, task_ids):
        tasks = self.call('tasks/' + ','.join(task_ids))[1]
        if type(tasks) is not list:
            return [tasks]
