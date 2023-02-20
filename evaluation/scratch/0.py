#!/usr/bin/env python3
import pandas as pd
from typing import List
import xmltodict
import os
import re

NERONE = "/home/bandoos/repos/nerone_mvn"
file = os.path.join(
    NERONE,
    "test/evaluation/resources/corpora/en/CoNNL2003/train/control/eng.train.control.united.xml",
)

line_re = r"\[(\d+)] (.+) \[(\d+)\]$"
_line_re = re.compile(line_re)


def read_xml_item(path):
    with open(path, "rb") as f:
        data = xmltodict.parse(f)
        item = data["rss"]["channel"]["item"]
        return item


# with open(file, "rb") as f:
#     data = xmltodict.parse(f)

# item = data["rss"]["channel"]["item"]

item = read_xml_item(file)

# print(len(item["ORGANIZATION"]))

# example = item["ORGANIZATION"][0]

# start, text, end = re.match(line_re, example).groups()


def parse_tag_content(line):
    r = _line_re.match(line)
    if r is not None:
        start, text, end = r.groups()
        return (start, end, text)


# orgs = list(map(parse_tag_content, item["ORGANIZATION"]))


def tabulate(item, tags: List[str]):
    records = []
    for tag in tags:
        conts = map(parse_tag_content, item[tag])
        conts = filter(lambda x: x, conts)
        with_tag = map(lambda xs: (tag, *xs), conts)
        records.extend(with_tag)

    return pd.DataFrame(records, columns=["tag", "start", "end", "text"])


df = tabulate(item, ["ORGANIZATION", "PERSON", "LOCATION"])

df.to_csv("./evaluation-set-test.csv", index_label="index")

# What would be the result of `a = lambda x: x+1*2; a(3)`
# The result would be 7. The lambda function defines a simple mathematical
# operation on the input value of x, which in this case is 3. The operation is
# to add 1 to the value of x, then multiply that sum by 2. Therefore, the final
# result of the function when called with an input of 3 is (3+1)2 = 42 = 7.
