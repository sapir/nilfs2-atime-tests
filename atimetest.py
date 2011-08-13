#!/usr/bin/python

import unittest
import os
import time
from subprocess import check_call

def mk_sparse_file(path, size):
    assert size > 0
    print 'Mking sparse file'
    with open(path, 'wb') as f:
        f.seek(size - 1)
        f.write('\0')

def mk_nilfs_img(image_path):
    mk_sparse_file(image_path, 150 * 1048576)
    print 'Initing fs image'
    check_call(['mkfs.nilfs2', image_path])

def mount_nilfs(dev, path, opts=()):
    args = ['mount', '-t', 'nilfs2', dev, path]
    args += ['-o', ','.join(opts)]
    print 'Mounting'
    check_call(args)

def umount(path):
    print 'Unmounting'
    check_call(['umount', path])


class TestNilfs(unittest.TestCase):
    IMG_PATH = 'fs.dat'
    MOUNT_PATH = 'mynilfs'
    MOUNT_OPTS = ['loop']
    TEST_FILE_NAME = 'abc.txt'
    
    def _mount(self):
        mount_nilfs(self.IMG_PATH, self.MOUNT_PATH, self.MOUNT_OPTS)
    
    def _umount(self):
        umount(self.MOUNT_PATH)
    
    def setUp(self):
        if not os.path.isdir(self.MOUNT_PATH):
            os.mkdir(self.MOUNT_PATH)
        
        mk_nilfs_img(self.IMG_PATH)
        
        self._mount()        
    
    def tearDown(self):
        self._umount()
    
    
    @property
    def _test_file_path(self):
        return os.path.join(self.MOUNT_PATH, self.TEST_FILE_NAME)
    
    def _write_test_file(self):
        with open(self._test_file_path, 'wt') as f:
            print >>f, 'hi there'
    
    def _read_test_file(self):
        with open(self._test_file_path, 'rt') as f:
            return f.read()
    
    def _stat_test_file(self):
        st = os.stat(self._test_file_path)
        return st.st_mtime, st.st_atime
    
    def _wait_a_bit(self):
        time.sleep(2)
    
    def test_simple(self):
        self._write_test_file()
        m, a = self._stat_test_file()
        self.assertEqual(m, a)
    
    def test_read_updates_atime(self):
        self._write_test_file()
        m0, a0 = self._stat_test_file()
        self.assertEqual(m0, a0)
        for i in range(3):
            self._wait_a_bit()
            self._read_test_file()
            m, a = self._stat_test_file()
            self.assertEqual(m, m0)
            self.assertGreater(a, a0)
    
    def test_atime_survives_umount(self):
        self._write_test_file()
        self._wait_a_bit()
        self._read_test_file()
        m0, a0 = self._stat_test_file()
        self._wait_a_bit()
        self._umount()
        self._wait_a_bit()
        self._mount()
        m1, a1 = self._stat_test_file()
        self.assertEqual(m0, m1)
        self.assertEqual(a0, a1)
        self.assertGreater(a0, m0)

if __name__ == '__main__':
    unittest.main()
