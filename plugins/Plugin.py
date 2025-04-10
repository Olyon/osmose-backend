#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Black Myst <black.myst@free.fr> 2011                       ##
##                                                                       ##
## This program is free software: you can redistribute it and/or modify  ##
## it under the terms of the GNU General Public License as published by  ##
## the Free Software Foundation, either version 3 of the License, or     ##
## (at your option) any later version.                                   ##
##                                                                       ##
## This program is distributed in the hope that it will be useful,       ##
## but WITHOUT ANY WARRANTY; without even the implied warranty of        ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         ##
## GNU General Public License for more details.                          ##
##                                                                       ##
## You should have received a copy of the GNU General Public License     ##
## along with this program.  If not, see <http://www.gnu.org/licenses/>. ##
##                                                                       ##
###########################################################################

from modules.Stablehash import stablehash
from analysers.Analyser import Analyser

import os
from inspect import getframeinfo, stack
from typing import Dict, List, Union


class Plugin(object):

    def __init__(self, father):
        self.father = father

    def init(self, logger):
        """
        Called before starting analyse.
        @param logger:
        """
        self.errors = {}
        pass

    def availableMethodes(self):
        """
        Get a list of overridden methods.
        This is usefull to optimize call from analyser_sax.
        """
        capabilities = []
        currentClass = self.__class__
        if currentClass.node != Plugin.node: capabilities.append("node")
        if currentClass.way != Plugin.way: capabilities.append("way")
        if currentClass.relation != Plugin.relation: capabilities.append("relation")
        return capabilities

    def node(self, node: Dict[str, Union[str, int]], tags: Dict[str, str]):
        """
        Called each time a node is found on data source.

        @param node: dict with details.
            example: node[u"id"], node[u"lat"], node[u"lon"], node[u"version"]
        @param tags: dict with all tags and values.
        @return: error list.
        """
        pass

    def way(self, way: Dict[str, Union[str, int]], tags: Dict[str, str], nodes: List[int]):
        """
        Called each time a way is found on data source.

        @param way: dict with details.
            example: node[u"id"], node[u"lat"], node[u"lon"], node[u"version"]
        @param tags: dict with all tags and values.
        @param nodes: list of all nodes id.
        @return: error list.
        """
        pass

    def relation(self, relation: Dict[str, Union[str, int]], tags: Dict[str, str], members: List[Dict[str, Union[str, int]]]):
        """
        Called each time a relation is found on data source.

        @param relation: dict with details.
            example: node[u"id"], node[u"lat"], node[u"lon"], node[u"version"]
        @param tags: dict with all tags and values.
        @param members:  list of all relation members.
        @return: error list.
        """
        pass

    def end(self, logger):
        """
        Called after starting analyse.
        @param logger:
        """
        pass

    def def_class(self, **kwargs):
        if 'source' not in kwargs and self.father and self.father.config:
            config = self.father.config
            caller = getframeinfo(stack()[1][0])
            kwargs['source'] = '{0}/plugins/{1}#L{2}'.format(config and hasattr(config, 'source_url') and config.source_url or None, os.path.basename(caller.filename), caller.lineno)

        return Analyser.def_class_(self.father and self.father.config or None, **kwargs)


    def merge_doc(self, *docs):
        return Analyser.merge_doc(*docs)


    def ToolsStripAccents(self, mot):
        mot = mot.replace(u"à", u"a").replace(u"â", u"a")
        mot = mot.replace(u"é", u"e").replace(u"è", u"e").replace(u"ë", u"e").replace(u"ê", u"e")
        mot = mot.replace(u"î", u"i").replace(u"ï", u"i")
        mot = mot.replace(u"ô", u"o").replace(u"ö", u"o")
        mot = mot.replace(u"û", u"u").replace(u"ü", u"u").replace(u"ù", u"u")
        mot = mot.replace(u"ÿ", u"y")
        mot = mot.replace(u"ç", u"c")
        mot = mot.replace(U"À", U"A").replace(u"Â", u"A")
        mot = mot.replace(U"É", U"E").replace(U"È", U"E").replace(U"Ë", U"E").replace(U"Ê", U"E")
        mot = mot.replace(U"Î", U"I").replace(U"Ï", U"I")
        mot = mot.replace(U"Ô", U"O").replace(U"Ö", U"O")
        mot = mot.replace(U"Û", U"U").replace(U"Ü", U"U").replace(u"Ù", u"U")
        mot = mot.replace(U"Ÿ", U"Y")
        mot = mot.replace(U"Ç", U"C")
        mot = mot.replace(U"œ", U"oe")
        mot = mot.replace(U"æ", U"ae")
        mot = mot.replace(U"Œ", U"OE")
        mot = mot.replace(U"Æ", U"AE")
        return mot


class with_options:
    def __init__(self, plugin, options):
        self.plugin = plugin
        self.options = options

    def __enter__(self):
        self.old_options = self.plugin.father.config.options
        self.plugin.father.config.options = self.plugin.father.config.options.copy()
        self.plugin.father.config.options.update(self.options)

    def __exit__(self, type, value, traceback):
        self.plugin.father.config.options = self.old_options


###########################################################################
import unittest

