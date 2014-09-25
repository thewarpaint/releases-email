# encoding: utf-8
import mock
import pytest

from jira import Jira, JiraError


def make_issue_json(id):
    template = u'{"id":%d,"key":"ABC-123","fields":{"summary":"Release email JIRA integration","created":"2014-09-25T13:46:03.000+0000","description":"Release email JIRA integration","subtasks":[]}}'
    return template % (id or 1)


@pytest.fixture
def an_issue():
    issue_json = make_issue_json(1)
    return mock.Mock(content=issue_json, status_code=200)


class TestCall:
    def test_get_is_default_method(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(content="{}")

            j = Jira('user', 'password', 'http://jira.com/')
            j.call('some-url')

            assert get.called

    def test_non_json_response_raises_error(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(status_code=200, content="Not JSON")

            with pytest.raises(JiraError):
                j = Jira('user', 'password', 'http://jira.com/')
                j.call('some-url')

    def test_unauthorized_request_raises_error(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(status_code=401)

            with pytest.raises(JiraError):
                j = Jira('user', 'password', 'http://jira.com/')
                j.call('some-url')


class TestGetIssue:
    def test_gets_issue(self, an_issue):
        with mock.patch('requests.get') as get:
            get.return_value = an_issue

            j = Jira('user', 'password', 'http://jira.com/')
            issue = j.get_issue('1')

            # id from an_issue fixture's JSON
            assert issue[1]['id'] == 1

    def test_return_none_if_issue_doesnt_exist(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(status_code=404, content="Blah")

            j = Jira('user', 'password', 'http://jira.com/')
            issue = j.get_issue('1')

            assert issue[1] is None
