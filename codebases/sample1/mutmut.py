#!/usr/bin/env python
# -*- coding: utf-8 -*-

from parso.python.tree import Name, Number, Keyword
from parso import parse
import re
import fnmatch
import itertools
import os
import shlex
import subprocess
import sys
import traceback
from configparser import ConfigParser, NoOptionError, NoSectionError
from functools import wraps
from io import open
from os.path import isdir, exists
from shutil import move, copy
from threading import Timer
from time import time
from typing import List

import click
from glob2 import glob

from mutmut import mutate_file, Context, list_mutations, __version__, \
    BAD_TIMEOUT, OK_SUSPICIOUS, BAD_SURVIVED, OK_KILLED, UNTESTED, MutationID
from mutmut.cache import register_mutants, update_mutant_status, \
    print_result_cache, cached_mutation_status, hash_of_tests, \
    filename_and_mutation_id_from_pk, cached_test_time, set_cached_test_time, \
    update_line_numbers, print_result_cache_junitxml, get_unified_diff

spinner = itertools.cycle('⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏')


# -*- coding: utf-8 -*-


__version__ = '1.6.0'


class MutationID(object):
    def __init__(self, line, index, line_number):
        self.line = line
        self.index = index
        self.line_number = line_number

    def __repr__(self):
        return 'MutationID(line="{}", index={}, line_number={})'.format(self.line, self.index, self.line_number)

    def __eq__(self, other):
        return (self.line, self.index, self.line_number) == (other.line, other.index, other.line_number)


ALL = MutationID(line='%all%', index=-1, line_number=-1)


class InvalidASTPatternException(Exception):
    pass


class ASTPattern(object):
    def __init__(self, source, **definitions):
        if definitions is None:
            definitions = {}
        source = source.strip()

        self.definitions = definitions

        self.module = parse(source)

        self.markers = []

        def get_leaf(line, column, of_type=None):
            r = self.module.children[0].get_leaf_for_position((line, column))
            while of_type is not None and r.type != of_type:
                r = r.parent
            return r

        def parse_markers(node):
            if hasattr(node, '_split_prefix'):
                for x in node._split_prefix():
                    parse_markers(x)

            if hasattr(node, 'children'):
                for x in node.children:
                    parse_markers(x)

            if node.type == 'comment':
                line, column = node.start_pos
                for match in re.finditer(r'\^(?P<value>[^\^]*)', node.value):
                    name = match.groupdict()['value'].strip()
                    d = definitions.get(name, {})
                    assert set(d.keys()) | {'of_type', 'marker_type'} == {
                        'of_type', 'marker_type'}
                    self.markers.append(dict(
                        node=get_leaf(line - 1, column +
                                      match.start(), of_type=d.get('of_type')),
                        marker_type=d.get('marker_type'),
                        name=name,
                    ))

        parse_markers(self.module)

        pattern_nodes = [x['node']
                         for x in self.markers if x['name'] == 'match' or x['name'] == '']
        if len(pattern_nodes) != 1:
            raise InvalidASTPatternException(
                "Found more than one match node. Match nodes are nodes with an empty name or with the explicit name 'match'")
        self.pattern = pattern_nodes[0]
        self.marker_type_by_id = {
            id(x['node']): x['marker_type'] for x in self.markers}

    def matches(self, node, pattern=None, skip_child=None):
        if pattern is None:
            pattern = self.pattern

        check_value = True
        check_children = True

        # Match type based on the name, so _keyword matches all keywords.
        # Special case for _all that matches everything
        if pattern.type == 'name' and pattern.value.startswith('_') and pattern.value[1:] in ('any', node.type):
            check_value = False

        # The advanced case where we've explicitly marked up a node with
        # the accepted types
        elif id(pattern) in self.marker_type_by_id:
            if self.marker_type_by_id[id(pattern)] in (pattern.type, 'any'):
                check_value = False
                check_children = False  # TODO: really? or just do this for 'any'?

        # Check node type strictly
        elif pattern.type != node.type:
            return False

        # Match children
        if check_children and hasattr(pattern, 'children'):
            if len(pattern.children) != len(node.children):
                return False

            for pattern_child, node_child in zip(pattern.children, node.children):
                if node_child is skip_child:  # prevent infinite recursion
                    continue

                if not self.matches(node=node_child, pattern=pattern_child, skip_child=node_child):
                    return False

        # Node value
        if check_value and hasattr(pattern, 'value'):
            if pattern.value != node.value:
                return False

        # Parent
        if pattern.parent.type != 'file_input':  # top level matches nothing
            if skip_child != node:
                return self.matches(node=node.parent, pattern=pattern.parent, skip_child=node)

        return True


# We have a global whitelist for constants of the pattern __all__, __version__, etc

dunder_whitelist = [
    'all',
    'version',
    'title',
    'package_name',
    'author',
    'description',
    'email',
    'version',
    'license',
    'copyright',
]


UNTESTED = 'untested'
OK_KILLED = 'ok_killed'
OK_SUSPICIOUS = 'ok_suspicious'
BAD_TIMEOUT = 'bad_timeout'
BAD_SURVIVED = 'bad_survived'


mutant_statuses = [
    UNTESTED,
    OK_KILLED,
    OK_SUSPICIOUS,
    BAD_TIMEOUT,
    BAD_SURVIVED,
]


