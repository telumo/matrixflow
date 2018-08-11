import sys
from nose.tools import with_setup, raises, eq_, ok_
from pathlib import Path

sys.path.insert(0, '../..')
from utils import convert, camel2snake, snake2camel


def test_snake2camel_1():
    obj = {
        "aa_aa":0,
        "vv_aa_aaa": "aaaa",
        "vv_aa": [1,2,3,5],
        "dc_dc": {"ggg_ggg": 0, "sss_ddd": "a_aa"},
        "ff_ffff": [
            {
                "ddd_dddd": "aaa_aa"
            },
            {
                "ggg_ggg": 3,
                "ggg_fgg": 2
            },
            {
                "list_list": [
                    {"ddd_ddd":"gggg"}
                ]
            }
        ]
    }
    res = convert(obj, snake2camel)
    expected = {
        "aaAa":0,
        "vvAaAaa": "aaaa",
        "vvAa": [1,2,3,5],
        "dcDc": {"gggGgg": 0, "sssDdd": "a_aa"},
        "ffFfff": [
            {
                "dddDddd": "aaa_aa"
            },
            {
                "gggGgg": 3,
                "gggFgg": 2
            },
            {
                "listList": [
                    {"dddDdd":"gggg"}
                ]
            }
        ]
    }
    eq_(res, expected)

def test_snake2camel_2():
    obj = {"a_a":{"b_b":4}}
    res = convert(obj, snake2camel)
    expected = {"aA":{"bB":4}}
    eq_(res, expected)


def test_camel2snake_1():
    expected = {
        "aa_aa":0,
        "vv_aa_aaa": "aaaa",
        "vv_aa": [1,2,3,5],
        "dc_dc": {"ggg_ggg": 0, "sss_ddd": "a_aa"},
        "ff_ffff": [
            {
                "ddd_dddd": "aaa_aa"
            },
            {
                "ggg_ggg": 3,
                "ggg_fgg": 2
            },
            {
                "list_list": [
                    {"ddd_ddd":"gggg"}
                ]
            }
        ]
    }
    obj = {
        "aaAa":0,
        "vvAaAaa": "aaaa",
        "vvAa": [1,2,3,5],
        "dcDc": {"gggGgg": 0, "sssDdd": "a_aa"},
        "ffFfff": [
            {
                "dddDddd": "aaa_aa"
            },
            {
                "gggGgg": 3,
                "gggFgg": 2
            },
            {
                "listList": [
                    {"dddDdd":"gggg"}
                ]
            }
        ]
    }
    res = convert(obj, camel2snake)
    eq_(res, expected)
