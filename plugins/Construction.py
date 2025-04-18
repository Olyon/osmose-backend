#-*- coding: utf-8 -*-

###########################################################################
##                                                                       ##
## Copyrights Frédéric Rodrigo 2011-2016                                 ##
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

from modules.OsmoseTranslation import T_
from plugins.Plugin import Plugin
import datetime
import dateutil.parser

class Construction(Plugin):

    def init(self, logger):
        Plugin.init(self, logger)
        if self.father.config.options.get("project") != 'openstreetmap':
            return False
        self.errors[4070] = self.def_class(item = 4070, level = 2, tags = ['tag', 'fix:survey'],
            title = T_('Finished construction'),
            detail = T_(
'''There is no tag `opening_date`, `check_date`, `open_date`,
`construction:date`, `temporary:date_on`, `date_on` and the object has
been in construction for more than two years or opening data is
exceeded.'''))

        # Tags where the value "construction" does not refer to construction work on the object itself
        # Note that only company=construction is documented
        self.tag_not_construction = ["company", "craft", "historic", "industrial", "shop"]

        self.tag_date = ["opening_date", "open_date", "construction:date", "temporary:date_on", "date_on"]
        self.default_date = datetime.datetime(9999, 12, 1)
        self.today = datetime.datetime.today()
        self.date_limit = datetime.timedelta(days=2 * 365)
        self.recall = int(self.total_seconds(datetime.timedelta(days=6 * 30)))

    def getTagDate(self, tags):
        for i in self.tag_date:
            if i in tags:
                return tags[i]

    def convert2date(self, string):
        try:
            date = dateutil.parser.parse(string, default=self.default_date)
            if date.tzinfo and abs(date.tzinfo.utcoffset()) > 1439:
                # Ignore tzinfo if not in valid range
                date.tzinfo = None
            if date.year != 9999:
                return date
        except ValueError:
            pass
        except TypeError:
            # triggered by python-dateutil 2.2, on an incorrect string
            pass

    def node(self, data, tags):
        construction_found = "construction" in tags

        if not construction_found and "operational_status" in tags:
            construction_found = tags.get("operational_status").endswith("construction")
        if not construction_found:
            for t in tags:
                if ((t.startswith("construction:") and t != "construction:date")
                    or (tags.get(t) == "construction" and t not in self.tag_not_construction and ":" not in t)):
                    construction_found = True
                    break

        if not construction_found:
            return

        date = None
        tagDate = self.getTagDate(tags)
        if tagDate:
            date = self.convert2date(tagDate)

        end_date = False
        try:
            if date:
                end_date = date
            elif data["timestamp"] > 0:
                end_date = datetime.datetime.fromtimestamp(data["timestamp"]) + self.date_limit
            else:
                return
        except:
            # This should only trigger in case the pbf reader is updated (and the plugin not), causing the timestamp format to change (or be absent)
            print("Error: Unexpected format of timestamp or no timestamp provided, expected numerical timestamp")
            return

        delta = int(self.total_seconds(self.today - end_date))
        if delta > 0:
            # Change the subclass every 6 months after expiration, re-popup the marker in frontend even if set as false-positive
            return {"class": 4070, "subclass": delta // self.recall}

    def way(self, data, tags, nds):
        return self.node(data, tags)

    def relation(self, data, tags, members):
        return self.node(data, tags)


    def total_seconds(self, td):
        # Note: compared to timedelta.total_seconds(), this function doesn't use microseconds
        return td.seconds + td.days * 24 * 3600

###########################################################################
from plugins.Plugin import TestPluginCommon

class Test(TestPluginCommon):
    def setUp(self):
        TestPluginCommon.setUp(self)
        self.p = Construction(None)
        self.set_default_config(self.p)
        self.p.init(None)

    def test(self):
        # Use today, so it won't trigger due to the timestamp in this test
        ts = datetime.datetime.timestamp(datetime.datetime.today())

        constr_tags = [{"construction": "yes"},
                       {"highway": "construction"},
                       {"landuse": "construction"},
                       {"building": "construction"},
                       {"operational_status": "under_construction"},
                       {"railway": "construction"},
                       {"construction:man_made": "water_works"},
                      ]
        other_tags = [{"highway": "primary"},
                      {"landuse": "farm"},
                      {"building": "yes"},
                      {"company": "construction"},
                      {"construction:date": "2001-01-01"},
                      {"removed:landuse": "construction"},
                     ]

        correct_dates = ["2010-02-03",
                         "January 3rd, 2012",
                         "02/01/1987",
                         "12/21/1993",
                         "22/01/2012",
                        ]
        not_correct_dates = ["22/01/2123",
                             "2142-10-01",
                             "monday",
                             "yes",
                             "2018-11-11--2018-12-31",
                            ]
        for tags in constr_tags:
            for tag_d in self.p.tag_date:
                for val_d in correct_dates:
                    t = tags.copy()
                    t.update({tag_d: val_d})
                    self.check_err(self.p.node({"timestamp": ts}, t), t)
                for val_d in not_correct_dates:
                    t = tags.copy()
                    t.update({tag_d: val_d})
                    assert not self.p.way({"timestamp": ts}, t, None), t

        for tags in other_tags:
            for tag_d in self.p.tag_date:
                for val_d in correct_dates:
                    t = tags.copy()
                    t.update({tag_d: val_d})
                    assert not self.p.relation({"timestamp": ts}, t, None), t

    def test_timestamp(self):
        tags = {"construction": "yes"}
        for ts in ["2003-01-04", "1989-03-10"]:
            ts_int = datetime.datetime.timestamp(datetime.datetime.strptime(ts,"%Y-%m-%d"))
            self.check_err(self.p.node({"timestamp": ts_int}, tags), ts)
        for ts in ["2078-01-04", str(datetime.datetime.today())[0:10]]:
            ts_int = datetime.datetime.timestamp(datetime.datetime.strptime(ts,"%Y-%m-%d"))
            assert not self.p.node({"timestamp": ts_int}, tags), ts
        assert not self.p.node({"timestamp": 0}, tags)

    def test_recall(self):
        tags = {"construction": "yes"}
        today = datetime.datetime.today()
        td = datetime.timedelta(days=6 * 30)
        for i in range(5, 10, 1):
            e = self.p.node({"timestamp": datetime.datetime.timestamp(today - i*td)}, tags)
            self.check_err(e, i)
            assert e["subclass"] == i - 5
