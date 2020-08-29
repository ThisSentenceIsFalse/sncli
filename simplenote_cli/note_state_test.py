# Copyright (c) 2020 Mihai Popescu
# new BSD license

import unittest, time
from .note_state import NoteState

class NoteStateTests(unittest.TestCase):

    # A note state must be initializable with just a 'localkey'
    def test_new_default_interface():
        state = NoteState.new('test')

        self.assertEqual(state.meta.localkey, 'test')
        self.assertIs(state.meta.remotekey, None)
        self.assertIs(state.meta.version, None)
        self.assertIs(state.meta.saved, False)
        self.assertIs(state.meta.synced, False)

    def test_new_default_data_iface():
        state = NoteState.new('test')
        now = time.time()
        
        self.assertEqual(state.xchg.content, '')
        self.assertIs(state.xchg.deleted, False)
        self.assertEqual(state.xchg.tags, [])
        self.assertEqual(state.xchg.systemTags, [])
        self.assertEqual(state.xchg.shareURL, '')
        self.assertEqual(state.xchg.publishURL, '')
        # TODO: any better way to test proximity to current time?
        self.assertIsInstance(state.xchg.modificationDate, float)
        self.assertTrue(0 <= state.xchg.modificationDate <= now)
        self.assertIsInstance(state.xchg.creationDate, float)
        self.assertTrue(0 <= state.xchg.creationDate <= now)
        self.assertLessEqual(state.xchg.creationDate, 
                             state.xchg.modificationDate)

    def test_new_xchg_data():
        state = NoteState.new('test')
        xchg_data = state.xchg_data()
        tested_xchg_keys = [
            'content', 'deleted', 'tags', 'systemTags',
            'shareURL', 'publishURL', 'modificationDate', 'creationDate'
        ]

        for key in tested_xchg_keys:
            xchg_value = xchg_data[key]
            corresponding_attr = getattr(state.xchg, key)
            self.assertEqual(xchg_value, corresponding_attr)

    # The constructor for new note states must ignore foreign fields
    # TODO: is 'version' foreign per this description? The current code
    # doesn't use it when importing, and there's a currently unevaluated
    # risk using any assumedly local version field, so I shy away from it
    def test_new_unknown_fields():
        state = NoteState.new('test', {
            'content': 'foo',
            'tags': ['bla'],
            'systemTags': [],
            # below fields not set in the content
            # NOTE: 'version' is __not__ used to update the meta, see asserts
            'abcd': 42
        })
        xchg_data = state.xchg_data()
        
        self.assertNotIn('abcd', xchg_data)
    
    # Unsynced (yet) states must be able to accept newer authoritative
    # version numbers and an authoritative remote key if the server
    # confirms our version.
    def test_new_accept_remote():
        state = NoteState.new('test')
        state.xchg.content = 'foo'
        state.xchg.tags += ['bla']
        # ...
        # server.update_note(state.xchg_data())
        # ...
        # accepting without data means that our version is authoritative now
        state.accept_remote(remotekey='bla', version=42)
        diffs = state.diff()
        
        self.assertEqual(state.meta.remotekey, 'bla')
        self.assertEqual(state.meta.localkey, 'bla')
        self.assertEqual(state.meta.version, 42)
        self.assertIs(state.meta.synced, True)
        self.assertEqual(diffs['new'], [])

    def test_new_accept_remote_foreign_fields():
        remote_data = {
            'content': 'foo',
            'deleted': False,
            'tags': ['bla'],
            'systemTags': [],
            'shareURL': '',
            'publishURL': '',
            'creationDate': init_state.xchg.creationDate,
            'modificationDate': time.time(),
            # field below will appear in the dict by xchg_data()
            'abcd': 42
        }
        state = NoteState.new('test')
        state.accept_remote(remotekey='bla', version=42)
        # ...
        # update from server
        state.accept_remote(remote_data, version=43)

        self.assertDictContainsSubset(remote_data, xchg_data)

    def test_new_accept_remote_conflicting():
        remote_data = {
            'content': 'baz',
            'deleted': False,
            'tags': ['waz'],
            'systemTags': [],
            'shareURL': '',
            'publishURL': '',
            'creationDate': init_state.xchg.creationDate,
            'modificationDate': time.time()
        }
        state = NoteState.new('test')
        state.xchg.content = 'foo'
        state.xchg.tags += ['bla']

        # content and tags should conflict here
        self.assertRaises(ValueError, state.accept_remote, state,
                          remote_data, remotekey='boo', version=42)

    # States must refuse older versions of the document
    def test_new_accept_remote_old_version():
        state = NoteState.new('test')
        state.accept_remote(remotekey='bla', version=42)

        self.assertRaises(ValueError, state.accept_remote, state, version=41)

    def test_new_accept_remote_second_key():
        remote_data = {
            'content': 'foo',
            'deleted': False,
            'tags': ['bla'],
            'systemTags': [],
            'shareURL': '',
            'publishURL': '',
            'creationDate': init_state.xchg.creationDate,
            'modificationDate': time.time()
        }
        state = NoteState.new('test')
        state.accept_remote(remotekey='bla', version=42)

        self.assertRaises(ValueError, state.accept_remote, 
                          state, remotekey='baz', version=43)

    def test_new_diff():
        state = NoteState.new('test')
        old_data = state.xchg_data()
        state.xchg.content = 'foo'
        state.xchg.tags += ['bla']
        diff = state.diff()

        assertIs(state.meta.synced, False)
        assertEqual(diff['old'], old_data)
        assertEqual(diff['new']['content'], 'foo')
        assertEqual(diff['new']['tags'], ['bla'])

    # It must be possible to load a dump into a new state instance
    def test_load_dump():
        n1 = NoteState.new('test', {'content': 'foo', 'tags': ['bla']});
        s1 = n1.dump();
        n2 = NoteState.load(s1);
        s2 = n2.dump();

        assertEqual(n1, n2);

    # improper content must be rejected
    def test_bad_content_type():
        self.assertRaises(ValueError, NoteState.new,
                          'test', {'content': 42})

        xchg = NoteState.new('test').xchg
        self.assertRaises(ValueError, setattr, xchg, 'content', 42)

    def test_bad_deleted_type():
        self.assertRaises(ValueError, NoteState.new,
                          'test', {'deleted': ''})

        xchg = NoteState.new('test').xchg
        self.assertRaises(ValueError, setattr, xchg, 'deleted', '')

    def test_bad_tags_type():
        self.assertRaises(ValueError, NoteState.new,
                          'test', {'tags': ''})

        xchg = NoteState.new('test').xchg
        self.assertRaises(ValueError, setattr, xchg, 'tags', '')

    def test_bad_tags_elem_type():
        self.assertRaises(ValueError, NoteState.new, 
                          'test', {'tags': ['abc', 42]})

        xchg = NoteState.new('test').xchg
        self.assertRaises(ValueError, setattr, xchg, 'tags', ['abc', 42])

    # TODO: systemTags testing
    def test_bad_systags_type():
        self.assertRaises(ValueError, NoteState.new, 
                          'test', {'systemTags': ''})

        xchg = NoteState.new('test').xchg
        self.assertRaises(ValueError, setattr, xchg, 'systemTags', '')

    def test_bad_creation_date_type():
        self.assertRaises(ValueError, NoteState.new, {'creationDate': ''});

    def test_bad_modification_date_type():
        self.assertRaises(ValueError, NoteState, {'modificationDate': ''});

    def test_modification_before_creation():
        mod_date = time.time(),
        creat_date = time.time();

        while (creat_date <= mod_date):
            creat_date = time.time();

        dates = {
            'creationDate': creat_date,
            'modificationDate': mod_date
        }

        self.assertRaises(ValueError, NoteState.new, 'foo', dates);

if __name__ == '__main__':
    unittest.main()