def number_mutation(value, **_):
    suffix = ''
    if value.upper().endswith('L'):  # pragma: no cover (python 2 specific)
        suffix = value[-1]
        value = value[:-1]

    if value.upper().endswith('J'):
        suffix = value[-1]
        value = value[:-1]

    if value.startswith('0o'):
        base = 8
        value = value[2:]
    elif value.startswith('0x'):
        base = 16
        value = value[2:]
    elif value.startswith('0b'):
        base = 2
        value = value[2:]
    elif value.startswith('0') and len(value) > 1 and value[1] != '.':  # pragma: no cover (python 2 specific)
        base = 8
        value = value[1:]
    else:
        base = 10

    try:
        parsed = int(value, base=base)
    except ValueError:
        # Since it wasn't an int, it must be a float
        parsed = float(value)

    result = repr(parsed + 1)
    if not result.endswith(suffix):
        result += suffix
    return result


def string_mutation(value, **_):
    prefix = value[:min(
        [x for x in [value.find('"'), value.find("'")] if x != -1])]
    value = value[len(prefix):]

    if value.startswith('"""') or value.startswith("'''"):
        # We assume here that triple-quoted stuff are docs or other things
        # that mutation is meaningless for
        return prefix + value
    return prefix + value[0] + 'XX' + value[1:-1] + 'XX' + value[-1]


def partition_node_list(nodes, value):
    for i, n in enumerate(nodes):
        if hasattr(n, 'value') and n.value == value:
            return nodes[:i], n, nodes[i + 1:]

    assert False, "didn't find node to split on"


def lambda_mutation(children, **_):
    pre, op, post = partition_node_list(children, value=':')

    if len(post) == 1 and getattr(post[0], 'value', None) == 'None':
        return pre + [op] + [Number(value=' 0', start_pos=post[0].start_pos)]
    else:
        return pre + [op] + [Keyword(value=' None', start_pos=post[0].start_pos)]


NEWLINE = {'formatting': [], 'indent': '', 'type': 'endl', 'value': ''}


def argument_mutation(children, context, **_):
    """
    :type context: Context
    """
    if len(context.stack) >= 3 and context.stack[-3].type in ('power', 'atom_expr'):
        stack_pos_of_power_node = -3
    elif len(context.stack) >= 4 and context.stack[-4].type in ('power', 'atom_expr'):
        stack_pos_of_power_node = -4
    else:
        return

    power_node = context.stack[stack_pos_of_power_node]

    if power_node.children[0].type == 'name' and power_node.children[0].value in context.dict_synonyms:
        c = children[0]
        if c.type == 'name':
            children = children[:]
            children[0] = Name(
                c.value + 'XX', start_pos=c.start_pos, prefix=c.prefix)
            return children


def keyword_mutation(value, context, **_):
    if len(context.stack) > 2 and context.stack[-2].type in ('comp_op', 'sync_comp_for') and value in ('in', 'is'):
        return

    if len(context.stack) > 1 and context.stack[-2].type == 'for_stmt':
        return

    return {
        # 'not': 'not not',
        'not': '',
        'is': 'is not',  # this will cause "is not not" sometimes, so there's a hack to fix that later
        'in': 'not in',
        'break': 'continue',
        'continue': 'break',
        'True': 'False',
        'False': 'True',
    }.get(value)


import_from_star_pattern = ASTPattern("""
from _name import *
#                 ^
""")


def operator_mutation(value, node, **_):
    if import_from_star_pattern.matches(node=node):
        return

    if value in ('*', '**') and node.parent.type == 'param':
        return

    if value == '*' and node.parent.type == 'parameters':
        return

    if value in ('*', '**') and node.parent.type in ('argument', 'arglist'):
        return

    return {
        '+': '-',
        '-': '+',
        '*': '/',
        '/': '*',
        '//': '/',
        '%': '/',
        '<<': '>>',
        '>>': '<<',
        '&': '|',
        '|': '&',
        '^': '&',
        '**': '*',
        '~': '',

        '+=': ['-=', '='],
        '-=': ['+=', '='],
        '*=': ['/=', '='],
        '/=': ['*=', '='],
        '//=': ['/=', '='],
        '%=': ['/=', '='],
        '<<=': ['>>=', '='],
        '>>=': ['<<=', '='],
        '&=': ['|=', '='],
        '|=': ['&=', '='],
        '^=': ['&=', '='],
        '**=': ['*=', '='],
        '~=': '=',

        '<': '<=',
        '<=': '<',
        '>': '>=',
        '>=': '>',
        '==': '!=',
        '!=': '==',
        '<>': '==',
    }.get(value)


def and_or_test_mutation(children, node, **_):
    children = children[:]
    children[1] = Keyword(
        value={'and': ' or', 'or': ' and'}[children[1].value],
        start_pos=node.start_pos,
    )
    return children


def expression_mutation(children, **_):
    def handle_assignment(children):
        mutation_index = -1  # we mutate the last value to handle multiple assignement
        if getattr(children[mutation_index], 'value', '---') != 'None':
            x = ' None'
        else:
            x = ' ""'
        children = children[:]
        children[mutation_index] = Name(
            value=x, start_pos=children[mutation_index].start_pos)

        return children

    if children[0].type == 'operator' and children[0].value == ':':
        if len(children) > 2 and children[2].value == '=':
            # we need to copy the list here, to not get in place mutation on the next line!
            children = children[:]
            children[1:] = handle_assignment(children[1:])
    elif children[1].type == 'operator' and children[1].value == '=':
        children = handle_assignment(children)

    return children


