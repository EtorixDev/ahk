import asyncio
import random
import string
import time
import unittest
from typing import Literal

import pytest

from ahk import AHK
from ahk.extensions import Extension


sleep = time.sleep

function_name = 'AHKDoSomething'

ext_text = f'''\
{function_name}(first, second) {{
    return FormatResponse("ahk.message.StringResponseMessage", Format("{{}} and {{}}", first, second))
}}
'''

math_function_name = 'SimpleMath'

math_test = rf'''
{math_function_name}(lhs, rhs, operator) {{
    if (operator = "+") {{
        result := (lhs + rhs)
    }} else if (operator = "*") {{
        result := (lhs * rhs)
    }} else {{ ; invalid operator argument
        return FormatResponse("ahk.message.ExceptionResponseMessage", Format("Invalid operator: {{}}", operator))
    }}
    return FormatResponse("ahk.message.IntegerResponseMessage", result)
}}
'''

async_extension = Extension(script_text=ext_text)
async_math_extension = Extension(script_text=math_test)


@async_math_extension.register
def simple_math(ahk: AHK, lhs: int, rhs: int, operator: Literal['+', '*']) -> int:
    assert isinstance(lhs, int)
    assert isinstance(rhs, int)
    args = [str(lhs), str(rhs), operator]  # all args must be strings
    result = ahk.function_call(math_function_name, args, blocking=True)
    return result


@async_extension.register
def do_something(ahk, first: str, second: str) -> str:
    res = ahk.function_call(function_name, [first, second])
    return res


class TestExtensions(unittest.TestCase):
    def setUp(self) -> None:
        self.ahk = AHK(extensions=[async_extension])

    def tearDown(self) -> None:
        self.ahk._transport._proc.kill()
        time.sleep(0.2)

    def test_ext_explicit(self):
        res = self.ahk.do_something('foo', 'bar')
        assert res == 'foo and bar'


class TestExtensionsAuto(unittest.TestCase):
    def setUp(self) -> None:
        self.ahk = AHK(extensions='auto')

    def tearDown(self) -> None:
        self.ahk._transport._proc.kill()
        time.sleep(0.2)

    def test_ext_auto(self):
        res = self.ahk.do_something('foo', 'bar')
        assert res == 'foo and bar'

    def test_math_example(self):
        res = self.ahk.simple_math(1, 2, '+')
        assert res == 3

    def test_math_example_exception(self):
        with pytest.raises(Exception):
            res = self.ahk.simple_math(1, 2, 'x')


class TestNoExtensions(unittest.TestCase):
    def setUp(self) -> None:
        self.ahk = AHK()
        self.ahk.get_mouse_position()  # cause daemon to start

    def tearDown(self) -> None:
        self.ahk._transport._proc.kill()
        time.sleep(0.2)

    def test_ext_no_ext(self):
        assert not hasattr(self.ahk, 'do_something')


class TestExtensionsV2(TestExtensions):
    def setUp(self) -> None:
        self.ahk = AHK(extensions=[async_extension], version='v2')


class TestExtensionsAutoV2(TestExtensionsAuto):
    def setUp(self) -> None:
        self.ahk = AHK(extensions='auto', version='v2')


class TestNoExtensionsV2(TestNoExtensions):
    def setUp(self) -> None:
        self.ahk = AHK(version='v2')
        self.ahk.get_mouse_position()  # cause daemon to start