class TestPluginCommon(unittest.TestCase):
    def setUp(self):
        # import for gettext functions
        import analysers.Analyser
        assert analysers.Analyser  # silence pyflakes

    def set_default_config(self, plugin):
        class _config:
            options = {"project": "openstreetmap"}
        class father:
            config = _config()
        plugin.father = father()

    # Check errors generation, and unicode encoding
    def check_err(self, errors, log="Valid errors expected", expected=None):
        if isinstance(errors, dict):
            errors = [errors]
        assert errors, log
        for error in errors:
            assert "class" in error, error
            assert isinstance(error["class"], int), error["class"]
            if "subclass" in error:
                assert isinstance(error["subclass"], int), error["subclass"]
            if "text" in error:
                self.check_dict(error["text"], log)
            if "fix" in error:
                # TODO: check fix format
                self.check_array([error["fix"]], log)
            for k in error.keys():
                if k not in ("class", "subclass", "text", "fix", "allow_fix_override"):
                    assert False, "key '{0}' is not accepted in error: {1}".format(k, error)

        if expected:
            found = False
            for e in errors:
                for exk, exv in expected.items():
                    if not exk in e or e[exk] != exv:
                        e = None
                        break
                if e:
                    # Found a match
                    found = e
                    break
            assert found, str(expected) + " Not found in the errors list" + str(errors)

        # Check if errors are also unique
        errors_hashableitems = list(map(lambda e: str(e["class"]) + "|" + str(e.get("subclass", "")), errors))
        non_unique = set([x for x in errors_hashableitems if errors_hashableitems.count(x) > 1])
        assert len(non_unique) == 0, "Duplicate entry with class|subclass:\n - " + '\n - '.join(non_unique)

    def check_not_err(self, errors, log="Error not expected", expected=None):
        if not errors:
            return
        if isinstance(errors, dict):
            errors = [errors]
        assert log

        if expected:
            found = False
            for e in errors:
                for exk, exv in expected.items():
                    if not exk in e or e[exk] != exv:
                        e = None
                        break
                if e:
                    # Found a match
                    found = e
                    break
            assert not found, str(found) + " Found in the errors list"

    def check_dict(self, d, log):
        for (k,v) in d.items():
            if isinstance(v, list):
                self.check_array(v, log)
            elif isinstance(v, dict):
                self.check_dict(v, log)

    def check_array(self, a, log):
        for v in a:
            if isinstance(v, list):
                self.check_array(v, log)
            elif isinstance(v, dict):
                self.check_dict(v, log)


class Test(TestPluginCommon):

    def test(self):
        a = Plugin(None)
        self.assertEqual(a.init(None), None)
        self.assertEqual(a.errors, {})
        self.assertEqual(a.node(None, None), None)
        self.assertEqual(a.way(None, None, None), None)
        self.assertEqual(a.relation(None, None, None), None)
        self.assertEqual(a.end(None), None)
        for n in [(u"bpoue", u"bpoue"),
                  (u"bpoué", u"bpoue"),
                  (u"bpoùé", u"bpoue"),
                  (u"bpôùé", u"bpoue"),
                 ]:
            self.assertEqual(a.ToolsStripAccents(n[0]), n[1], n)

        for n in [(u"1", u"beppu"),
                  (u"1", u"lhnsune"),
                  (u"1", u"uae"),
                  (u"1", u"bue"),
                 ]:
            self.assertNotEqual(stablehash(n[0]), stablehash(n[1]))

    def test_check_err(self):
        import pytest
        self.assertEqual(self.check_err([{"class": 1, "subclass": 2}]), None)
        self.assertEqual(self.check_err([{"class": 1, "subclass": 2, "text": {"en": "titi"}}]), None)
        self.assertEqual(self.check_err([{"class": 1, "subclass": 2, "fix": {"name": "toto"}}]), None)
        self.assertEqual(self.check_err([{"class": 1, "subclass": 2, "fix": {"+": {"name": "toto"}}}]), None)

        with pytest.raises(Exception):
            self.check_err([{"unknown": "x"}])
        with pytest.raises(Exception):
            self.check_err([{"class": "a", "subclass": 2}])
        with pytest.raises(Exception):
            self.check_err([{"class": 1, "subclass": "b"}])
        with pytest.raises(Exception):
            self.check_err([{"class": 1, "subclass": 2, "text": "toto"}])

        with pytest.raises(Exception):
            self.check_err(["unknown"])

    def test_check_dict(self):
        self.assertEqual(self.check_dict({"a": "toto"}, None), None)
        self.assertEqual(self.check_dict({"a": ["toto"]}, None), None)
        self.assertEqual(self.check_dict({"a": ["toto", "titi"]}, None), None)
        self.assertEqual(self.check_dict({"a": ["toto", {"a": "titi"}]}, None), None)

    def test_check_array(self):
        self.assertEqual(self.check_array("toto", None), None)
        self.assertEqual(self.check_array(["toto"], None), None)
        self.assertEqual(self.check_array(["toto", "titi"], None), None)
        self.assertEqual(self.check_array(["toto", {"a": "titi"}], None), None)
        self.assertEqual(self.check_array(["toto", ["a", "titi"]], None), None)

    def test_availableMethodes(self):
        class Plugin_with_node(Plugin):
            def node(self, node, tags):
                pass # pragma: no cover
        a = Plugin_with_node(None)
        self.assertEqual(a.availableMethodes(), ["node"])

        class Plugin_with_way(Plugin):
            def way(self, node, tags, nodes):
                pass # pragma: no cover
        a = Plugin_with_way(None)
        self.assertEqual(a.availableMethodes(), ["way"])

        class Plugin_with_relation(Plugin):
            def relation(self, relation, tags, members):
                pass # pragma: no cover
        a = Plugin_with_relation(None)
        self.assertEqual(a.availableMethodes(), ["relation"])

        class Plugin_with_all(Plugin_with_node, Plugin_with_way, Plugin_with_relation):
            pass
        a = Plugin_with_all(None)
        self.assertEqual(a.availableMethodes(), ["node", "way", "relation"])
