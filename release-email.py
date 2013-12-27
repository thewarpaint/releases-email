#!/usr/bin/env python
# encoding: utf-8
import sys
import os
from urlparse import urlparse
from os.path import dirname, realpath
import subprocess
from datetime import datetime
import hashlib
from gitlabels import get_labels, remove_labels
from manoderecha.manoderecha import Manoderecha

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import NoBuildData
import pystache


jenkins_url = sys.argv[1]
project_url = sys.argv[2]
job_name = sys.argv[3]
MANODERECHA_USER = os.environ['MANODERECHA_USER']
MANODERECHA_PASSWORD = os.environ['MANODERECHA_PASSWORD']


# Simple HTML mail template
TEMPLATE_FILE = os.path.join(dirname(realpath(__file__)), 'mail-template.html')
with open(TEMPLATE_FILE, 'r') as f:
    tpl = f.read().decode('utf-8')

release_data = dict()


# Basic release info
release_data['project_url'] = project_url
release_data['current_time'] = datetime.now().strftime("%a, %B %d, %Y, %H:%M")
release_data['nice_project_url'] = "".join(urlparse(release_data['project_url'])[1:])

# Release changelog
def gravatar_hash(email):
    normalized_email = email.strip().lower().encode('utf-8')
    gravatar_hash = hashlib.md5(normalized_email).hexdigest()
    return gravatar_hash

git_log_command = ['git', 'log', '--pretty=%h}%s}%an}%ae']

try:
    jenkins = Jenkins(jenkins_url)
    since = jenkins[job_name].get_last_good_build().get_revision()
    git_log_command.append('%s..' % since)
except NoBuildData:
    pass

raw_git_log = subprocess.check_output(git_log_command).decode('utf-8')

tokenized_git_log = [
    line.split(u"}") for line in raw_git_log.strip().split(u"\n") if line]

release_data['git_log'] = [
    {
        'hash': entry[0],
        'message': entry[1],
        'author_name': entry[2],
        'author_email': entry[3],
        'author_gravatar': gravatar_hash(entry[3])}
    for entry in tokenized_git_log
    if not entry[1].startswith('Merge')]


# Contributors
contributors = set([
    (entry['author_name'], entry['author_email'], entry['author_gravatar'])
    for entry in release_data['git_log']])
release_data['contributors'] = [
    {'name': name, 'email': email, 'gravatar': gravatar}
    for name, email, gravatar in contributors]


# Tasks

md = Manoderecha(MANODERECHA_USER, MANODERECHA_PASSWORD)

task_ids = set()
for entry in release_data['git_log']:
    labels = get_labels(entry['message'])

    entry['labels'] = ["%s:%s" % (k, v) for k, v in labels.items()]
    entry['message'] = remove_labels(entry['message'])

    if 'md' in labels:
        task_ids.update(labels['md'].split(','))

release_data['tasks'] = md.get_tasks(task_ids)
for task in release_data['tasks']:
    task['status'] = '>' if task['isActive'] else '.'

# Headers
print u"Subject: New deployment to %s" % release_data['nice_project_url']
print u"MIME-Version: 1.0"
print u"Content-Type: text/html"
print u"Content-Disposition: inline"
# Mail content
print pystache.render(tpl, release_data).encode('utf-8')
