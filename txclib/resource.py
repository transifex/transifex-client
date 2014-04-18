import collections
import os
import os.path
import re
try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class State:
    def __init__(self):
        self.transitions = dict()
        self.exception_transitions = dict()
        self.tags = set()

    def add(self, c, state):
        if c not in self.transitions:
            self.transitions[c] = set([state])
        else:
            self.transitions[c].add(state)

    def update(self, c, state_set):
        if c not in self.transitions:
            self.transitions[c] = set(state_set)
        else:
            self.transitions[c].update(state_set)


class Automaton:
    def __init__(self):
        self.start = None
        self.goals = set()

    def reachable_states(self):
        start = self.start
        if start is None:
            return
        visited = set()
        queue = collections.deque([start])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            for state_set in current.transitions.values():
                queue.extend(state_set)
            yield current

    @classmethod
    def union(cls, *automata):
        result = cls()
        result.start = State()
        for automaton in automata:
            for c, state_set in automaton.start.transitions.iteritems():
                result.start.update(c, state_set)
            result.goals.update(automaton.goals)
        return result

    @classmethod
    def create_dfa(cls, start, goals):
        result = cls()
        result.start = State()
        start_state_set = frozenset([start])
        mapping = {start_state_set: result.start}
        queue = collections.deque([(start_state_set, result.start)])
        while queue:
            current_state_set, current_state = queue.popleft()
            for state in current_state_set:
                current_state.tags.update(state.tags)
            if current_state_set & goals:
                result.goals.add(current_state)
            d = {}
            for state in current_state_set:
                for c, state_set in state.transitions.iteritems():
                    if not c in d:
                        d[c] = list()
                    d[c].append(state_set)

            for c, list_of_state_sets in d.iteritems():
                state_set = frozenset().union(*list_of_state_sets)
                if not state_set in mapping:
                    state = State()
                    mapping[state_set] = state
                    queue.append((state_set, state))
                else:
                    state = mapping[state_set]
                current_state.add(c, state)
        return result

    def matches(self, s):
        states = [self.start]
        for c in s:
            next_states = set()
            for current in states:
                for exception_class, state_set in current.exception_transitions.iteritems():
                    if c not in exception_class:
                        next_states.update(state_set)
                if c in current.transitions:
                    next_states.update(current.transitions[c])
            if not next_states:
                return False, None
            states = next_states

        goal_states = states & self.goals
        if not goal_states:
            return False, None
        tags = set()
        for goal in goal_states:
            tags.update(goal.tags)
        return True, tags


class Resource:
    @classmethod
    def create_from_config(cls, config, name):
        r = cls()
        r.name = name
        r.project_slug, r.resource_slug = name.split('.', 1)
        r.file_filter = FileFilter(r, config.get(name, "file_filter"))
        r.source_lang = config.get(name, "source_lang")
        try:
            r.source_file = config.get(name, "source_file")
        except configparser.NoOptionError:
            r.source_file = r.file_filter.expression.replace("<lang>", r.source_lang)
        values = set()
        r.trans = {}
        for (name, value) in config.items(name):
            if not name.startswith("trans."):
                continue
            if value in values:
                raise Exception(
                    "Your configuration seems wrong. "
                    "You have multiple languages pointing to the same file."
                )
            lang = name.split('.')[1]
            r.trans[lang] = value
            values.add(value)
        return r


class FileFilter:
    def __init__(self, resource, expression):
        self.resource = resource
        self.expression = expression
        self.re = re.compile("".join(self._match_language_re()))

    def lang(self, s):
        m = self.re.match(s)
        if not m:
            return None
        return m.group("lang")

    def _match_language_re(self):
        first = True
        for s, flag in self.parse():
            if not flag:
                yield s
            else:
                yield r"(?P<lang>[^/]+)" if first else r"(?P=lang)"
                first = False

    def parse(self):
        indexes = [m.start() for m in re.finditer("<lang>", self.expression)]
        i = j = 0
        while i < len(self.expression):
            if j < len(indexes) and indexes[j] == i:
                yield "lang", True
                i += 6
                j += 1
            else:
                yield self.expression[i], False
                i += 1

    def create_automaton(self, char_set):
        current = start = State()
        for s, flag in self.parse():
            state = State()
            if flag:
                for c in char_set:
                    if c == '/':
                        continue
                    current.add(c, state)
                    state.add(c, state)
                current.add(char_set, state)
                state.add(char_set, state)
            else:
                current.add(s, state)
            current = state
        current.tags.add(self)
        automaton = Automaton()
        automaton.start = start
        automaton.goals.add(current)
        return automaton

    @staticmethod
    def get_char_set(file_filters):
        char_set = set(["/"])
        for file_filter in file_filters:
            for c, flag in file_filter.parse():
                if not flag:
                    char_set.add(c)
        return frozenset(char_set)

    def __repr__(self):
        return self.expression


class Resources:
    def __init__(self, l):
        self.list = list(l)
        char_set = FileFilter.get_char_set(r.file_filter for r in self.list)
        automaton = Automaton.union(*[r.file_filter.create_automaton(char_set) for r in self.list])
        automaton = Automaton.create_dfa(automaton.start, automaton.goals)
        for state in automaton.reachable_states():
            for c, state_set in state.transitions.iteritems():
                if isinstance(c, frozenset):
                    state.exception_transitions[c] = set(state_set)
        self.automaton = automaton

    def walk(self, path):
        for root, dirs, files in os.walk(path, followlinks=True):
            for f in files:
                rel = os.path.relpath(os.path.abspath(os.path.join(root, f)), path)
                success, tags = self.automaton.matches(rel)
                if not success:
                    continue
                file_filter = list(tags)[0]
                lang = file_filter.lang(rel)
                if lang is None:
                    continue
                resource = file_filter.resource
                if lang in resource.trans:
                    continue
                if resource.source_lang == lang:
                    continue
                if rel == resource.source_file:
                    continue
                resource.trans[lang] = rel
