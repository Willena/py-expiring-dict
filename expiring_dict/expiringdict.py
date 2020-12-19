try:
    from collections.abc import MutableMapping
except ImportError:  # Will allow usage with virtually any python 3 version
    from collections import MutableMapping

from threading import Timer, Thread, Lock
from sortedcontainers import SortedKeyList
from time import time, sleep


class ExpiringDict(MutableMapping):
    def __init__(self, ttl=None, interval=0.100, *args, **kwargs):
        """
        Create an ExpiringDict class, optionally passing in a time-to-live
        number in seconds that will act globally as an expiration time for keys.

        If omitted, the dict will work like a normal dict by default, expiring
        only keys explicity set via the `.ttl` method.
        """
        self.__store = dict(*args, **kwargs)
        self.__keys = SortedKeyList(key=lambda x: x[0])
        self.__reverse_keys = dict()
        self.__ttl = ttl
        self.__lock = Lock()
        self.__interval = interval
        self.__key_delete_callback = None
        self.__delete_callback = None

        t = Thread(target=self.__worker)
        t.setDaemon(True)
        t.start()

    def flush(self):
        now = time()
        max_index = 0
        with self.__lock:
            for index, (timestamp, key) in enumerate(self.__keys):
                if timestamp > now:  # rest of the timestamps in future
                    max_index = index
                    break
                try:
                    del self.__store[key]
                    del self.__reverse_keys[key]
                    if self.__key_delete_callback is not None:
                        self.__key_delete_callback(key)
                except KeyError:
                    pass  # don't care if it was deleted early

            if max_index > 0 and self.__delete_callback is not None:
                self.__delete_callback(max_index)

            del self.__keys[0:max_index]

    def __worker(self):
        while True:
            self.flush()
            sleep(self.__interval)

    def __setitem__(self, key, value):
        """
        Set `value` of `key` in dict. `key` will be automatically
        deleted if the `ttl` option was provided for this object.
        """
        # if self.__ttl:
        #     self.__set_with_expire(key, value, self.__ttl)
        # else:
        #     self.__store[key] = value

        self.ttl(key, value, self.__ttl)

    def ttl(self, key, value=None, ttl=-1):
        """
        Set `value` of `key` in dict to expire after `ttl` seconds.
        Overrides object level `ttl` setting.
        0 => expire now, already expired
        None => infinite
        >0 => specified life
        """
        self.__set_with_expire(key, value, self.__ttl if ttl == -1 else ttl)

    def reset_ttl(self, key, ttl=-1):
        self.__set_with_expire(key, None, self.__ttl if ttl == -1 else ttl, use_value=False)

    def expire(self, key):
        self.reset_ttl(key, 0)

    def __set_with_expire(self, key, value, ttl, use_value=True):
        with self.__lock:
            if use_value:
                self.__store[key] = value
            self.__reset_ttl(key, ttl, no_value=not use_value)

    def __reset_ttl(self, key, ttl=None, no_value=False):

        self.__discard_keys(key)

        if key in self.__store and ttl is not None:
            expiration = (time() + ttl, key)
            self.__keys.add(expiration)
            self.__reverse_keys[key] = expiration

    def __discard_keys(self, key):
        if key in self.__reverse_keys:
            # Reset key expiration storage :)
            self.__keys.discard(self.__reverse_keys[key])
            del self.__reverse_keys[key]

    def set_key_delete_callback(self, callback):
        self.__key_delete_callback = callback

    def set_delete_callback(self, callback):
        self.__delete_callback = callback

    def __delitem__(self, key):
        with self.__lock:
            self.__discard_keys(key)
            del self.__store[key]

    def __getitem__(self, key):
        return self.__store[key]

    def __iter__(self):
        return iter(self.__store)

    def __len__(self):
        return len(self.__store)


"""
Auto tests
"""
if __name__ == '__main__':
    def cb(x):
        print("Key {} has been delete ".format(x))

    def tcb(x):
        print("Deleted {} elements".format(x))


    demo = ExpiringDict(ttl=3, interval=0.1)
    demo.set_key_delete_callback(cb)
    demo.set_delete_callback(tcb)
    demo['toto'] = "abc"  # TTL = 3
    demo.reset_ttl("tata")  # Should not update TTL because does not exist
    demo.ttl("tutu", "val", 500)  # TTL = 500
    demo.reset_ttl('tutu', 1000)  # TTL 1000
    sleep(1)
    print ("Init ok ")
    demo.reset_ttl('tutu', 0)  # TTL = 0, delete next GC
    demo.expire("toto")
    demo.ttl("noExp", "val", None)
    sleep(3)
    print ("Len " + str(len(demo)))
    demo.reset_ttl('noExp', 100)
    sleep(3)
    print("Add again ")
    demo.ttl("noExp", "val", None)
    sleep(10)
    del demo['noExp']
