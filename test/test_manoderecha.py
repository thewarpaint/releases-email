# encoding: utf-8
import mock
import pytest

from manoderecha import Manoderecha, ManoderechaError, ManoderechaAuth


def make_task_json(id):
    template = u'{"id":%d,"projectId":279,"statusId":7,"responsibleId":265,"petitionerId":68,"priorityId":3,"creatorId":68,"groupId":null,"petitionId":null,"taskSourceId":null,"concept":"Botón de multiple selection en todas las cajas del record browser","creation":"2013-10-03 16:13:41","startDate":null,"deliveryDate":null,"estimatedTime":360,"chargeable":false,"visible":true,"payable":true,"locked":false,"ganttStartDate":"2013-10-17 00:00:00","ganttCompletionDate":"2013-10-17 00:00:00","isActive":false}'
    return template % (id or 1)

def make_minute_json(id):
    template = u'{"id":%d,"createdAt":"2013-06-19 23:17:42","creatorId":33,"name":"Pythonic minute","projectId":3,"date":"2014-10-29","startTime":1330,"endTime":1400}'
    return template % (id or 1)


@pytest.fixture
def a_task():
    task_json = make_task_json(1)
    return mock.Mock(content=task_json, status_code=200)


@pytest.fixture
def a_minute():
    minute_json = make_minute_json(1)
    return mock.Mock(content=minute_json, status_code=200)


def make_some_tasks(length):
    envelope = u"%s" if length==1 else u"[%s]"
    tasks_json = envelope % ",".join(
        make_task_json(id) for id in xrange(1, length + 1))
    return mock.Mock(content=tasks_json, status_code=200 if length > 0 else 404)


def make_some_minutes(length):
    envelope = u"%s" if length==1 else u"[%s]"
    minutes_json = envelope % ",".join(
        make_minute_json(id) for id in xrange(1, length + 1))
    return mock.Mock(content=minutes_json, status_code=200 if length > 0 else 404)


class TestAuth:
    def test_sets_header_correctly(self):
        request = mock.Mock(headers = {})
        auth = ManoderechaAuth('jair', 'j41r')
        auth(request)

        headers = request.headers
        assert 'Api-Authorization' in headers
        assert headers['Authorization'] == headers['Api-Authorization']


class TestCall:
    def test_get_is_default_method(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(content="{}")

            m = Manoderecha('user', 'password')
            m.call('some-url')

            assert get.called

    def test_non_json_response_raises_error(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(content="Invalid JSON")

            with pytest.raises(ManoderechaError):
                m = Manoderecha('user', 'password')
                m.call('some-url')


class TestGetTask:
    def test_gets_task(self, a_task):
        with mock.patch('requests.get') as get:
            get.return_value = a_task

            m = Manoderecha('user', 'password')
            task = m.get_task('1')

            # id from a_task fixture's JSON
            assert task['id'] == 1

    def test_return_none_if_task_doesnt_exist(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(status_code=404, content="Blah")

            m = Manoderecha('user', 'password')
            task = m.get_task('1')

            assert task is None


class TestGetTasks:
    def test_gets_tasks(self):
        with mock.patch('requests.get') as get:
            for length in [0, 1, 3]:
                get.return_value = make_some_tasks(length)

                m = Manoderecha('user', 'password')
                tasks = m.get_tasks(xrange(1, length + 1))

                assert len(tasks) == length
                assert [t['id'] for t in tasks] == range(1, length + 1)


class TestGetMinute:
    def test_gets_minute(self, a_minute):
        with mock.patch('requests.get') as get:
            get.return_value = a_minute

            m = Manoderecha('user', 'password')
            minute = m.get_minute('1')

            # id from a_minute fixture's JSON
            assert minute['id'] == 1

    def test_return_none_if_minute_doesnt_exist(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(status_code=404, content="Blah")

            m = Manoderecha('user', 'password')
            minute = m.get_minute('1')

            assert minute is None


class TestGetMinutes:
    def test_gets_minutes(self):
        with mock.patch('requests.get') as get:
            for length in [0, 1, 3]:
                get.return_value = make_some_minutes(length)

                m = Manoderecha('user', 'password')
                minutes = m.get_minutes(xrange(1, length + 1))

                assert len(minutes) == length
                assert [m['id'] for m in minutes] == range(1, length + 1)
