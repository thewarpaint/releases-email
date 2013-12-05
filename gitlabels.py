import re

def get_labels(message):
    labels = {}

    match = re.match("\(([A-z0-9\s\-_*+:]+)\)", message)
    if match:
        for l in match.group(1).split(' '):
            label = l.split(':', 1)
            labels[label[0]] = label[1] if len(label) > 1 else u''

    return labels
