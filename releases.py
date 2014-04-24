import argparse
import hashlib
import os
import subprocess
from datetime import datetime
from os.path import dirname, realpath
from urlparse import urlparse
import re

import pystache
from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import NoBuildData

from gitlabels import get_labels, remove_labels
from manoderecha.manoderecha import Manoderecha


def basic_release_info(project_url):
    """
    Returns basic information for this release of the project.

    Args:
        project_url: Live url for the project.

    Returns:
        A dictionary with project url, a nicer format of the same and the
        current time.
    """
    return {
        'project_url': project_url,
        'current_time': datetime.now().strftime("%a, %B %d, %Y, %H:%M"),
        'nice_project_url': "".join(urlparse(project_url)[1:]),
    }


def gravatar_hash(email):
    """
    Computes gravatar's hash from an user email.

    Args:
        email: The user's email.

    Returns:
        A gravatar md5 hash.
    """
    normalized_email = email.strip().lower().encode('utf-8')
    gravatar_hash = hashlib.md5(normalized_email).hexdigest()
    return gravatar_hash


def get_last_good_revision(jenkins_url, job_name):
    """
    Gets last good revision for the project.

    Args:
        jenkins_url: URL of the jenkins server.
        job_name: Job name for the project.

    Returns:
        A revision identifier, or None if it couldn't be retrieved.
    """
    try:
        jenkins = Jenkins(jenkins_url)
        return jenkins[job_name].get_last_good_build().get_revision()
    except NoBuildData:
        return None


def get_raw_git_log(since):
    """
    Calls git log since the specified identifier (or the initial commit) and
    returns its output.

    Args:
        since (optional): A git reference to start the log from.

    Returns:
        The output of the git log command as unicode, fields delimited with "}".
        Fields are: hash, message, author name and author e-mail.
    """
    git_log_command = ['git', 'log', '--pretty=%h}%s}%an}%ae']
    if since:
        git_log_command.append('%s..' % since)
    return subprocess.check_output(git_log_command).decode('utf-8')


def tokenize_git_log(raw_log):
    """
    Tokenizes a raw git log.

    It gets rid of Merge commits and adds Gravatar hash.

    Args:
        raw_log: A raw git log in the format returned by get_raw_git_log.

    Returns:
        A dictionary with the relevant fields.
    """
    tokenized = [l.split(u"}") for l in raw_log.strip().split(u"\n") if l]

    return [
        {
            'hash': entry[0],
            'message': entry[1],
            'author_name': entry[2],
            'author_email': entry[3],
            'author_gravatar': gravatar_hash(entry[3])
        } for entry in tokenized
        if not entry[1].startswith('Merge')]


def parse_labels(git_log):
    """
    Annotates git log entries with their gitlabels.

    Args:
        git_log: A git log tokenized by tokenize_git_log.

    Returns:
        The same git log with each entry annotated with:
        - labels: A dictionary of labels.
        - pretty_labels: A list of label representations.
        - message: The unlabeled commit message.
    """
    for entry in git_log:
        labels = get_labels(entry['message'])
        entry['labels'] = labels
        entry['pretty_labels'] = sorted(
            "%s:%s" % (k, v) if v else k for k, v in labels.items())
        entry['message'] = remove_labels(entry['message'])

    return git_log


def remove_ignored(git_log, ignore_tags):
    """
    Removes from the log commit messages with labels in ignore_tags.

    Args:
        git_log: A git log labeled by parse_labels
        ignore_tags: A list of tags to ignore.

    Returns:
        The same git log without entries with tags in ignore_tags.
    """
    return filter(
        lambda l: len(set(l['labels'].keys()) & set(ignore_tags)) == 0, git_log)


def links_to_commits(git_log, git_url):
    """
    Adds links to commits on supported web services.

    Args:
        git_log: A git log labeled by parse_labels
        git_url: Git remote url

    Returns:
        The same git log with entries tagged with a 'commit_url' field.
    """
    exp = re.compile(r'(?:https://|git@|git://)([\.\w]+)[:/](.+).git')
    server_to_url = {
        'github.com': 'http://github.com/{repo}/commit/{commit}',
        'cincoovnis.com': 'http://gitweb.cincoovnis.com/?p={repo}.git;a=commit;h={commit}',
    }
    server, repo = exp.match(git_url).groups()

    if server not in server_to_url:
        return git_log
    else:
        pattern = server_to_url[server]

    for entry in git_log:
        entry['commit_url'] = pattern.format(repo=repo, commit=entry['hash'])

    return git_log


