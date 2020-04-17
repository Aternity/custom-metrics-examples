"""This file uses code modified from the Prometheus Client Library which is available under an Apache 2.0
#license. For details, see https://github.com/prometheus/client_python"""

import re
from collections import namedtuple

try:
    import StringIO
except ImportError:
    # Python 3
    import io as StringIO

class Metric(object):
    def __init__(self, name, documentation, typ):
        self.name = name
        self.documentation = documentation
        self.typ = typ

class Timestamp(object):
    """A nanosecond-resolution timestamp."""

    def __init__(self, sec, nsec):
        if nsec < 0 or nsec >= 1e9:
            raise ValueError("Invalid value for nanoseconds in Timestamp: {0}".format(nsec))
        if sec < 0:
            nsec = -nsec
        self.sec = int(sec)
        self.nsec = int(nsec)

    def __str__(self):
        return "{0}.{1:09d}".format(self.sec, self.nsec)

    def __repr__(self):
        return "Timestamp({0}, {1})".format(self.sec, self.nsec)

    def __float__(self):
        return float(self.sec) + float(self.nsec) / 1e9

    def __eq__(self, other):
        return type(self) == type(other) and self.sec == other.sec and self.nsec == other.nsec

    def __ne__(self, other):
        return not self == other

    def __gt__(self, other):
        return self.sec > other.sec or self.nsec > other.nsec


# Timestamp and exemplar are optional.
# Value can be an int or a float.
# Timestamp can be a float containing a unixtime in seconds,
# a Timestamp object, or None.
# Exemplar can be an Exemplar object, or None.
Sample = namedtuple('Sample', ['name', 'labels', 'value', 'timestamp', 'exemplar'])
Sample.__new__.__defaults__ = (None, None)

Exemplar = namedtuple('Exemplar', ['labels', 'value', 'timestamp'])
Exemplar.__new__.__defaults__ = (None,)

def text_string_to_metric_families(text):
    """Parse Prometheus text format from a unicode string.
    See text_fd_to_metric_families.
    """
    for metric_family in text_fd_to_metric_families(StringIO.StringIO(text)):
        metric_family


ESCAPE_SEQUENCES = {
    '\\\\': '\\',
    '\\n': '\n',
    '\\"': '"',
}


def replace_escape_sequence(match):
    return ESCAPE_SEQUENCES[match.group(0)]


HELP_ESCAPING_RE = re.compile(r'\\[\\n]')
ESCAPING_RE = re.compile(r'\\[\\n"]')


def _replace_help_escaping(s):
    return HELP_ESCAPING_RE.sub(replace_escape_sequence, s)


def _replace_escaping(s):
    return ESCAPING_RE.sub(replace_escape_sequence, s)


def _is_character_escaped(s, charpos):
    num_bslashes = 0
    while (charpos > num_bslashes and
           s[charpos - 1 - num_bslashes] == '\\'):
        num_bslashes += 1
    return num_bslashes % 2 == 1


def _parse_labels(labels_string):
    labels = {}
    # Return if we don't have valid labels
    if "=" not in labels_string:
        return labels

    escaping = False
    if "\\" in labels_string:
        escaping = True

    # Copy original labels
    sub_labels = labels_string
    try:
        # Process one label at a time
        while sub_labels:
            # The label name is before the equal
            value_start = sub_labels.index("=")
            label_name = sub_labels[:value_start]
            sub_labels = sub_labels[value_start + 1:].lstrip()
            # Find the first quote after the equal
            quote_start = sub_labels.index('"') + 1
            value_substr = sub_labels[quote_start:]

            # Find the last unescaped quote
            i = 0
            while i < len(value_substr):
                i = value_substr.index('"', i)
                if not _is_character_escaped(value_substr, i):
                    break
                i += 1

            # The label value is between the first and last quote
            quote_end = i + 1
            label_value = sub_labels[quote_start:quote_end]
            # Replace escaping if needed
            if escaping:
                label_value = _replace_escaping(label_value)
            labels[label_name.strip()] = label_value

            # Remove the processed label from the sub-slice for next iteration
            sub_labels = sub_labels[quote_end + 1:]
            next_comma = sub_labels.find(",") + 1
            sub_labels = sub_labels[next_comma:].lstrip()

        return labels

    except ValueError:
        raise ValueError("Invalid labels: %s" % labels_string)