def decorator_mutation(children, **_):
    assert children[-1].type == 'newline'
    return children[-1:]


array_subscript_pattern = ASTPattern("""
_name[_any]
#       ^
""")


function_call_pattern = ASTPattern("""
_name(_any)
#       ^
""")


def name_mutation(node, value, **_):
    simple_mutants = {
        'True': 'False',
        'False': 'True',
        'deepcopy': 'copy',
        'None': '""',
        # TODO: probably need to add a lot of things here... some builtins maybe, what more?
    }
    if value in simple_mutants:
        return simple_mutants[value]

    if array_subscript_pattern.matches(node=node):
        return 'None'

    if function_call_pattern.matches(node=node):
        return 'None'


mutations_by_type = {
    'operator': dict(value=operator_mutation),
    'keyword': dict(value=keyword_mutation),
    'number': dict(value=number_mutation),
    'name': dict(value=name_mutation),
    'string': dict(value=string_mutation),
    'argument': dict(children=argument_mutation),
    'or_test': dict(children=and_or_test_mutation),
    'and_test': dict(children=and_or_test_mutation),
    'lambdef': dict(children=lambda_mutation),
    'expr_stmt': dict(children=expression_mutation),
    'decorator': dict(children=decorator_mutation),
    'annassign': dict(children=expression_mutation),
}

# TODO: detect regexes and mutate them in nasty ways? Maybe mutate all strings as if they are regexes


def should_exclude(context, config):
    if config is None or config.covered_lines_by_filename is None:
        return False

    try:
        covered_lines = config.covered_lines_by_filename[context.filename]
    except KeyError:
        if config.coverage_data is not None:
            covered_lines = config.coverage_data.lines(
                os.path.abspath(context.filename))
            config.covered_lines_by_filename[context.filename] = covered_lines
        else:
            covered_lines = None

    if covered_lines is None:
        return True
    current_line = context.current_line_index + 1
    if current_line not in covered_lines:
        return True
    return False


class Context(object):
    def __init__(self, source=None, mutation_id=ALL, dict_synonyms=None, filename=None, config=None):
        self.index = 0
        self.remove_newline_at_end = False
        if source and source[-1] != '\n':
            source += '\n'
            self.remove_newline_at_end = True
        self.source = source
        self.mutation_id = mutation_id
        self.performed_mutation_ids = []
        assert isinstance(mutation_id, MutationID)
        self.current_line_index = 0
        self.filename = filename
        self.stack = []
        self.dict_synonyms = (dict_synonyms or []) + ['dict']
        self._source_by_line_number = None
        self._pragma_no_mutate_lines = None
        self._path_by_line = None
        self.config = config

    def exclude_line(self):
        return self.current_line_index in self.pragma_no_mutate_lines or should_exclude(context=self, config=self.config)

    @property
    def source_by_line_number(self):
        if self._source_by_line_number is None:
            self._source_by_line_number = self.source.split('\n')
        return self._source_by_line_number

    @property
    def current_source_line(self):
        return self.source_by_line_number[self.current_line_index]

    @property
    def mutation_id_of_current_index(self):
        return MutationID(line=self.current_source_line, index=self.index, line_number=self.current_line_index)

    @property
    def pragma_no_mutate_lines(self):
        if self._pragma_no_mutate_lines is None:
            self._pragma_no_mutate_lines = {
                i
                for i, line in enumerate(self.source_by_line_number)
                if '# pragma:' in line and 'no mutate' in line.partition('# pragma:')[-1]
            }
        return self._pragma_no_mutate_lines

    def should_mutate(self):
        if self.mutation_id == ALL:
            return True
        return self.mutation_id in (ALL, self.mutation_id_of_current_index)


def mutate(context):
    """
    :type context: Context
    :return: tuple of mutated source code and number of mutations performed
    :rtype: Tuple[str, int]
    """
    try:
        result = parse(context.source, error_recovery=False)
    except Exception:
        print('Failed to parse {}. Internal error from parso follows.'.format(
            context.filename))
        print('----------------------------------')
        raise
    mutate_list_of_nodes(result, context=context)
    mutated_source = result.get_code().replace(' not not ', ' ')
    if context.remove_newline_at_end:
        assert mutated_source[-1] == '\n'
        mutated_source = mutated_source[:-1]

    # If we said we mutated the code, check that it has actually changed
    if context.performed_mutation_ids:
        if context.source == mutated_source:
            raise RuntimeError(
                "Mutation context states that a mutation occurred but the "
                "mutated source remains the same as original")
    context.mutated_source = mutated_source
    return mutated_source, len(context.performed_mutation_ids)


