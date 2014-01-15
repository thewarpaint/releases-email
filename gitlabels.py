# encoding: utf-8

# We're here parsing the use of “labels” on commit messages.
# See: http://ell.io/tt$.gitlabels
import re

LABELS_EXPRESSION = re.compile("^\((?:([^):,\s]+(?::\"[^)\"]*\"|:[^)\",\s]*)?)(?:[, \\t]+|(?=\))))+\)")


def get_labels(message):
    labels = {}

    match = LABELS_EXPRESSION.match(message)
    if match:
        for l in re.split("[, \t]+", match.group(0).strip("()")):
            label = l.split(':', 1)
            labels[label[0]] = label[1].strip('"') if len(label) > 1 else u''

    return labels


def remove_labels(message):
    return LABELS_EXPRESSION.sub('', message).strip()
