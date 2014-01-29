from datetime import datetime
from urlparse import urlparse
import subprocess
import hashlib

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.custom_exceptions import NoBuildData

from gitlabels import get_labels, remove_labels

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
            {'hash': entry[0],
            'message': entry[1],
            'author_name': entry[2],
            'author_email': entry[3],
            'author_gravatar': gravatar_hash(entry[3])}
        for entry in tokenized
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
