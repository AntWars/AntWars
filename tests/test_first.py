import pytest


class TestClass(object):
    def test_one(self):
        x = "this"
        assert 'h' in x

    @pytest.mark.xfail
    def test_two(self):
        x = "hello"
        assert hasattr(x, 'check')