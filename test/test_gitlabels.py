from gitlabels import get_labels, remove_labels


def test_gets_alphanumeric_labels():
    message = u"(one two three3) A test message"
    labels = get_labels(message)
    assert sorted(labels) == ['one', 'three3', 'two']


def test_gets_labels_with_special_characters():
    message = u"(one two - _ *)"
    labels = get_labels(message)
    assert sorted(labels) == ['*', '-', '_', 'one', 'two']


def test_returns_empty_list_for_non_labeled():
    messages = [
        u"A message without labels",
        u"( A malformed message",
        u"(invalid chars in labels ~)",
    ]
    for message in messages:
        labels = get_labels(message)
        assert sorted(labels) == []


def test_returns_arguments_for_labels_with_it():
    message = "(md:1864 xy:123:125 false -) A message with an argument"
    labels = get_labels(message)

    assert labels['md'] == '1864'
    assert labels['xy'] == '123:125'


def test_can_remove_labels():
    labeled_messages = [
        "(one two three) Message",
        "(one) Message",
    ]
    for message in labeled_messages:
        assert remove_labels(message) == 'Message'

    assert remove_labels('(abc) Two sets (def ghi)') == "Two sets (def ghi)"


def test_leaves_unlabeled_untouched():
    unlabeled_messages = [
        "A simple message",
        "() No real labels",
        "Misplaced (abc def ghi) labels",
    ]
    for message in unlabeled_messages:
        assert remove_labels(message) == message.strip()
