import mock

from jenkinsapi.custom_exceptions import NoBuildData

from releases import (
    basic_release_info, gravatar_hash, get_last_good_revision,
    get_raw_git_log, tokenize_git_log, parse_labels,
    get_contributors, get_tasks)


class TestBasicReleaseInfo:
    def test_sets_basic_release_info(test):
        """
        Checks basic release info is set
        """
        project_url = "http://example.com/some-project"
        result = basic_release_info(project_url)

        assert result['project_url'] == project_url
        assert result['nice_project_url'] == "example.com/some-project"
        assert 'current_time' in result


class TestGravatarHash:
    def test_computes_gravatar_hash(self):
        """
        Checks e-mail hashing happens properly
        """
        email = "jairtrejo@gmail.com"
        assert len(gravatar_hash(email)) == 32

    def test_normalizes_email_for_gravatar_hash(self):
        """
        Checks
        """
        email_one = "jairtrejo@gmail.com"
        email_two = "Jairtrejo@GMAIL.COM "
        assert gravatar_hash(email_one) == gravatar_hash(email_two)


class TestGetLastGoodRevision:
    def test_gets_last_good_revision_from_jenkins(self):
        with mock.patch('releases.Jenkins') as Jenkins:
            job = mock.Mock()
            job.get_last_good_build.return_value.get_revision.return_value = 'abcde'
            Jenkins.return_value.__getitem__.side_effect = lambda k: job

            assert get_last_good_revision('url', 'job') == 'abcde'

    def test_returns_none_when_there_are_no_previous_good_builds(self):
        with mock.patch('releases.Jenkins') as Jenkins:
            job = mock.Mock()
            job.get_last_good_build.return_value.get_revision.side_effect = NoBuildData
            Jenkins.return_value.__getitem__.side_effect = lambda k: job

            assert get_last_good_revision('url', 'job') is None


class TestGetRawGitLog:
    def tests_it_calls_git_log_with_the_supplied_identifier(self):
        with mock.patch('releases.subprocess') as subprocess:
            subprocess.check_output.return_value = u"The log".encode('utf-8')
            assert get_raw_git_log('abcde') == u"The log"

            args, kwargs = subprocess.check_output.call_args
            command = args[0]
            assert command[3].startswith('abcde')

    def test_it_doesnt_specify_log_start_with_no_identifier(self):
        with mock.patch('releases.subprocess') as subprocess:
            subprocess.check_output.return_value = u"The log".encode('utf-8')
            assert get_raw_git_log(None) == u"The log"

            args, kwargs = subprocess.check_output.call_args
            command = args[0]
            assert len(command) == 3


class TestTokenizeGitLog:
    def test_it_tokenizes_log_correctly(self):
        raw_git_log = "\n".join((
            u"abcde}Some message}Sherlock Holmes}sherlock@example.com",
            u"fghij}Other message}John Watson}watson@example.com",
        ))
        changelog = tokenize_git_log(raw_git_log)
        first = changelog[0]

        assert len(changelog) == 2
        assert first['hash'] == u"abcde"
        assert first['message'] == u"Some message"
        assert first['author_name'] == u"Sherlock Holmes"
        assert first['author_email'] == u"sherlock@example.com"
        assert 'author_gravatar' in first

    def test_it_removes_merge_commits(self):
        raw_git_log = "\n".join((
            u"abcde}Some message}Sherlock Holmes}sherlock@example.com",
            u"fghij}Merge commit}John Watson}watson@example.com",
        ))
        changelog = tokenize_git_log(raw_git_log)

        assert len(changelog) == 1
        assert changelog[0]['author_email'] == u"sherlock@example.com"


class TestParseLabels:
    def test_it_parses_labels_with_gitlabels(self):
        with mock.patch('releases.get_labels') as get_labels:
            get_labels.return_value = {'label': 'arg'}
            parsed = parse_labels([{'message': 'Abc'}])
            assert parsed[0]['labels'] == get_labels.return_value

    def test_it_parses_messages_with_gitlabels(self):
        with mock.patch('releases.remove_labels') as remove_labels:
            remove_labels.return_value = u"Message"
            parsed = parse_labels([{'message': 'Abc'}])
            assert parsed[0]['message'] == u"Message"

    def test_it_returns_empty_list_for_empty_log(self):
        parsed = parse_labels([])
        assert len(parsed) == 0


class TestGetContributors:
    def test_it_gets_all_contributors(self):
        raw_git_log = "\n".join((
            u"abcde}Some message}Sherlock Holmes}sherlock@example.com",
            u"fghij}Other message}John Watson}watson@example.com",
        ))
        changelog = tokenize_git_log(raw_git_log)
        contributors = get_contributors(changelog)

        assert len(contributors) == 2
        assert (set(c['email'] for c in contributors) ==
                set(['sherlock@example.com', 'watson@example.com']))

    def test_it_merges_contributors_by_gravatar(self):
        raw_git_log = "\n".join((
            u"abcde}Some message}Sherlock Holmes}sherlock@example.com",
            u"fghij}Other message}John Watson}Watson@example.com",
            u"klmno}New message}Sherlock Holmes}sherlock@example.com",
            u"pqrst}Final message}John Watson}watson@example.com",
        ))
        changelog = tokenize_git_log(raw_git_log)
        contributors = get_contributors(changelog)

        assert len(contributors) == 2
        assert (set(c['email'] for c in contributors) ==
                set(['sherlock@example.com', 'watson@example.com']))


class TestGetTasks:
    def test_it_gets_tasks_from_manoderecha(self):
        raw_git_log = "\n".join((
            u"abcde}Some message}Sherlock Holmes}sherlock@example.com",
            u"fghij}(md:123) Other message}John Watson}Watson@example.com",
            u"klmno}New message}Sherlock Holmes}sherlock@example.com",
            u"pqrst}(md:456) Final message}John Watson}watson@example.com",
        ))
        changelog = tokenize_git_log(raw_git_log)
        changelog = parse_labels(changelog)
        md = mock.Mock()
        md.get_tasks.return_value = [{'isActive': True}]
        tasks = get_tasks(changelog, md)
        assert tasks == md.get_tasks.return_value

        args, kwargs = md.get_tasks.call_args
        task_ids = args[0]
        assert set(['123', '456']) == set(task_ids)