# If we have multiple values only consider the first
def _parse_value_and_timestamp(s):
    s = s.lstrip()
    separator = " "
    if separator not in s:
        separator = "\t"
    values = [value.strip() for value in s.split(separator) if value.strip()]
    if not values:
        return float(s), None
    value = float(values[0])
    timestamp = (float(values[-1])/1000) if len(values) > 1 else None
    return value, timestamp


def _parse_sample(text):
    # Detect the labels in the text
    try:
        label_start, label_end = text.index("{"), text.rindex("}")
        # The name is before the labels
        name = text[:label_start].strip()
        # We ignore the starting curly brace
        label = text[label_start + 1:label_end]
        # The value is after the label end (ignoring curly brace and space)
        value, timestamp = _parse_value_and_timestamp(text[label_end + 2:])
        return Sample(name, _parse_labels(label), value, timestamp)

    # We don't have labels
    except ValueError:
        # Detect what separator is used
        separator = " "
        if separator not in text:
            separator = "\t"
        name_end = text.index(separator)
        name = text[:name_end]
        # The value is after the name
        value, timestamp = _parse_value_and_timestamp(text[name_end:])
        return Sample(name, {}, value, timestamp)

def build_metric(name, documentation, typ, samples):
    # Munge counters into OpenMetrics representation
    # used internally.
    if typ == 'counter':
        if name.endswith('_total'):
            name = name[:-6]
        else:
            new_samples = []
            for s in samples:
                new_samples.append(Sample(s[0] + '_total', *s[1:]))
                samples = new_samples
    metric = Metric(name, documentation, typ)
    metric.samples = samples
    return metric

def text_fd_to_metric_families(fd):
    name = ''
    documentation = ''
    typ = 'untyped'
    samples = []
    allowed_names = []
    metrics = []
    for line in fd:
        line = line.strip()
        if line.startswith('#'):
            parts = line.split(None, 3)
            if len(parts) < 2:
                continue
            if parts[1] == 'HELP':
                if parts[2] != name:
                    if name != '':
                        metrics.append(build_metric(name, documentation, typ, samples))
                    # New metric
                    name = parts[2]
                    typ = 'untyped'
                    samples = []
                    allowed_names = [parts[2]]
                if len(parts) == 4:
                    documentation = _replace_help_escaping(parts[3])
                else:
                    documentation = ''
            elif parts[1] == 'TYPE':
                if parts[2] != name:
                    if name != '':
                        metrics.append(build_metric(name, documentation, typ, samples))
                    # New metric
                    name = parts[2]
                    documentation = ''
                    samples = []
                typ = parts[3]
                allowed_names = {
                    'counter': [''],
                    'gauge': [''],
                    'summary': ['_count', '_sum', ''],
                    'histogram': ['_count', '_sum', '_bucket'],
                }.get(typ, [''])
                allowed_names = [name + n for n in allowed_names]
            else:
                # Ignore other comment tokens
                pass
        elif line == '':
            # Ignore blank lines
            pass
        else:
            sample = _parse_sample(line)
            if sample.name not in allowed_names:
                if name != '':
                    metrics.append(build_metric(name, documentation, typ, samples))
                # New metric, yield immediately as untyped singleton
                name = ''
                documentation = ''
                typ = 'untyped'
                samples = []
                allowed_names = []
                metrics.append(build_metric(sample[0], documentation, typ, [sample]))
            else:
                samples.append(sample)

    if name != '':
        metrics.append(build_metric(name, documentation, typ, samples))

    return metrics

