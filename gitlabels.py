import re

LABELS_EXPRESSION = re.compile("^\(([A-z0-9\s\-_*+:]+)\)")

def get_labels(message):
    labels = {}

    match = LABELS_EXPRESSION.match(message)
    if match:
        for l in match.group(1).split(' '):
            label = l.split(':', 1)
            labels[label[0]] = label[1] if len(label) > 1 else u''

    return labels

def remove_labels(message):
    return LABELS_EXPRESSION.sub('', message).strip()
