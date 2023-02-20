#!/usr/bin/env python3

import streamlit as st
from streamlit.elements.slider import Step
import xmltodict
from annotated_text import annotated_text
from enum import Enum
import state as s
from typing import List, TextIO

from toolz import groupby

import folium
from streamlit_folium import st_folium

# Text annot format:
# annotated_text(
#     "This ",
#     ("is", "verb"),
#     " some ",
#     ("annotated", "adj"),
#     ("text", "noun"),
#     " for those of ",
#     ("you", "pronoun"),
#     " who ",
#     ("like", "verb"),
#     " this sort of ",
#     ("thing", "noun"),
#     ".",
# )

PREFIX = "neroneview"


# @s.with_prop("rss", None, PREFIX)
@s.with_prop("item_idx", 0, PREFIX)
class State:
    item_idx: int
    # rss: TextIO

    def move_idx(self, amount=1):
        self.item_idx += amount


def conform_matches(matches):
    return [matches] if isinstance(matches, dict) else matches


# Define tags and their color
class EntityTag(Enum):
    EntityMatch = ("emm:entity", "#3AE")
    EntityGuess = ("emm:guess", "#CCE5FF")
    Timex = ("emm:timex", "#2F2")
    FullGeo = ("emm:fullgeo", "#CCCC00")
    Georss = ("emm:georss", "#FFFF66")

    @classmethod
    def tags(cls):
        return [x.value[0] for x in cls]


def flatten_matches(matches):
    """An entity may match at several start locations (@pos).
    This function conforms single and multi matches so they
    can be handled uniformly. It is a generator
    facotry, the returned generator can be iterated
    and wll yield a match dict per matched location per match
    """
    for match in matches:
        if "," in match["@pos"]:
            poss = match["@pos"].split(",")
            for p in poss:
                _m = match.copy()
                _m["@pos"] = p
                yield _m
        else:
            yield match


def get_entities_spans(matches: List[dict], tag: EntityTag):
    """Given a list of matches and a tag
    It reuturns a list os span Tuples (pos_start, pos_end, tag_type).
    Uses `flatten_matches` to handles entities that matched in several
    points of the text.
    """
    spans = []
    for v in flatten_matches(matches):
        pos = int(v["@pos"])
        text = v["#text"]
        spans.append((pos, pos + len(text), tag))
    return spans


def split_at_spans(string, spans):
    """Given the raw text `string` and a list
    of computed tag spans will build the annotated text
    format required for the visualization:
    List[ Str | Tuple[Str, Str] ]

    so a list of text segments that can be raw (Str)
    or annotated Tuple[Str,Str].

    """

    acc = []
    i = 0
    spans = sorted(spans, key=lambda x: x[0])
    for span in spans:
        # print(acc)
        if i != span[0]:
            acc.append(string[i : span[0]])

        if i > span[0]:
            continue

        match = string[span[0] : span[1]]

        tag_key = span[2].name
        tag_value = span[2].value
        if isinstance(tag_value, tuple):
            # tag_name = tag_value[0]
            tag_color = tag_value[1]
            acc.append((match, tag_key, tag_color))
        else:
            acc.append((match, tag_key))

        i = span[1]

    if i < len(string):
        acc.append(string[i:])

    return acc


controls = st.columns(4)

file = st.file_uploader(
    "upload file"
    # , key=s.k("rss", PREFIX)
)

state = State()


@st.experimental_memo
def load_items(f):
    print("loading from:", f)
    xml_doc = xmltodict.parse(f.read())
    channel = xml_doc["rss"]["channel"]
    items = channel["item"]
    items = [items] if isinstance(items, dict) else items

    return items


if file is not None:

    # parse the uploaded rss document
    items = load_items(file)

    st.header("NEROne Results")

    nav_buttons = st.columns(3)
    with nav_buttons[1]:
        if st.button("next"):
            state.move_idx(1)

    with nav_buttons[0]:
        if st.button("prev"):
            state.move_idx(-1)

    # st.multiselect("modules", options=EntityTag.tags())

    with nav_buttons[2]:
        modules = []
        active_modules = set()
        for t in EntityTag:
            # st.write(t.value)
            # st.text(t.value[0])
            label = t.value[0].replace(":", "-")
            module_active_key = f"active_mod_{label}"
            value = st.checkbox(label, key=module_active_key, value=True)
            if value:
                active_modules.add(t)
            modules.append(module_active_key)
            # st.checkbox(t, key=f"tag::{t}")

    # st.write(modules)
    # st.write(active_modules)

    i = state.item_idx
    item = items[i]

    # for i, item in enumerate(items[0:4]):

    st.json(item, expanded=False)
    st.markdown("## Item {} {}".format(i, item["guid"]))

    text = item["emm:text"]["#text"]

    if title := item.get("title"):
        text = title + ". " + text

    # annotated_text(text)

    # recognition_results = []
    recognition_spans = []

    entities = {}

    for t in EntityTag:
        if t in active_modules:
            ents = conform_matches(item.get(t.value[0], []))
            # recognition_results.extend(ents)
            entities[t.name] = ents

            spans = get_entities_spans(ents, t)
            if t == EntityTag.Timex:
                spans = map(lambda x: (x[0] - 1, x[1], x[2]), spans)

            recognition_spans.extend(spans)

    ann_text = split_at_spans(text, recognition_spans)

    st.markdown("### Annotated text")
    annotated_text(*ann_text)
    st.markdown("----")

    # for k, v in entities.items():
    #     # _ents = groupby("@id", v)
    #     st.header(k)
    #     st.write(v)

    if EntityTag.FullGeo.name in entities:
        st.header("map")

        fullgeos = entities[EntityTag.FullGeo.name]
        georss = entities.get(EntityTag.Georss.name, [])

        fullgeos.extend(georss)
        if not fullgeos:
            st.warning("No locations!")
        else:
            m = folium.Map(location=["0", "0"], zoom_start=1)

            with st.expander("log", expanded=False):
                for loc0 in fullgeos:
                    geo = [float(loc0["@lat"]), float(loc0["@lon"])]
                    name = loc0["@name"]

                    print("--->", name, geo)
                    if geo[0] == 0 and geo[1] == 0:
                        st.warning(f"Lat/Lon = 0,0 for {name} (id={loc0.get('@id')})")
                        continue

                    # st.write(loc0)
                    folium.Marker(
                        geo,
                        popup=f"Fullgeo@name: {name}",
                        tooltip=name,
                    ).add_to(m)
            st_folium(m, width=750)

    if enclosure := item.get("enclosure"):
        if url := enclosure.get("@url"):
            st.image(url)