def get_contributors(git_log):
    """
    Gets a list of contributors from the git log information.

    Args:
        git_log: A git log tokenized by tokenize_git_log.

    Returns:
        A list of contributors, each a dictionary with fields 'name', 'email'
        and 'gravatar'.
    """
    contributors = {
        entry['author_gravatar']: (entry['author_name'], entry['author_email'])
        for entry in git_log}

    return [
        {'name': info[0], 'email': info[1], 'gravatar': gravatar}
        for gravatar, info in contributors.items()]


def get_tasks(git_log, md):
    """
    Gets a list of tasks from the relevant gitlabels.

    Args:
        git_log: A git log tokenized and label-parsed.
        md: A manoderecha API client.

    Returns:
        A list of manoderecha tasks
    """
    task_ids = set()
    for entry in git_log:
        labels = entry['labels']
        if 'md' in labels:
            task_ids.update(labels['md'].split(','))
    tasks = md.get_tasks(task_ids)
    for task in tasks:
        task['status'] = '>' if task['isActive'] else '.'

    return tasks


def get_minutes(git_log, md):
    """
    Gets a list of minutes from the relevant gitlabels.

    Args:
        git_log: A git log tokenized and label-parsed.
        md: A manoderecha API client.

    Returns:
        A list of manoderecha minutes
    """
    minute_ids = set()
    for entry in git_log:
        labels = entry['labels']
        if 'minute' in labels:
            minute_ids.update(labels['minute'].split(','))
    minutes = md.get_minutes(minute_ids)

    return minutes


def configure_argparser():
    parser = argparse.ArgumentParser(description=u"Generate a changelog e-mail whenever you deploy")
    parser.add_argument('jenkins_url', help=u"Jenkins server URL")
    parser.add_argument('job_name', help=u"Jenkins job name")
    parser.add_argument('project_url', help=u"project's URL")

    parser.add_argument('--ignore-tags', nargs='+',
                        help=u"List of tags to ignore. Commit messages that include those tags will be eliminated from the changelog")

    parser.add_argument('--git-url',
                        help=u"Git url for the project. Depending on the server, can be used to link to commits.")

    parser.add_argument('--manoderecha-user',
                        default=os.environ.get('MANODERECHA_USER'),
                        help=u"manoderecha user for task fetching. Can be set as environment variable")
    parser.add_argument('--manoderecha-password',
                        default=os.environ.get('MANODERECHA_PASSWORD'),
                        help=u"manoderecha password for task fetching. Can be set as environment variable")

    return parser


def run():
    # Configuration
    parser = configure_argparser()
    config = parser.parse_args()

    # Simple HTML mail template
    TEMPLATE_FILE = os.path.join(
        dirname(realpath(__file__)), 'mail-template.html')
    with open(TEMPLATE_FILE, 'r') as f:
        tpl = f.read().decode('utf-8')

    # Basic release info
    release_data = basic_release_info(config.project_url)

    # Changelog
    since = get_last_good_revision(config.jenkins_url, config.job_name)
    raw_log = get_raw_git_log(since)
    with_parsed_labels = parse_labels(tokenize_git_log(raw_log))
    git_log = remove_ignored(with_parsed_labels, config.ignore_tags or [])
    if config.git_url:
        git_log = links_to_commits(git_log, config.git_url)

    release_data['git_log'] = git_log

    # Contributors
    release_data['contributors'] = get_contributors(git_log)

    # Manoderecha
    md = Manoderecha(config.manoderecha_user, config.manoderecha_password)
    release_data['tasks'] = get_tasks(git_log, md)
    release_data['minutes'] = get_minutes(git_log, md)

    # Headers
    print u"Subject: New deployment to %s" % release_data['nice_project_url']
    print u"MIME-Version: 1.0"
    print u"Content-Type: text/html"
    print u"Content-Disposition: inline"
    # Mail content
    print pystache.render(tpl, release_data).encode('utf-8')
