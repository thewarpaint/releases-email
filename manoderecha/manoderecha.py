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

        if r.status_code == 401:
            raise ManoderechaError("Authentication error")
        elif r.status_code == 404:
            return (404, None)
        else:
            try:
                return (r.status_code, json.loads(r.content))
            except ValueError:
                raise ManoderechaError("Invalid JSON from API")

    def get_task(self, task_id):
        return self.call('tasks/' + task_id)[1]

    def get_tasks(self, task_ids):
        task_ids = map(str, task_ids)
        tasks = task_ids and self.call('tasks/' + ','.join(task_ids))[1] or []

        if type(tasks) is not list:
            tasks = [tasks]

        return tasks

    def get_minute(self, minute_id):
        return self.call('minutes/' + minute_id)[1]

    def get_minutes(self, minute_ids):
        minute_ids = map(str, minute_ids)
        minutes = minute_ids and self.call('minutes/' + ','.join(minute_ids))[1] or []

        if type(minutes) is not list:
            minutes = [minutes]

        return minutes
