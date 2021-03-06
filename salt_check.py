#!/usr/bin/env python
# -*- coding: UTF-8 -*-
'''This custom salt module makes it easy to test salt states and highstates.
   Author: William Cannon  william period cannon at gmail dot com

   Here's how it works:
   Create a state as a directory (e.g.  /srv/salt/apache/init.sls)
   Create a sub-directory of the state directory and name it 'salt-check-tests' (e.g. /srv/salt/apache/salt-check-tests)
   Put one or more test files in the 'salt-check-tests' directory, each with a file name ending with .tst .
   Note:  a test file contains 1 or more tests defined in yaml

   Three ways to run tests:
   ------------------------
   Method 1:  Test with CLI parameter
   salt '*' salt_check.run_test  
     test='{"module_and_function": "test.echo",
            "args":["This works!”],
            "assertion": "assertEqual",
            "expected-return": "This works!"}'

   Method 2: Test state logic dynamically
   salt '*' salt_check.run_state_tests apache

   Method 3: Test highstate logic dynamically
   salt '*' salt_check.run_highstate_tests

   YAML Syntax for one test (replace text in caps):
   ------------------------------------------------
   UNIQUE-TEST-NAME:
     module_and_function:SALT_EXECUTION_MODULE.FUNCTION_NAME
     args:
       - A
       - LIST OF
       - ARGUMENTS FOR
       - THE FUNCTION
     kwargs:
       - A
       - LIST OF
       - KEYWORD ARGUMENTS FOR
       - THE FUNCTION
     assertion: [assertEqual | assertNotEqual | assertTrue | assertFalse |
                assertIn     | assertGreater  | assertGreaterEqual |
                assertLess   | assertLessEqual ]
     expected-return: RETURN_FROM_CALLING_SALT_EXECUTION_MODULE.FUNCTION_NAME

   Quick example of a salt_check test:
   ----------------------------------- 
   test-1-tmp-file:
    module_and_function: file.file_exists
    args:
      - /tmp/hello
    kwargs:
    assertion: assertEqual
    expected-return: True'''

import os
import os.path
import yaml
import salt.client
import salt.minion
import salt.config
import salt.loader
import salt.exceptions
import logging
import time

log = logging.getLogger(__name__)