def mutate_node(node, context):
    """
    :type context: Context
    """
    context.stack.append(node)
    try:
        if node.type in ('tfpdef', 'import_from', 'import_name'):
            return

        if node.type == 'atom_expr' and node.children and node.children[0].type == 'name' and node.children[0].value == '__import__':
            return

        if node.start_pos[0] - 1 != context.current_line_index:
            context.current_line_index = node.start_pos[0] - 1
            context.index = 0  # indexes are unique per line, so start over here!

        if node.type == 'expr_stmt':
            if node.children[0].type == 'name' and node.children[0].value.startswith('__') and node.children[0].value.endswith('__'):
                if node.children[0].value[2:-2] in dunder_whitelist:
                    return

        if hasattr(node, 'children'):
            mutate_list_of_nodes(node, context=context)

            # this is just an optimization to stop early
            if context.performed_mutation_ids and context.mutation_id != ALL:
                return

        mutation = mutations_by_type.get(node.type)

        if mutation is None:
            return

        for key, value in sorted(mutation.items()):
            old = getattr(node, key)
            if context.exclude_line():
                continue

            new = value(
                context=context,
                node=node,
                value=getattr(node, 'value', None),
                children=getattr(node, 'children', None),
            )

            if isinstance(new, list) and not isinstance(old, list):
                # multiple mutations
                new_list = new
            else:
                # one mutation
                new_list = [new]

            # go through the alternate mutations in reverse as they may have
            # adverse effects on subsequent mutations, this ensures the last
            # mutation applied is the original/default/legacy mutmut mutation
            for new in reversed(new_list):
                assert not callable(new)
                if new is not None and new != old:
                    if context.should_mutate():
                        context.performed_mutation_ids.append(
                            context.mutation_id_of_current_index)
                        setattr(node, key, new)
                    context.index += 1
                # this is just an optimization to stop early
                if context.performed_mutation_ids and context.mutation_id != ALL:
                    return
    finally:
        context.stack.pop()


def mutate_list_of_nodes(node, context):
    """
    :type context: Context
    """
    return_annotation_started = False

    for child_node in node.children:
        if child_node.type == 'operator' and child_node.value == '->':
            return_annotation_started = True

        if return_annotation_started and child_node.type == 'operator' and child_node.value == ':':
            return_annotation_started = False

        if return_annotation_started:
            continue

        mutate_node(child_node, context=context)

        # this is just an optimization to stop early
        if context.performed_mutation_ids and context.mutation_id != ALL:
            return


def list_mutations(context):
    """
    :type context: Context
    """
    assert context.mutation_id == ALL
    mutate(context)
    return context.performed_mutation_ids


def mutate_file(backup, context):
    """
    :type backup: bool
    :type context: Context
    :return: Tuple[str, str]
    """
    with open(context.filename) as f:
        original = f.read()
    context.source = original
    if backup:
        with open(context.filename + '.bak', 'w') as f:
            f.write(original)
    mutated, _ = mutate(context)
    with open(context.filename, 'w') as f:
        f.write(mutated)
    return original, mutated
    
# decorator
def config_from_setup_cfg(**defaults):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            config_parser = ConfigParser()
            config_parser.read('setup.cfg')

            def s(key, default):
                try:
                    return config_parser.get('mutmut', key)
                except (NoOptionError, NoSectionError):
                    return default

            for k in list(kwargs.keys()):
                if not kwargs[k]:
                    kwargs[k] = s(k, defaults.get(k))
            f(*args, **kwargs)

        return wrapper
    return decorator


def status_printer():
    """Manage the printing and in-place updating of a line of characters
    .. note::
        If the string is longer than a line, then in-place updating may not
        work (it will print a new line at each refresh).
    """
    last_len = [0]

    def p(s):
        s = next(spinner) + ' ' + s
        len_s = len(s)
        output = '\r' + s + (' ' * max(last_len[0] - len_s, 0))
        sys.stdout.write(output)
        sys.stdout.flush()
        last_len[0] = len_s
    return p


print_status = status_printer()


def guess_paths_to_mutate():
    """Guess the path to source code to mutate
    :rtype: str
    """
    this_dir = os.getcwd().split(os.sep)[-1]
    if isdir('lib'):
        return 'lib'
    elif isdir('src'):
        return 'src'
    elif isdir(this_dir):
        return this_dir
    elif isdir(this_dir.replace('-', '_')):
        return this_dir.replace('-', '_')
    elif isdir(this_dir.replace(' ', '_')):
        return this_dir.replace(' ', '_')
    elif isdir(this_dir.replace('-', '')):
        return this_dir.replace('-', '')
    elif isdir(this_dir.replace(' ', '')):
        return this_dir.replace(' ', '')
    raise FileNotFoundError(
        'Could not figure out where the code to mutate is. '
        'Please specify it on the command line using --paths-to-mutate, '
        'or by adding "paths_to_mutate=code_dir" in setup.cfg to the [mutmut] section.')


def do_apply(mutation_pk, dict_synonyms, backup):
    """Apply a specified mutant to the source code
    :param mutation_pk: mutmut cache primary key of the mutant to apply
    :type mutation_pk: str
    :param dict_synonyms: list of synonym keywords for a python dictionary
    :type dict_synonyms: list[str]
    :param backup: if :obj:`True` create a backup of the source file
        before applying the mutation
    :type backup: bool
    """
    filename, mutation_id = filename_and_mutation_id_from_pk(int(mutation_pk))

    update_line_numbers(filename)

    context = Context(
        mutation_id=mutation_id,
        filename=filename,
        dict_synonyms=dict_synonyms,
    )
    mutate_file(
        backup=backup,
        context=context,
    )


