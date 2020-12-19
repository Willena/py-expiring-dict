from expiring_dict import ExpiringDict
from time import sleep


def test_init():
    ExpiringDict()


def test_no_ttl():
    d = ExpiringDict()
    d["key"] = "value"
    assert len(d._ExpiringDict__keys) == 0


def test_class_ttl():
    d = ExpiringDict(ttl=0.01, interval=0.005)
    d["key"] = "should be gone"
    assert len(d) == 1
    sleep(0.02)
    assert len(d) == 0


def test_set_ttl():
    d = ExpiringDict(interval=0.005)
    d.ttl("key", "expire", 0.01)
    assert len(d) == 1
    sleep(0.02)
    assert len(d) == 0


def test_dict_ops():
    ed = ExpiringDict()
    ed["one"] = 1
    ed["two"] = 2
    ed["three"] = 3
    d = dict()
    d["one"] = 1
    d["two"] = 2
    d["three"] = 3
    assert [x for x in d] == [x for x in ed]
    assert [k for k in d.keys()] == [k for k in ed.keys()]
    assert [v for v in d.values()] == [v for v in ed.values()]
    assert [i for i in d.items()] == [i for i in ed.items()]
    assert "one" in ed


def test_delete_callback():
    has_callback = False

    def delete_callback(x):
        print("Callback: {} deleted keys".format(x))
        has_callback = True

    ed = ExpiringDict(ttl=1, interval=0.1)
    ed.set_delete_callback(delete_callback)

    sleep(2)
    # assert has_callback is True


def test_key_delete_callback():

    has_callback = False

    def key_delete_callback(x):
        print("Callback: Delete {}".format(x))
        has_callback = True

    ed = ExpiringDict(ttl=1, interval=0.1)
    ed.set_delete_callback(key_delete_callback)

    sleep(2)
    # assert has_callback is True


def test_reset_ttl():
    ed = ExpiringDict(ttl=2, interval=0.1)
    ed["toto"] = "tata"  # Should expire in 2s
    ed.reset_ttl("toto", 5)
    sleep(3)
    assert len(ed) == 1
    sleep(3)
    assert len(ed) == 0
    ed['tutu'] = "zzz"
    ed.reset_ttl('tutu', None)
    sleep(5)
    assert len(ed) == 1


def test_expire():
    ed = ExpiringDict(ttl=5, interval=0.1)
    ed["toto"] = "tata"  # Should expire in 5s
    ed.reset_ttl("toto", 0) # Expire NOW !
    sleep(1)
    assert len(ed) == 0
    ed["tutu"] = "tata"  # Should expire in 5s
    ed.expire("tutu") # Expire NOW !
    sleep(1)
    assert len(ed) == 0


if __name__ == '__main__':
    # Run All tests
    test_reset_ttl()
    test_expire()
    test_key_delete_callback()
    test_delete_callback()
    test_init()
    test_class_ttl()
    test_dict_ops()
    test_no_ttl()
    test_set_ttl()
