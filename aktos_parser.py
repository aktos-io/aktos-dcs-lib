# coding: utf-8

import re
from pprint import pprint
import sys

def warning(*objs):
    sys.stderr.write("Warning: " + ''.join(*objs + ['\n']))

class MarkdownConfig(object):
    """
    self.flatten(): returns flattened array list of config file
    self.tests(): runs tests

    example usage:

        cfg = MarkdownConfig('test-config.md')
        cfg.tests()
        for fl in cfg.flatten():
            print ''.join(fl)

    """
    def __init__(self, config_file=None):
        if config_file is not None:
            self.open_config(config_file)


    def open_config(self, config_file):
        try:
            with open(config_file) as f:
                self.content = f.read().decode('utf-8')
        except:
            raise Exception("File can not be opened: ", config_file)


    def find_indent_char(self, content):
        m = re.search(r'^([ \t]{1,})[a-zA-Z_0-9\*]+', content, re.M|re.L|re.U)
        if m:
            #print "groups: ", m.groups()
            self.indent = m.group(1)
        else:
            self.indent = ' ' * 2

        #print "DEBUG: indent char: ", repr(self.indent)


    def flatten(self):
        return self._flatten(self.content)

    def _flatten(self, content):
        """
        :param content:
        :param prev:
        :return:

        """
        self.find_indent_char(content)
        parent = []
        flattened = []

        for line in content.split('\n'):
            if line.strip():
                indent_level = self.get_indent_level(line)
                if indent_level == len(parent):
                    pass
                elif indent_level == len(parent) + 1:
                    # one more level indent
                    parent = flattened[-1]
                elif indent_level < len(parent):
                    # one level dedent
                    parent = parent[:indent_level]
                elif indent_level > len(parent) + 1:
                    raise BaseException

                #print "line, parent, flattened: ", line
                #pprint(parent)
                #pprint(flattened)

                flattened.append(parent + [line.strip()])

        return flattened

    def flat_dict(self):
        flat_list = self.flatten()
        _dict = {}
        for i in flat_list:
            try:
                last_key, value = i[-1].split(':')
                value = value.strip()
                if value:
                    try:
                        if len(value.split('.')) > 1:
                            value = float(value)
                        else:
                            value = int(value)
                    except:
                        pass

                    stripped_keys = [j.replace(':', '') for j in i[:-1]]
                    keys = stripped_keys + [last_key]
                    flat_key = '.'.join(keys)
                    _dict[flat_key] = value
            except:
                pass

        #pprint(_dict)
        return _dict

    def flat_list(self):
        return self.flatten()

    def flat_list_str(self, config_str=None):
        if not config_str:
            config_str = self.content

        flatten = self._flatten(config_str)
        return '\n'.join([''.join(i) for i in flatten])




    def test_flattened_1(self):
        import textwrap

        input_config = []
        expected_output = []

        i = """
            a:
                b: 1
                c: 2
                d:
                    aa: 3
                    bb: 4
                    cc:
                        aaa: 5
                        bbb: 6
                e:
                    dd: 123
                    ee: 567

            b: 1

            c:
                f: 5
        """

        o = """
            a:
            a:b: 1
            a:c: 2
            a:d:
            a:d:aa: 3
            a:d:bb: 4
            a:d:cc:
            a:d:cc:aaa: 5
            a:d:cc:bbb: 6
            a:e:
            a:e:dd: 123
            a:e:ee: 567
            b: 1
            c:
            c:f: 5
        """

        input_config.append(i)
        expected_output.append(o)

        i = """
            a
                b
                    c
                d
                    e
                f:1
                    g: 3

        """
        o = """
            a
            ab
            abc
            ad
            ade
            af:1
            af:1g: 3

        """
        input_config.append(i)
        expected_output.append(o)


        for i in range(len(input_config)):
            print "Performing test %d..." % (i+1)
            config_file = input_config[i]
            expected = expected_output[i]

            config_file = textwrap.dedent(config_file)
            expected = textwrap.dedent(expected)

            config_file = config_file.strip()
            expected = expected.strip()

            flatten = self.flat_list_str(config_file)

            assert flatten == expected

    def tests(self):
        self.test_flattened_1()
        print "All tests passed successfully..."

    def test_indent(self):
        for line in self.content.split('\n'):
            print "indent: ", self.get_indent_level(line), line

    def get_indent_level(self, string, prev_level=0):
        if string[:len(self.indent)] == self.indent:
            prev_level += 1
            try:
                rest = string[len(self.indent):]
                return self.get_indent_level(rest, prev_level=prev_level)
            except IndexError:
                pass
        return prev_level



class AktosConfig(MarkdownConfig):
    """
    example config:

        a:
            b:
                c: 1
                d: 2
            e: 3
        f: 4

    flatten:



    raw_config_table:
    [
        ['a:', 'b:', 'c: 1'],
        ['a:', 'b:', 'd: 2'],
        ['a:', 'e: 3'],
        ['f: 4'],
    ]

    flat_dict:

    {
        'a.b.c': 1,
        'a.b.d': 2,
        'a.e': 3,
        'f': 4,
    }
    """
    def raw_config_table(self):
        """
        :return: lines which have ":..." at the end
        """
        flatten = self.flatten()
        flatten_cfg = [l for l in flatten if len(l[-1].split(':')[1].strip()) > 0]
        return flatten_cfg

    def raw_config_table_str(self):
        for l in self.raw_config_table():
            print ''.join(l)

    def get(self, key_tree=None, default_value=None):
        """

        :param key_tree: "key.of.the.path"
        :param default_value: returns this value if no key_tree found
        :return: config value

        if no key_tree is given, whole tree is returned
        """
        flattened_dictionary = self.flat_dict()
        #print "Flatten dict: ", flattened_dictionary
        if key_tree is None:
            return flattened_dictionary

        try:
            return flattened_dictionary[key_tree]
        except:
            # get any values including this "key_tree"
            s = {}
            for k, v in flattened_dictionary.iteritems():
                if k.startswith(key_tree):
                    #print "k, v: ", k, v
                    k = remove_prefix(k, key_tree + ".")
                    s[k] = v

            if s == {}:
                s = default_value
            return s


def remove_prefix(x, prefix):
    return x.split(prefix, 1)[-1]

if __name__ == '__main__':
    c = AktosConfig('aktos-parser-test2.db')
    c.tests()
    #pprint(c.raw_config_table())
    pprint(c.flat_dict())
    print(c.flat_list_str())
    #import code; code.interact(local=locals())
    