class SaltCheck(object):
    '''
    This class implements the salt_check
    '''

    def __init__(self, opts=None):
        if opts:
            self.opts = opts
        else:
            self.opts = __opts__
        self.salt_lc = salt.client.Caller(mopts=self.opts)
        self.results_dict = {}
        self.results_dict_summary = {}
        self.assertions_list = '''assertEqual assertNotEqual
                                  assertTrue assertFalse
                                  assertIn assertGreater
                                  assertGreaterEqual
                                  assertLess assertLessEqual'''.split()
        self.modules = self.populate_salt_modules_list()

    def cache_master_files(self):
        ''' equivalent to a salt cli: salt web cp.cache_master
        note: should do this for each env in file_root'''
        # This does not get rid of previous files from a prior cache
        # should change this to be a 'real-time' representation of
        # master cache
        log.info("cache_master_files start time: {}".format(time.time()))
        try:
            returned = self.call_salt_command(fun='cp.cache_master',
                                              args=None,
                                              kwargs=None)
            pillar_refresh = self.call_salt_command(fun='pillar.items',
                                              args=None,
                                              kwargs=None)
        except Exception:
            raise
        log.info("cache_master_files finish time: {}".format(time.time()))
        return returned

    def get_top_states(self):
        ''' equivalent to a salt cli: salt web state.show_top'''
        try:
            returned = self.call_salt_command(fun='state.show_top',
                                              args=None,
                                              kwargs=None)
            # doing this to handle states with periods
            # e.g.  apache.vhost_web1
            alt_states = []
            for state in returned['base']:
                state_bits = state.split(".")
                state_name = state_bits[0]
                if state_name not in alt_states:
                    alt_states.append(state_name)
        except Exception:
            raise
        log.info("top states: {}".format(alt_states))
        #return returned['base']
        return alt_states

    def populate_salt_modules_list(self):
        '''return a list of all modules available on minion'''
        valid_modules = self.call_salt_command(fun='sys.list_modules',
                                               args=None,
                                               kwargs=None)
        return valid_modules

    def is_valid_module(self, module_name):
        '''Determines if a module is valid on a minion'''
        if module_name not in self.modules:
            val = False
        else:
            val = True
        return val

    def is_valid_function(self, module_name, function):
        '''Determine if a function is valid for a module'''
        try:
            functions = self.call_salt_command(fun='sys.list_functions',
                                               args=[module_name],
                                               kwargs=None)
        except salt.exceptions.SaltException:
            functions = ["unable to look up functions"]
        return "{0}.{1}".format(module_name, function) in functions

    def is_valid_test(self, test_dict):
        '''Determine if a test contains:
             a test name,
             a valid module and function,
             a valid assertion,
             an expected return value'''
        tots = 0  # need 6 to pass test
        m_and_f = test_dict.get('module_and_function', None)
        assertion = test_dict.get('assertion', None)
        expected_return = test_dict.get('expected-return', None)
        if m_and_f:
            tots += 1
            module, function = m_and_f.split('.')
            if self.is_valid_module(module):
                tots += 1
            if self.is_valid_function(module, function):
                tots += 1
        if assertion:
            tots += 1
            if assertion in self.assertions_list:
                tots += 1
        if expected_return:
            tots += 1
        return tots >= 6
        # return True

    def call_salt_command(self,
                          fun,
                          args=None,
                          kwargs=None):
        '''Generic call of salt Caller command'''
        value = False
        try:
            if args and kwargs:
                value = self.salt_lc.function(fun, *args, **kwargs)
            elif args and not kwargs:
                value = self.salt_lc.function(fun, *args)
            elif not args and kwargs:
                value = self.salt_lc.function(fun, **kwargs)
            else:
                value = self.salt_lc.function(fun)

        except salt.exceptions.SaltException as err:
            value = err
        except Exception as err:
            value = err
        return value

    def call_salt_command_test(self,
                               fun
                               ):
        '''Generic call of salt Caller command'''
        value = False
        try:
            value = self.salt_lc.function(fun)
        except salt.exceptions.SaltException as err:
            value = err
        return value

    def run_test(self, test_dict):
        '''Run a single salt_check test'''
        if self.is_valid_test(test_dict):
            mod_and_func = test_dict['module_and_function']
            args = test_dict.get('args', None)
            assertion = test_dict['assertion']
            expected_return = test_dict['expected-return']
            kwargs = test_dict.get('kwargs', None)
            actual_return = self.call_salt_command(mod_and_func, args, kwargs)
            #log.info("expected before alteration= {}".format(expected_return))
            #log.info("type of expected before= {}".format(type(expected_return)))
            expected_return = self.cast_expected_to_returned_type(expected_return, actual_return)
            #log.info("expected after alteration= {}".format(expected_return))
            #log.info("type of expected = {}".format(type(expected_return)))
            # return actual_return
            if assertion == "assertEqual":
                value = self.assert_equal(expected_return, actual_return)
            elif assertion == "assertNotEqual":
                value = self.assert_not_equal(expected_return, actual_return)
            elif assertion == "assertTrue":
                value = self.assert_true(expected_return)
            elif assertion == "assertFalse":
                value = self.assert_false(expected_return)
            elif assertion == "assertIn":
                value = self.assert_in(expected_return, actual_return)
            elif assertion == "assertNotIn":
                value = self.assert_not_in(expected_return, actual_return)
            elif assertion == "assertGreater":
                value = self.assert_greater(expected_return, actual_return)
            elif assertion == "assertGreaterEqual":
                value = self.assert_greater_equal(expected_return, actual_return)
            elif assertion == "assertLess":
                value = self.assert_less(expected_return, actual_return)
            elif assertion == "assertLessEqual":
                value = self.assert_less_equal(expected_return, actual_return)
            else:
                value = False
        else:
            value = "False: Invalid test"
        return value

    @staticmethod
    def cast_expected_to_returned_type(expected, returned):
        '''
        Determine the type of variable returned
        Cast the expected to the type of variable returned
        '''
        ret_type = type(returned)
        new_expected = expected
        if expected == "False" and ret_type == bool:
            expected = False
        try:
            new_expected = ret_type(expected)
        except:
            log.info("Unable to cast expected into type of returned")
            log.info("returned = {}".format(returned))
            log.info("type of returned = {}".format(type(returned)))
            log.info("expected = {}".format(expected))
            log.info("type of expected = {}".format(type(expected)))
        return new_expected

    @staticmethod
    def assert_equal(expected, returned):
        '''
        Test if two objects are equal
        '''
        result = True
        #log.info("returned = {}".format(returned))
        #log.info("type of returned = {}".format(type(returned)))
        #log.info("expected = {}".format(expected))
        #log.info("type of expected = {}".format(type(expected)))

        #if type(returned) == bool:
        #    returned = str(returned)


        try:
            assert (expected == returned), "{0} is not equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_not_equal(expected, returned):
        '''
        Test if two objects are not equal
        '''
        result = (True)
        try:
            assert (expected != returned), "{0} is equal to {1}".format(expected, returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_true(returned):
        '''
        Test if an boolean is True
        '''
        result = (True)
        try:
            assert (returned is True), "{0} not True".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_false(returned):
        '''
        Test if an boolean is False
        '''
        result = (True)
        if type(returned) == str:
            returned = eval(returned)
        try:
            assert (returned is False), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True)
        try:
            assert (expected in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_not_in(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True)
        try:
            assert (expected not in returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_greater(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True)
        try:
            assert (expected > returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_greater_equal(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True)
        try:
            assert (expected >= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_less(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True)
        try:
            assert (expected < returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    @staticmethod
    def assert_less_equal(expected, returned):
        '''
        Test if a value is in the list of returned values
        '''
        result = (True)
        try:
            assert (expected <= returned), "{0} not False".format(returned)
        except AssertionError as err:
            result = "False: " + str(err)
        return result

    def show_minion_options(self):
        '''gather and return minion config options'''
        cachedir = self.opts['cachedir']
        root_dir = self.opts['root_dir']
        states_dirs = self.opts['states_dirs']
        environment = self.opts['environment']
        file_roots = self.opts['file_roots']
        return {'cachedir': cachedir,
                'root_dir': root_dir,
                'states_dirs': states_dirs,
                'environment': environment,
                'file_roots': file_roots}

    def get_state_search_path_list(self):
        '''For the state file system, return a
           list of paths to search for states'''
        # state cache should be updated before running this method
        log.info("get_state_search_path_list time: {}".format(time.time()))
        search_list = []
        cachedir = self.opts.get('cachedir', None)
        environment = self.opts['environment']
        if environment:
            path = cachedir + os.sep + "files" + os.sep + environment
            search_list.append(path)
        path = cachedir + os.sep + "files" + os.sep + "base"
        search_list.append(path)
        return search_list

    def get_state_dir(self):
        ''''return the path of the state dir'''
        paths = self.get_state_search_path_list()
        return paths


class StateTestLoader(object):
    '''
    Class loads in test files for a state
    e.g.  state_dir/salt-check-tests/[1.tst, 2.tst, 3.tst]
    '''

    def __init__(self, search_paths):
        self.search_paths = search_paths
        self.path_type = None
        self.test_files = []  # list of file paths
        self.test_dict = {}

    def load_test_suite(self):
        '''load tests either from one file, or a set of files'''
        for myfile in self.test_files:
            self.load_file(myfile)

    def load_file(self, filepath):
        '''
        loads in one test file
        '''
        try:
            myfile = open(filepath, 'r')
            contents_yaml = yaml.load(myfile)
            for key, value in contents_yaml.items():
                self.test_dict[key] = value
        except:
            raise
        return

    def gather_files(self, filepath):
        '''gather files for a test suite'''
        log.info("gather_files: {}".format(time.time()))
        filepath = filepath + os.sep + 'salt-check-tests'
        rootDir = filepath
        for dirName, subdirList, fileList in os.walk(rootDir):
            for fname in fileList:
                if fname.endswith('.tst'):
                    start_path = dirName + os.sep + fname
                    full_path = os.path.abspath(start_path)
                    self.test_files.append(full_path)
        return

    def find_state_dir(self, state_name):
        '''find and return the path to the state dir'''
        log.info("find_state_dir: {}".format(time.time()))
        state_path = None
        for path in self.search_paths:
            rootDir = path
            #log.info("rootDir: {}".format(rootDir))
            for dirName, subdirList, fileList in os.walk(rootDir, topdown=True):
                mydir = dirName.split(os.sep)[-1]
                #log.info("find_state_dir mydir = {}".format(mydir))
                if state_name == mydir and "salt-check-tests" in subdirList:
                    state_path = dirName
                    #log.info("state_path = {}".format(dirName))
                    return state_path
        return state_path


def _get_test_files(state_name):
    '''Given a path to the state files, gather the list of test files under
    the salt-check-test subdir'''
    log.info("_get_test_files: {}".format(time.time()))
    salt_check = SaltCheck()
    paths = salt_check.get_state_search_path_list()
    stl = StateTestLoader(search_paths=paths)
    mydir = stl.find_state_dir(state_name)
    stl.gather_files(mydir)
    #log.info("test files: {}".format(stl.test_files))
    return stl.test_files


def _get_top_states():
    ''' Show the dirs for the top file used for a particular minion'''
    salt_check = SaltCheck()
    return salt_check.get_top_states()


def run_state_tests(state_name):
    '''
    Runs tests for one state
    CLI Example:
        salt '*' salt_check.run_state_tests STATE-NAME
    '''
    log.info("run_state_test time: {}".format(time.time()))
    results_dict = {}
    if not state_name:
        return "State name required"
    scheck = SaltCheck()
    #log.info("Creating SaltCheck instance")
    # this should be done manually instead scheck.cache_master_files()
    log.info("Caching master files")
    paths = scheck.get_state_search_path_list()
    #log.info("State search paths: {}".format(paths))
    stl = StateTestLoader(search_paths=paths)
    mydir = stl.find_state_dir(state_name)
    #log.info("mydir: {}".format(mydir))
    if mydir:
        stl.gather_files(mydir)
        _get_test_files(state_name)
        stl.load_test_suite()
        results_dict = {}
        for key, value in stl.test_dict.items():
            result = scheck.run_test(value)
            results_dict[key] = result
        #log.info("State Name = {}, results_dict: {}".format(state_name, results_dict))
    return {state_name: results_dict}


def update_master_cache():
    '''
    Updates the master cache onto the minion - to transfer all salt-check-tests
    Should be done one time before running tests, and if tests are updated

    CLI Example:
        salt '*' salt_check.update_master_cache
    '''
    log.info("Caching master files")
    scheck = SaltCheck()
    scheck.cache_master_files()
    return True

def run_highstate_tests():
    '''
    Runs tests for all states included in a highstate
    CLI Example:
        salt '*' salt_check.run_highstate_tests
    '''
    states = _get_top_states()
    #log.info("States:  {}".format(states))
    return_dict = {}
    for state in states:
        log.info("Running state test: {} @ {}".format(state, time.time()))
        ret_dict = run_state_tests(state)
        return_dict.update(ret_dict)
    return return_dict


def run_test(**kwargs):
    '''
    Enables running one salt_check test via cli
    CLI Example::
        salt '*' salt_check.run_test
          test='{"module_and_function": "test.echo",
            "assertion": "assertEqual",
            "expected-return": "This works!",
            "args":["This works!"] }'
    '''
    # salt converts the string to a dictionary auto-magically
    log.info("run_test time: {}".format(time.time()))
    scheck = SaltCheck()
    test = kwargs.get('test', None)
    if test and isinstance(test, dict):
        return scheck.run_test(test)
        #return test
    else:
        return "test must be dictionary"
