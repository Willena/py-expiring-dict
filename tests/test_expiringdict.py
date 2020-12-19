import copy
import random
import string
import queue
from threading import Thread

from expiring_dict import ExpiringDict
from time import sleep, time


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

def test_perf():
    def key(message):
        return tuple([message[k] for k in keys if k in message])

    def th(data):
        print(data)
        while True:
            try:
                e = Q.get(timeout=0.01)
                k = key(e)
                # print(" key {key}".format(key=k))
                exDir = data['mnemo']

                if k in exDir:
                    if e in exDir[k]['messages']:
                        # print("  Already have the message")
                        continue

                    exDir[k]['messages'].append(copy.deepcopy(e))
                    exDir[k]['d'] += 1
                    # print("  Add one nano sec")

                else:
                    exDir[k] = {'messages': [copy.deepcopy(e)], 'd': 0}
                    # print("  New message")

            except queue.Empty:
                pass

    def get_random_string(length):
        letters = string.ascii_lowercase
        result_str = ''.join(random.choice(letters) for i in range(length))
        return result_str

    def generator():
        return {
            "a": get_random_string(3),
            "b": "Static",
            "c": "Static",
            "d": random.randint(0, 1000),
            "u": "str" + str(random.randint(0, 10000))
        }

    def producer():
        t = time()
        while time() - t < 60 * 5:
            obj = generator()
            Q.put_nowait(obj)
            # print("Added obj ".format(obj))

    if __name__ == '__main__':
        global keys
        keys = ["a", "b", "c", "d"]

        global Q
        Q = queue.Queue(maxsize=-1)

        data = {'mnemo': ExpiringDict(ttl=180, interval=5)}
        data['mnemo'].set_delete_callback(lambda x: print(
            "Deleting {} items. Current len {}s".format(x, len(data['mnemo']))))

        thList = []

        for i in range(0, 5):
            tha = Thread(target=th, args=(data,))
            tha.setName("Thread" + str(i))
            tha.setDaemon(True)
            tha.start()

        t = None
        for i in range(0, 1):
            t = Thread(target=producer, name="Producer" + str(i))
            t.start()

        t.join()
        sleep(60 * 5)

if __name__ == '__main__':
    # Run All tests
    # test_reset_ttl()
    # test_expire()
    # test_key_delete_callback()
    # test_delete_callback()
    # test_init()
    # test_class_ttl()
    # test_dict_ops()
    # test_no_ttl()
    # test_set_ttl()
    test_perf()