null_out = open(os.devnull, 'w')


class Config(object):
    def __init__(self, swallow_output, test_command, covered_lines_by_filename,
                 baseline_time_elapsed, test_time_multiplier, test_time_base,
                 backup, dict_synonyms, total, using_testmon, cache_only,
                 tests_dirs, hash_of_tests, pre_mutation, post_mutation,
                 coverage_data):
        self.swallow_output = swallow_output
        self.test_command = test_command
        self.covered_lines_by_filename = covered_lines_by_filename
        self.baseline_time_elapsed = baseline_time_elapsed
        self.test_time_multipler = test_time_multiplier
        self.test_time_base = test_time_base
        self.backup = backup
        self.dict_synonyms = dict_synonyms
        self.total = total
        self.using_testmon = using_testmon
        self.cache_only = cache_only
        self.tests_dirs = tests_dirs
        self.hash_of_tests = hash_of_tests
        self.post_mutation = post_mutation
        self.pre_mutation = pre_mutation
        self.coverage_data = coverage_data


class Progress(object):
    def __init__(self):
        self.progress = 0
        self.skipped = 0
        self.killed_mutants = 0
        self.surviving_mutants = 0
        self.surviving_mutants_timeout = 0
        self.suspicious_mutants = 0

    def print(self, total):
        print_status('{}/{}  🎉 {}  ⏰ {}  🤔 {}  🙁 {}'.format(self.progress, total, self.killed_mutants,
                                                            self.surviving_mutants_timeout, self.suspicious_mutants, self.surviving_mutants))


@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument('command', nargs=1, required=False)
@click.argument('argument', nargs=1, required=False)
@click.argument('argument2', nargs=1, required=False)
@click.option('--paths-to-mutate', type=click.STRING)
@click.option('--paths-to-exclude', type=click.STRING, required=False)
@click.option('--backup/--no-backup', default=False)
@click.option('--runner')
@click.option('--use-coverage', is_flag=True, default=False)
@click.option('--use-patch-file', help='Only mutate lines added/changed in the given patch file')
@click.option('--tests-dir')
@click.option('-m', '--test-time-multiplier', default=2.0, type=float)
@click.option('-b', '--test-time-base', default=0.0, type=float)
@click.option('-s', '--swallow-output', help='turn off output capture', is_flag=True)
@click.option('--dict-synonyms')
@click.option('--cache-only', is_flag=True, default=False)
@click.option('--version', is_flag=True, default=False)
@click.option('--suspicious-policy', type=click.Choice(['ignore', 'skipped', 'error', 'failure']), default='ignore')
@click.option('--untested-policy', type=click.Choice(['ignore', 'skipped', 'error', 'failure']), default='ignore')
@click.option('--pre-mutation')
@click.option('--post-mutation')
@config_from_setup_cfg(
    dict_synonyms='',
    paths_to_exclude='',
    runner='python -m pytest -x',
    tests_dir='tests/:test/',
    pre_mutation=None,
    post_mutation=None,
    use_patch_file=None,
)
def climain(command, argument, argument2, paths_to_mutate, backup, runner, tests_dir,
            test_time_multiplier, test_time_base,
            swallow_output, use_coverage, dict_synonyms, cache_only, version,
            suspicious_policy, untested_policy, pre_mutation, post_mutation,
            use_patch_file, paths_to_exclude):
    """
commands:\n
    run [mutation id]\n
        Runs mutmut. You probably want to start with just trying this. If you supply a mutation ID mutmut will check just this mutant.\n
    results\n
        Print the results.\n
    apply [mutation id]\n
        Apply a mutation on disk.\n
    show [mutation id]\n
        Show a mutation diff.\n
    show [path to file]\n
        Show all mutation diffs for this file.\n
    junitxml\n
        Show a mutation diff with junitxml format.
    """
    if test_time_base is None:  # click sets the default=0.0 to None
        test_time_base = 0.0
    if test_time_multiplier is None:  # click sets the default=0.0 to None
        test_time_multiplier = 0.0
    sys.exit(main(command, argument, argument2, paths_to_mutate, backup, runner,
                  tests_dir, test_time_multiplier, test_time_base,
                  swallow_output, use_coverage, dict_synonyms, cache_only,
                  version, suspicious_policy, untested_policy, pre_mutation,
                  post_mutation, use_patch_file, paths_to_exclude))


