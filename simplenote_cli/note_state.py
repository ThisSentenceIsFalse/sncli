# Copyright (c) 2020 Mihai Popescu
# new BSD license

class NoteState:
    def __init__(self):
        pass

    def dump(self):
        pass

    def diff(self):
        pass

    def accept_remote(self, *, data=None, remotekey, version):
        pass

    @classmethod
    def new(cls, *, localkey, content={}):
        pass

    @classmethod
    def load(cls, *, content={}):
        pass
