import logging
import os
import unittest
import pprint

from miro import feedparserutil
from miro.item import FeedParserValues
from miro.plat import resources
from miro.test.framework import MiroTestCase

FPTESTINPUT = resources.path("testdata/feedparsertests/feeds")
FPTESTOUTPUT = resources.path("testdata/feedparsertests/output")

def _parse_feed(inputfile):
    """Runs feedparserutil.parse on the inputfile and returns a dict
    of feedparser stuff.

    :param inputfile: the name of the input file in the FPTESTINPUT
        directory.

    :returns: the feedparser dict

    :raises AssertionError: if the feedparser has problems and the
        feedparser dict has 'bozo_exception' in it.
    """
    fn = os.path.join(FPTESTINPUT, inputfile)
    d = feedparserutil.parse(fn)
    assert (not d["bozo"] or "entries" in d), ("Feed didn't parse: %s %s" %
                                               (fn, d["bozo_exception"]))
    return d

class FeedParserDictTest(MiroTestCase):
    def test_equality(self):
        # feedparserdicts are equal if for all keys k, either
        # the two feedparserdicts have the same value, or
        # one of the feedparserdicts doesn't have the key.
        a = feedparserutil.FeedParserDict()
        a["href"] = "hello"
        b = feedparserutil.FeedParserDict()
        b["url"] = "hello"
        c = feedparserutil.FeedParserDict()
        c["href"] = "hi"
        d = feedparserutil.FeedParserDict()
        d["href"] = "hi"
        d["what"] = "hello"
        self.assertEqual(a.equal(a), True)
        self.assertEqual(b.equal(b), True)
        self.assertEqual(c.equal(c), True)
        self.assertEqual(d.equal(d), True)
        self.assertEqual(a.equal(b), True)
        self.assertEqual(b.equal(a), True)

    def test_inequality(self):
        # feedparserdicts are inequal if for some key k, the
        # two feedparserdicts have different values.
        a = feedparserutil.FeedParserDict()
        a["href"] = "hello"
        b = feedparserutil.FeedParserDict()
        b["url"] = "hello"
        c = feedparserutil.FeedParserDict()
        c["href"] = "hi"
        d = feedparserutil.FeedParserDict()
        d["href"] = "hi"
        d["what"] = "hello"
        self.assertEqual(a.equal(c), False)
        self.assertEqual(c.equal(a), False)
        self.assertEqual(b.equal(c), False)
        self.assertEqual(c.equal(b), False)
        self.assertEqual(a.equal(d), False)
        self.assertEqual(d.equal(a), False)

class FeedParserTest(MiroTestCase):
    def test_ooze(self):
        feedparserutil.parse(os.path.join(FPTESTINPUT, "ooze.rss"))

    def test_usvideo(self):
        # test for bug 10653
        d = feedparserutil.parse(os.path.join(FPTESTINPUT, "usvideo.xml"))

        # this should kick up a KeyError and NOT a TypeError
        self.assertRaises(KeyError, lambda: d['url'])

# this creates a separate test method in FeedParserTest for each test
# in the FPTESTINPUT directory.  makes it easier to debug tests that
# go awry, makes it easier to see test progress from the command line
# (lots of little tests rather than one big test), and increases the
# test count appropriately.
def _test_closure(mem):
    def _actual_test(self):
        d = _parse_feed(mem)
        fp = open(os.path.join(FPTESTOUTPUT, "%s.output" % mem), "r")
        output = fp.read()
        fp.close()
        self.assertEquals(pprint.pformat(d), output)
    return _actual_test

for mem in os.listdir(FPTESTINPUT):
    setattr(FeedParserTest, 'test_%s' % mem.replace(".", ""),
            _test_closure(mem))

