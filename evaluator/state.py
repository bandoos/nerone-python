#!/usr/bin/env python3

import streamlit as st


# apporach would be even better
# by creating a streamlit descriptor/propery directly
# (less loc)
# class session_state_prop:
#     def __init__(self, name, prefix) -> None:
#         self.name = name
#         self.key = "{}_{}".format(prefix, name)

#     def __get__(self):
#         return st.session_state[self.key]


def k(name, prefix):
    return f"{prefix}_{name}"


def mk_getter(name, prefix):
    def fn(_):
        return st.session_state[k(name, prefix)]

    return fn


def mk_setter(name, prefix):
    def fn(_, value):
        st.session_state[k(name, prefix)] = value

    return fn


def with_prop(name, default, prefix):
    if not k(name, prefix) in st.session_state:
        st.session_state[k(name, prefix)] = default

    def inner(cls):
        prop = property(mk_getter(name, prefix))
        prop = prop.setter(mk_setter(name, prefix))
        setattr(cls, name, prop)
        # prop.__set__ = mk_setter(name, prefix)
        return cls

    return inner


def keygetter(prefix, method_name="_keyof"):
    def f(self, key):
        nonlocal prefix
        return k(key, prefix)

    def inner(cls):
        setattr(cls, method_name, f)
        return cls

    return inner
