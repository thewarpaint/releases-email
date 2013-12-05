# encoding: utf-8
import mock
import pytest

from manoderecha import Manoderecha, ManoderechaError


@pytest.fixture
def a_task():
    task_json = u'{"id":67995,"projectId":279,"statusId":7,"responsibleId":265,"petitionerId":68,"priorityId":3,"creatorId":68,"groupId":null,"petitionId":null,"taskSourceId":null,"concept":"Botón de multiple selection en todas las cajas del record browser","creation":"2013-10-03 16:13:41","startDate":null,"deliveryDate":null,"estimatedTime":360,"chargeable":false,"visible":true,"payable":true,"locked":false,"ganttStartDate":"2013-10-17 00:00:00","ganttCompletionDate":"2013-10-17 00:00:00","isActive":false}'
    return mock.Mock(content=task_json, status_code=200)


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
            task = m.get_task('67995')

            # id from a_task fixture's JSON
            assert task['id'] == 67995

    def test_return_none_if_task_doesnt_exist(self):
        with mock.patch('requests.get') as get:
            get.return_value = mock.Mock(status_code=404, content="Blah")

            m = Manoderecha('user', 'password')
            task = m.get_task('67995')

            assert task is None
