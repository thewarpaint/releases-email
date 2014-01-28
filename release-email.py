#!/usr/bin/env python
# encoding: utf-8
import sys
import os
from os.path import dirname, realpath

import pystache

from manoderecha.manoderecha import Manoderecha
from releases import (
    basic_release_info, get_last_good_revision,
    get_raw_git_log, tokenize_git_log, parse_labels,
    get_contributors, get_tasks)


# Parameters
jenkins_url = sys.argv[1]
project_url = sys.argv[2]
job_name = sys.argv[3]
MANODERECHA_USER = os.environ['MANODERECHA_USER']
MANODERECHA_PASSWORD = os.environ['MANODERECHA_PASSWORD']


# Simple HTML mail template
TEMPLATE_FILE = os.path.join(dirname(realpath(__file__)), 'mail-template.html')
with open(TEMPLATE_FILE, 'r') as f:
    tpl = f.read().decode('utf-8')
# Rendering context

release_data = basic_release_info(project_url)

since = get_last_good_revision(jenkins_url, job_name)
raw_log = get_raw_git_log(since)
release_data['git_log'] = parse_labels(tokenize_git_log(raw_log))

release_data['contributors'] = get_contributors(release_data['git_log'])

md = Manoderecha(MANODERECHA_USER, MANODERECHA_PASSWORD)
release_data['tasks'] = get_tasks(release_data['git_log'], md)

# Headers
print u"Subject: New deployment to %s" % release_data['nice_project_url']
print u"MIME-Version: 1.0"
print u"Content-Type: text/html"
print u"Content-Disposition: inline"
# Mail content
print pystache.render(tpl, release_data).encode('utf-8')