class FeedParserValuesTest(unittest.TestCase):
    def test_empty(self):
        fpv = FeedParserValues({})
        self.assertEquals(fpv.data["license"], None)
        self.assertEquals(fpv.data["rss_id"], None)
        self.assertEquals(fpv.data["entry_title"], None)
        self.assertEquals(fpv.data["thumbnail_url"], None)
        self.assertEquals(fpv.data["entry_description"], u"")
        self.assertEquals(fpv.data["link"], u"")
        self.assertEquals(fpv.data["payment_link"], u"")
        self.assertEquals(fpv.data["comments_link"], u"")
        self.assertEquals(fpv.data["url"], u"")
        self.assertEquals(fpv.data["enclosure_size"], None)
        self.assertEquals(fpv.data["enclosure_type"], None)
        self.assertEquals(fpv.data["enclosure_format"], None)
        # self.assertEquals(fpv.data["releaseDateObj"], None)

    def test_thumbnail_url(self):

        # this feed is an rss 2.0 feed with feedburner stuff in it.
        # there's a thumbnail for each item:
        # <rss>
        #    <item>
        #        <thumbnail>http:...</thumbnail>

        d = _parse_feed("http___feeds_miroguide_com_miroguide_featured.xml")

        for i, url in (
            (0, u"http://s3.miroguide.com/static/media/thumbnails/200x134/14094.jpeg"),
            (1, u"http://s3.miroguide.com/static/media/thumbnails/200x134/5152.jpeg"),
            (2, u"http://s3.miroguide.com/static/media/thumbnails/200x134/14086.jpeg"),
            (3, u"http://s3.miroguide.com/static/media/thumbnails/200x134/11717.jpeg"),
            (4, u"http://s3.miroguide.com/static/media/thumbnails/200x134/13422.jpeg")):

            fpv = FeedParserValues(d.entries[i])
            self.assertEquals(fpv.data["thumbnail_url"], url)

        d = _parse_feed("http___feeds_miroguide_com_miroguide_new.xml")

        for i, url in (
            (0, u"http://s3.miroguide.com/static/media/thumbnails/200x134/14280.jpeg"),
            (1, u"http://s3.miroguide.com/static/media/thumbnails/200x134/11715.jpeg")):

            fpv = FeedParserValues(d.entries[i])
            self.assertEquals(fpv.data["thumbnail_url"], url)

        # this feed has no thumbnails in the enclosures or in the
        # items.
        d = _parse_feed("http___feeds_feedburner_com_earth-touch_podcast_720p.xml")

        for i, url in (
            (0, None),
            (1, None)):

            fpv = FeedParserValues(d.entries[i])
            self.assertEquals(fpv.data["thumbnail_url"], url)

        # this feed has no thumbnails in the enclosures or in the
        # items.  it's an audio podcast.
        d = _parse_feed("http___feeds_thisamericanlife_org_talpodcast.xml")

        for i, url in (
            (0, None),):

            fpv = FeedParserValues(d.entries[i])
            self.assertEquals(fpv.data["thumbnail_url"], url)

        # thumbnails are in the enclosure
        # <enclosure>
        #    <thumbnail>
        #        <href>http...</href>
        d = _parse_feed("http___vodo_net_feeds_promoted.xml")

        for i, url in (
            (0, u'http://vodo.net/media/thumbnails/work_127_pioneerone_uploaded.jpeg'),
            (1, u'http://vodo.net/assets/thumbnails/snowblindmovie_QM5moDpN.jpeg'),
            (2, u'http://vodo.net/media/thumbnails/work_142_foureyedmonsters_uploaded.jpeg')):

            fpv = FeedParserValues(d.entries[i])
            self.assertEquals(fpv.data["thumbnail_url"], url)

        # thumbnails are on the item
        # <item>
        #    <thumbnail>
        #       <href>http:...</href>
        d = _parse_feed("http___www_linktv_org_rss_hq_globalpulse.xml")

        for i, url in (
            (0, u'http://www.linktv.org/sitecontent/videothumbs/globalpulse20100709.jpg'),
            (1, u'http://www.linktv.org/sitecontent/videothumbs/globalpulse20100625.jpg'),
            (2, u'http://www.linktv.org/sitecontent/videothumbs/globalpulse20100611.jpg')):

            fpv = FeedParserValues(d.entries[i])
            self.assertEquals(fpv.data["thumbnail_url"], url)


# FIXME - could use way more feedparser tests

if __name__ == "__main__":
    unittest.main()
