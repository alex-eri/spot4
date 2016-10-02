def check(num):
    assert num.startswith("+79")
    assert len(num) > 8
    assert len(num) < 13
    return True
