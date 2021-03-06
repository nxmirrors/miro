# Miro - an RSS based video player application
# Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011
# Participatory Culture Foundation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#
# In addition, as a special exception, the copyright holders give
# permission to link the code of portions of this program with the OpenSSL
# library.
#
# You must obey the GNU General Public License in all respects for all of
# the code used other than OpenSSL. If you modify file(s) with this
# exception, you may extend this exception to your version of the file(s),
# but you are not obligated to do so. If you do not wish to do so, delete
# this exception statement from your version. If you delete this exception
# statement from all source files in the program, then also delete it here.

"""miro.frontends.widgets.newsearchfeed -- Holds dialog and processing
code for the New Search Feed dialog.
"""

from miro.gtcache import gettext as _
from miro import searchengines

from miro.plat.frontends.widgets import widgetset
from miro.frontends.widgets import widgetutil
from miro.frontends.widgets.dialogs import MainDialog
from miro.dialogs import BUTTON_CANCEL, BUTTON_CREATE_FEED
from miro import util

from miro import app

import logging

def run_dialog():
    """Creates and launches the New Search Feed dialog.  This dialog waits
    for the user to press "Create Feed" or "Cancel".

    In the case of "Create Feed", returns a tuple of:

    * ("feed", ChannelInfo, search_term str, section str)
    * ("search_engine", SearchEngineInfo, search_term str, section str)
    * ("url", url str, search_term str, section str)

    In the case of "Cancel", returns None.
    """
    title = _('New Search Feed')
    description = _('A search feed contains items that match a search term.')

    channels = app.tab_list_manager.feed_list.get_feeds()
    channels += app.tab_list_manager.audio_feed_list.get_feeds()
    channels = [ci for ci in channels if not ci.is_folder]
    channels.sort(key=lambda x: util.name_sort_key(x.name))

    window = MainDialog(title, description)
    try:
        try:
            window.add_button(BUTTON_CREATE_FEED.text)
            window.add_button(BUTTON_CANCEL.text)

            extra = widgetset.VBox()

            hb1 = widgetset.HBox()
            hb1.pack_start(widgetset.Label(_('Search for:')), padding=5)
            searchterm = widgetset.TextEntry()
            searchterm.set_activates_default(True)
            hb1.pack_start(searchterm, expand=True)
            extra.pack_start(hb1)

            hb2 = widgetset.HBox()
            hb2.pack_start(widgetutil.align_top(widgetset.Label(_('In this:')), top_pad=3), padding=5)

            choice_table = widgetset.Table(columns=2, rows=3)
            choice_table.set_column_spacing(5)
            choice_table.set_row_spacing(5)
            rbg = widgetset.RadioButtonGroup()

            channel_rb = widgetset.RadioButton(_("Feed:"), rbg)
            channel_option = widgetset.OptionMenu(
                [ci.name + u" - " + ci.url for ci in channels])
            channel_option.set_size_request(250, -1)
            choice_table.pack(channel_rb, 0, 0)
            choice_table.pack(channel_option, 1, 0)

            search_engine_rb = widgetset.RadioButton(_("Search engine:"), rbg)
            search_engines = searchengines.get_search_engines()
            search_engine_option = widgetset.OptionMenu([se.title for se in search_engines])
            choice_table.pack(search_engine_rb, 0, 1)
            choice_table.pack(search_engine_option, 1, 1)

            url_rb = widgetset.RadioButton(_("URL:"), rbg)
            url_text = widgetset.TextEntry()
            choice_table.pack(url_rb, 0, 2)
            choice_table.pack(url_text, 1, 2)

            hb2.pack_start(choice_table, expand=True)

            # only the channel row is enabled
            choice_table.disable(row=1, column=1)
            choice_table.disable(row=2, column=1)

            def handle_clicked(widget):
                # this enables and disables the fields in the table
                # based on which radio button is selected
                if widget is channel_rb:
                    choice_table.enable(row=0, column=1)
                    choice_table.disable(row=1, column=1)
                    choice_table.disable(row=2, column=1)
                elif widget is search_engine_rb:
                    choice_table.disable(row=0, column=1)
                    choice_table.enable(row=1, column=1)
                    choice_table.disable(row=2, column=1)
                else:
                    choice_table.disable(row=0, column=1)
                    choice_table.disable(row=1, column=1)
                    choice_table.enable(row=2, column=1)

            channel_rb.connect('clicked', handle_clicked)
            search_engine_rb.connect('clicked', handle_clicked)
            url_rb.connect('clicked', handle_clicked)

            extra.pack_start(widgetutil.align_top(hb2, top_pad=6))

            hb3 = widgetset.HBox()
            hb3.pack_start(widgetutil.align_top(widgetset.Label(_('Add new feed to this section:')), top_pad=3), padding=5)

            rbg_section = widgetset.RadioButtonGroup()
            video_rb = widgetset.RadioButton(_("video"), rbg_section)
            audio_rb = widgetset.RadioButton(_("audio"), rbg_section)
            hb3.pack_start(video_rb)
            hb3.pack_start(audio_rb)
            extra.pack_start(widgetutil.align_top(hb3, top_pad=6))

            window.set_extra_widget(extra)
            response = window.run()

            if response == 0 and searchterm.get_text():
                term = searchterm.get_text()
                selected_option = rbg.get_selected()
                if rbg_section.get_selected() == video_rb:
                    section = u"video"
                else:
                    section = u"audio"
                if selected_option is channel_rb:
                    return ("feed",
                            channels[channel_option.get_selected()],
                            term,
                            section)
                elif selected_option is search_engine_rb:
                    return ("search_engine",
                            search_engines[search_engine_option.get_selected()],
                            term,
                            section)
                else:
                    return ("url",
                            url_text.get_text(),
                            term,
                            section)
        except StandardError:
            logging.exception("newsearchfeed threw exception.")
    finally:
        window.destroy()