def main(command, argument, argument2, paths_to_mutate, backup, runner, tests_dir,
         test_time_multiplier, test_time_base,
         swallow_output, use_coverage, dict_synonyms, cache_only, version,
         suspicious_policy, untested_policy, pre_mutation, post_mutation,
         use_patch_file, paths_to_exclude):
    """return exit code, after performing an mutation test run.
    :return: the exit code from executing the mutation tests
    :rtype: int
    """
    if version:
        print("mutmut version {}".format(__version__))
        return 0

    if use_coverage and use_patch_file:
        raise click.BadArgumentUsage(
            "You can't combine --use-coverage and --use-patch")

    valid_commands = ['run', 'results', 'apply', 'show', 'junitxml']
    if command not in valid_commands:
        raise click.BadArgumentUsage('{} is not a valid command, must be one of {}'.format(
            command, ', '.join(valid_commands)))

    if command == 'results' and argument:
        raise click.BadArgumentUsage(
            'The {} command takes no arguments'.format(command))

    dict_synonyms = [x.strip() for x in dict_synonyms.split(',')]

    if command in ('show', 'diff'):
        if not argument:
            print_result_cache()
            return 0

        if argument == 'all':
            print_result_cache(
                show_diffs=True, dict_synonyms=dict_synonyms, print_only_filename=argument2)
            return 0

        if os.path.isfile(argument):
            print_result_cache(show_diffs=True, only_this_file=argument)
            return 0

        print(get_unified_diff(argument, dict_synonyms))
        return 0

    if use_coverage and not exists('.coverage'):
        raise FileNotFoundError(
            'No .coverage file found. You must generate a coverage file to use this feature.')

    if command == 'results':
        print_result_cache()
        return 0

    if command == 'junitxml':
        print_result_cache_junitxml(
            dict_synonyms, suspicious_policy, untested_policy)
        return 0

    if command == 'apply':
        do_apply(argument, dict_synonyms, backup)
        return 0

    if paths_to_mutate is None:
        paths_to_mutate = guess_paths_to_mutate()

    if not isinstance(paths_to_mutate, (list, tuple)):
        paths_to_mutate = [x.strip() for x in paths_to_mutate.split(',')]

    if not paths_to_mutate:
        raise click.BadOptionUsage(
            '--paths-to-mutate', 'You must specify a list of paths to mutate. Either as a command line argument, or by setting paths_to_mutate under the section [mutmut] in setup.cfg')

    tests_dirs = []
    for p in tests_dir.split(':'):
        tests_dirs.extend(glob(p, recursive=True))

    for p in paths_to_mutate:
        for pt in tests_dir.split(':'):
            tests_dirs.extend(glob(p + '/**/' + pt, recursive=True))
    del tests_dir

    # stop python from creating .pyc files
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

    using_testmon = '--testmon' in runner

    print("""
- Mutation testing starting -
These are the steps:
1. A full test suite run will be made to make sure we
   can run the tests successfully and we know how long
   it takes (to detect infinite loops for example)
2. Mutants will be generated and checked
Results are stored in .mutmut-cache.
Print found mutants with `mutmut results`.
Legend for output:
🎉 Killed mutants.   The goal is for everything to end up in this bucket.
⏰ Timeout.          Test suite took 10 times as long as the baseline so were killed.
🤔 Suspicious.       Tests took a long time, but not long enough to be fatal.
🙁 Survived.         This means your tests needs to be expanded.
""")
    baseline_time_elapsed = time_test_suite(
        swallow_output=not swallow_output,
        test_command=runner,
        using_testmon=using_testmon
    )

    if using_testmon:
        copy('.testmondata', '.testmondata-initial')

    # if we're running in a mode with externally whitelisted lines
    covered_lines_by_filename = None
    coverage_data = None
    if use_coverage or use_patch_file:
        covered_lines_by_filename = {}
        if use_coverage:
            coverage_data = read_coverage_data()
            check_coverage_data_filepaths(coverage_data)
        else:
            assert use_patch_file
            covered_lines_by_filename = read_patch_data(use_patch_file)

    if command != 'run':
        raise click.BadArgumentUsage("Invalid command {}".format(command))

    mutations_by_file = {}

    paths_to_exclude = paths_to_exclude or ''
    if paths_to_exclude:
        paths_to_exclude = [path.strip()
                            for path in paths_to_exclude.split(',')]

    config = Config(
        total=0,  # we'll fill this in later!
        swallow_output=not swallow_output,
        test_command=runner,
        covered_lines_by_filename=covered_lines_by_filename,
        coverage_data=coverage_data,
        baseline_time_elapsed=baseline_time_elapsed,
        backup=backup,
        dict_synonyms=dict_synonyms,
        using_testmon=using_testmon,
        cache_only=cache_only,
        tests_dirs=tests_dirs,
        hash_of_tests=hash_of_tests(tests_dirs),
        test_time_multiplier=test_time_multiplier,
        test_time_base=test_time_base,
        pre_mutation=pre_mutation,
        post_mutation=post_mutation,
    )

    if argument is None:
        for path in paths_to_mutate:
            for filename in python_source_files(path, tests_dirs, paths_to_exclude):
                update_line_numbers(filename)
                add_mutations_by_file(
                    mutations_by_file, filename, dict_synonyms, config)
    else:
        filename, mutation_id = filename_and_mutation_id_from_pk(int(argument))
        mutations_by_file[filename] = [mutation_id]

    config.total = sum(len(mutations)
                       for mutations in mutations_by_file.values())

    print()
    print('2. Checking mutants')
    progress = Progress()

    try:
        run_mutation_tests(config=config, progress=progress,
                           mutations_by_file=mutations_by_file)
    except Exception as e:
        traceback.print_exc()
        return compute_exit_code(progress, e)
    else:
        return compute_exit_code(progress)
    finally:
        print()  # make sure we end the output with a newline


def check_coverage_data_filepaths(coverage_data):
    for filepath in coverage_data._lines:
        if not os.path.exists(filepath):
            raise ValueError(
                'Filepaths in .coverage not recognized, try recreating the .coverage file manually.')


