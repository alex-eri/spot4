def check(num):
    assert num.startswith("+")
    if num.startswith("+7"):
        assert num.startswith("+79")
        assert len(num) == 12
    assert len(num) > 8
    assert len(num) < 14
    return True
