#!/usr/bin/env python
# encoding: utf-8
import sys
import os.path
from os.path import dirname, realpath
import subprocess
from datetime import datetime
import hashlib

import pystache

# Simple HTML mail template
TEMPLATE_FILE = os.path.join(dirname(realpath(__file__)), 'mail-template.html')
with open(TEMPLATE_FILE, 'r') as f:
    tpl = f.read().decode('utf-8')


# Contributors
def gravatar_url(email):
    gravatar_hash = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
    return u"http://www.gravatar.com/avatar/%s?s=32" % gravatar_hash

release_data = dict()


# Basic release info
release_data['project_url'] = sys.argv[1]
release_data['current_time'] = datetime.now().strftime("%a, %B %d, %Y, %H:%M")


# Release changelog
raw_git_log = subprocess.check_output(
    ['git', 'log', '--pretty=%h}%s}%an}%ae', '--since=1 week ago']).decode('utf-8')

tokenized_git_log = [line.split(u"}") for line in raw_git_log.strip().split(u"\n")]

release_data['git_log'] = [
    {
        'hash': entry[0],
        'message': entry[1],
        'author_name': entry[2],
        'author_email': entry[3],
        'author_gravatar': gravatar_url(entry[3])}
    for entry in tokenized_git_log
    if not entry[1].startswith('Merge')]


# Contributors
contributors = set([
    (entry['author_name'], entry['author_email'], entry['author_gravatar'])
    for entry in release_data['git_log']])
release_data['contributors'] = [
    {'name': name, 'email': email, 'gravatar': gravatar}
    for name, email, gravatar in contributors]

# Headers
print u"Subject: New deploy on %s" % release_data['project_url']
print u"MIME-Version: 1.0"
print u"Content-Type: text/html"
print u"Content-Disposition: inline"
# Mail content
print pystache.render(tpl, release_data).encode('utf-8')