def get_mutations_by_file_from_cache(mutation_pk):
    filename, mutation_id = filename_and_mutation_id_from_pk(int(mutation_pk))
    return {filename: [mutation_id]}


def popen_streaming_output(cmd, callback, timeout=None):
    """Open a subprocess and stream its output without hard-blocking.
    :param cmd: the command to execute within the subprocess
    :type cmd: str
    :param callback: function that intakes the subprocess' stdout line by line.
        It is called for each line received from the subprocess' stdout stream.
    :type callback: Callable[[Context], bool]
    :param timeout: the timeout time of the subprocess
    :type timeout: float
    :raises TimeoutError: if the subprocess' execution time exceeds
        the timeout time
    :return: the return code of the executed subprocess
    :rtype: int
    """
    if os.name == 'nt':  # pragma: no cover
        process = subprocess.Popen(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout = process.stdout
    else:
        master, slave = os.openpty()
        process = subprocess.Popen(
            shlex.split(cmd, posix=True),
            stdout=slave,
            stderr=slave
        )
        stdout = os.fdopen(master)
        os.close(slave)

    def kill(process_):
        """Kill the specified process on Timer completion"""
        try:
            process_.kill()
        except OSError:
            pass

    # python 2-3 agnostic process timer
    timer = Timer(timeout, kill, [process])
    timer.setDaemon(True)
    timer.start()

    while process.returncode is None:
        try:
            if os.name == 'nt':  # pragma: no cover
                line = stdout.readline()
                # windows gives readline() raw stdout as a b''
                # need to decode it
                line = line.decode("utf-8")
                if line:  # ignore empty strings and None
                    callback(line.rstrip())
            else:
                while True:
                    line = stdout.readline()
                    if not line:
                        break
                    callback(line.rstrip())
        except (IOError, OSError):
            # This seems to happen on some platforms, including TravisCI.
            # It seems like it's ok to just let this pass here, you just
            # won't get as nice feedback.
            pass
        if not timer.is_alive():
            raise TimeoutError(
                "subprocess running command '{}' timed out after {} seconds".format(cmd, timeout))
        process.poll()

    # we have returned from the subprocess cancel the timer if it is running
    timer.cancel()

    return process.returncode


def tests_pass(config: Config, callback) -> bool:
    """
    :return: :obj:`True` if the tests pass, otherwise :obj:`False`
    """
    if config.using_testmon:
        copy('.testmondata-initial', '.testmondata')

    returncode = popen_streaming_output(
        config.test_command, callback, timeout=config.baseline_time_elapsed * 10)
    return returncode == 0 or (config.using_testmon and returncode == 5)


def run_mutation(config: Config, filename: str, mutation_id: MutationID, callback) -> str:
    """
    :return: (computed or cached) status of the tested mutant, one of mutant_statuses
    """
    context = Context(
        mutation_id=mutation_id,
        filename=filename,
        dict_synonyms=config.dict_synonyms,
        config=config,
    )

    cached_status = cached_mutation_status(
        filename, mutation_id, config.hash_of_tests)

    if cached_status != UNTESTED:
        return cached_status

    if config.pre_mutation:
        result = subprocess.check_output(
            config.pre_mutation, shell=True).decode().strip()
        if result and not config.swallow_output:
            print(result)

    try:
        mutate_file(
            backup=True,
            context=context
        )
        start = time()
        try:
            survived = tests_pass(config=config, callback=callback)
        except TimeoutError:
            return BAD_TIMEOUT

        time_elapsed = time() - start
        if not survived and time_elapsed > config.test_time_base + (config.baseline_time_elapsed * config.test_time_multipler):
            return OK_SUSPICIOUS

        if survived:
            return BAD_SURVIVED
        else:
            return OK_KILLED
    finally:
        move(filename + '.bak', filename)

        if config.post_mutation:
            result = subprocess.check_output(
                config.post_mutation, shell=True).decode().strip()
            if result and not config.swallow_output:
                print(result)


def run_mutation_tests_for_file(config: Config, progress: Progress, file_to_mutate: str, mutations: List[MutationID]) -> None:
    """
    :type config: Config
    :type progress: Progress
    :type file_to_mutate: str
    :type mutations: list[MutationID]
    """
    def feedback(line):
        if not config.swallow_output:
            print(line)
        progress.print(total=config.total)

    for mutation_id in mutations:
        status = run_mutation(config, file_to_mutate,
                              mutation_id, callback=feedback)
        update_mutant_status(file_to_mutate, mutation_id,
                             status, config.hash_of_tests)

        if status == BAD_SURVIVED:
            progress.surviving_mutants += 1
        elif status == BAD_TIMEOUT:
            progress.surviving_mutants_timeout += 1
        elif status == OK_KILLED:
            progress.killed_mutants += 1
        elif status == OK_SUSPICIOUS:
            progress.suspicious_mutants += 1
        else:
            raise ValueError(
                'Unknown status returned from run_mutation: {}'.format(status))

        progress.progress += 1
        progress.print(total=config.total)


def run_mutation_tests(config, progress, mutations_by_file):
    """
    :type config: Config
    :type progress: Progress
    :type mutations_by_file: dict[str, list[MutationID]]
    """
    for file_to_mutate, mutations in mutations_by_file.items():
        progress.print(total=config.total)

        run_mutation_tests_for_file(
            config, progress, file_to_mutate, mutations)


def read_coverage_data():
    """
    :rtype: CoverageData or None
    """
    try:
        # noinspection PyPackageRequirements,PyUnresolvedReferences
        from coverage import Coverage
    except ImportError as e:
        raise ImportError(
            'The --use-coverage feature requires the coverage library. Run "pip install --force-reinstall mutmut[coverage]"') from e
    cov = Coverage('.coverage')
    cov.load()
    return cov.get_data()


def read_patch_data(patch_file_path):
    try:
        # noinspection PyPackageRequirements
        import whatthepatch
    except ImportError as e:
        raise ImportError(
            'The --use-patch feature requires the whatthepatch library. Run "pip install --force-reinstall mutmut[patch]"') from e
    with open(patch_file_path) as f:
        diffs = whatthepatch.parse_patch(f.read())

    return {
        diff.header.new_path: {
            change.new for change in diff.changes if change.old is None}
        for diff in diffs
    }


def time_test_suite(swallow_output, test_command, using_testmon):
    """Execute a test suite specified by ``test_command`` and record
    the time it took to execute the test suite as a floating point number
    :param swallow_output: if :obj:`True` test stdout will be not be printed
    :type swallow_output: bool
    :param test_command: command to spawn the testing subprocess
    :type test_command: str
    :param using_testmon: if :obj:`True` the test return code evaluation will
        accommodate for ``pytest-testmon``
    :type using_testmon: bool
    :return: execution time of the test suite
    :rtype: float
    """
    cached_time = cached_test_time()
    if cached_time is not None:
        print('1. Using cached time for baseline tests, to run baseline again delete the cache file')
        return cached_time

    print('1. Running tests without mutations')
    start_time = time()

    output = []

    def feedback(line):
        if not swallow_output:
            print(line)
        print_status('Running...')
        output.append(line)

    returncode = popen_streaming_output(test_command, feedback)

    if returncode == 0 or (using_testmon and returncode == 5):
        baseline_time_elapsed = time() - start_time
    else:
        raise RuntimeError("Tests don't run cleanly without mutations. Test command was: {}\n\nOutput:\n\n{}".format(
            test_command, '\n'.join(output)))

    print('Done')

    set_cached_test_time(baseline_time_elapsed)

    return baseline_time_elapsed


def add_mutations_by_file(mutations_by_file, filename, dict_synonyms, config):
    """
    :type mutations_by_file: dict[str, list[MutationID]]
    :type filename: str
    :type exclude: Callable[[Context], bool]
    :type dict_synonyms: list[str]
    """
    with open(filename) as f:
        source = f.read()
    context = Context(
        source=source,
        filename=filename,
        config=config,
        dict_synonyms=dict_synonyms,
    )

    try:
        mutations_by_file[filename] = list_mutations(context)
        register_mutants(mutations_by_file)
    except Exception as e:
        raise RuntimeError('Failed while creating mutations for {}, for line "{}"'.format(
            context.filename, context.current_source_line)) from e


def python_source_files(path, tests_dirs, paths_to_exclude=None):
    """Attempt to guess where the python source files to mutate are and yield
    their paths
    :param path: path to a python source file or package directory
    :type path: str
    :param tests_dirs: list of directory paths containing test files
        (we do not want to mutate these!)
    :type tests_dirs: list[str]
    :param paths_to_exclude: list of UNIX filename patterns to exclude
    :type paths_to_exclude: list[str]
    :return: generator listing the paths to the python source files to mutate
    :rtype: Generator[str, None, None]
    """
    paths_to_exclude = paths_to_exclude or []
    if isdir(path):
        for root, dirs, files in os.walk(path, topdown=True):
            for exclude_pattern in paths_to_exclude:
                dirs[:] = [d for d in dirs if not fnmatch.fnmatch(
                    d, exclude_pattern)]
                files[:] = [f for f in files if not fnmatch.fnmatch(
                    f, exclude_pattern)]

            dirs[:] = [d for d in dirs if os.path.join(
                root, d) not in tests_dirs]
            for filename in files:
                if filename.endswith('.py'):
                    yield os.path.join(root, filename)
    else:
        yield path


def compute_exit_code(progress, exception=None):
    """Compute an exit code for mutmut mutation testing
    The following exit codes are available for mutmut:
     * 0 if all mutants were killed (OK_KILLED)
     * 1 if a fatal error occurred
     * 2 if one or more mutants survived (BAD_SURVIVED)
     * 4 if one or more mutants timed out (BAD_TIMEOUT)
     * 8 if one or more mutants caused tests to take twice as long (OK_SUSPICIOUS)
     Exit codes 1 to 8 will be bit-ORed so that it is possible to know what
     different mutant statuses occurred during mutation testing.
    :param exception:
    :type exception: Exception
    :param progress:
    :type progress: Progress
    :return: integer noting the exit code of the mutation tests.
    :rtype: int
    """
    code = 0
    if exception is not None:
        code = code | 1
    if progress.surviving_mutants > 0:
        code = code | 2
    if progress.surviving_mutants_timeout > 0:
        code = code | 4
    if progress.suspicious_mutants > 0:
        code = code | 8
    return code


if __name__ == '__main__':
    climain()
