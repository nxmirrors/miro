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

"""Controller for Feeds."""

import logging

from miro import app
from miro.gtcache import gettext as _
from miro.gtcache import ngettext
from miro import messages
from miro.frontends.widgets import feedsettingspanel
from miro.frontends.widgets import removefeeds
from miro.frontends.widgets import itemcontextmenu
from miro.frontends.widgets import itemlist
from miro.frontends.widgets import itemlistcontroller
from miro.frontends.widgets import itemlistwidgets
from miro.frontends.widgets import separator
from miro.frontends.widgets import imagepool
from miro.frontends.widgets import widgetconst
from miro.frontends.widgets import widgetutil
from miro.plat.frontends.widgets import widgetset
from miro.plat import resources

class FeedController(itemlistcontroller.ItemListController):
    """Controller object for feeds."""

    def __init__(self, id, is_folder, is_directory_feed):
        self.is_folder = is_folder
        self.is_directory_feed = is_directory_feed
        self._show_more_count = 0
        itemlistcontroller.ItemListController.__init__(self, u'feed', id)

    def build_list_item_view(self):
        return itemlistwidgets.ListItemView(self.item_list, self.columns)

    def make_context_menu_handler(self):
        return itemcontextmenu.ItemContextMenuHandler()

    def build_widget(self):
        feed_info = widgetutil.get_feed_info(self.id)
        icon = imagepool.get(feed_info.thumbnail, size=(41, 41))
        self._make_item_views()

        add_icon_box = not self.is_folder and not feed_info.thumbnail.startswith(resources.root())
        if feed_info.is_directory_feed:
            self.titlebar = itemlistwidgets.ItemListTitlebar(feed_info.name, icon,
                    add_icon_box=add_icon_box)
        else:
            self.titlebar = itemlistwidgets.ChannelTitlebar(feed_info.name, icon,
                    add_icon_box=add_icon_box)
            self.titlebar.connect('save-search', self._on_save_search)
        self.titlebar.connect('search-changed', self._on_search_changed)
        self.widget.titlebar_vbox.pack_start(self.titlebar)
        if not self.is_folder:
            sep = separator.HSeparator((0.85, 0.85, 0.85), (0.95, 0.95, 0.95))
            self.widget.titlebar_vbox.pack_start(sep)
            self.widget.titlebar_vbox.pack_start(self._make_toolbar(feed_info))

        vbox = widgetset.VBox()
        vbox.pack_start(self.downloading_section)
        vbox.pack_start(self.full_section)
        vbox.pack_start(self.downloaded_section)

        background = widgetset.SolidBackground((1, 1, 1))
        background.add(vbox)

        scroller = widgetset.Scroller(False, True)
        scroller.add(background)

        self.widget.normal_view_vbox.pack_start(scroller, expand=True)

    def _show_all(self):
        self._show_more_count = 0
        self.full_view.item_list.set_new_only(False)
        self.full_view.model_changed()
        self.show_more_container.hide()

    def _on_show_more(self, button):
        self._show_all()

    def _on_search_changed(self, widget, search_text):
        if self.full_view.item_list.new_only:
            self._show_all()
        self.set_search(search_text)
        self._update_counts()

    def _on_save_search(self, widget, search_text):
        info = widgetutil.get_feed_info(self.id)
        messages.NewFeedSearchFeed(info, search_text).send_to_backend()

    def _make_item_views(self):
        self.downloading_view = itemlistwidgets.ItemView(
                itemlist.DownloadingItemList(), self.is_folder)
        self.downloaded_view = itemlistwidgets.ItemView(
                itemlist.DownloadedItemList(), self.is_folder)
        self.full_view = itemlistwidgets.ItemView(itemlist.ItemList(), self.is_folder)
        self.downloading_section = itemlistwidgets.HideableSection(
                "", self.downloading_view)
        self.downloaded_section = itemlistwidgets.HideableSection(
                _("Downloaded"), self.downloaded_view)

        self.show_more_button = widgetset.Button('')
        self.show_more_button.connect('clicked', self._on_show_more)
        self.show_more_container = widgetutil.HideableWidget(
                widgetutil.align_left(self.show_more_button, 2, 2, 10, 0))
        full_section_vbox = widgetset.VBox(spacing=2)
        full_section_vbox.pack_start(self.full_view, expand=True)
        full_section_vbox.pack_start(self.show_more_container)
        self.full_section = itemlistwidgets.HideableSection(
                _("Full Feed"), full_section_vbox)

    def _make_toolbar(self, feed_info):
        toolbar = itemlistwidgets.FeedToolbar()
        if self.is_directory_feed:
            toolbar.autodownload_label.hide()
            toolbar.autodownload_menu.hide()
            toolbar.share_button.hide()
            toolbar.settings_button.hide()
        else:
            toolbar.autodownload_label.show()
            toolbar.autodownload_menu.show()
            toolbar.share_button.show()
            toolbar.settings_button.show()
            toolbar.set_autodownload_mode(feed_info.autodownload_mode)
        toolbar.connect('show-settings', self._on_show_settings)
        toolbar.connect('remove-feed', self._on_remove_feed)
        toolbar.connect('share', self._on_share)
        toolbar.connect('auto-download-changed',
                self._on_auto_download_changed)
        return toolbar

    def normal_item_views(self):
        return [self.downloading_view, self.full_view, self.downloaded_view]

    def default_item_view(self):
        return self.downloaded_view

    def _on_remove_feed(self, widget):
        info = widgetutil.get_feed_info(self.id)
        app.widgetapp.remove_feeds([info])

    def _on_show_settings(self, widget):
        info = widgetutil.get_feed_info(self.id)
        feedsettingspanel.run_dialog(info)

    def _on_share(self, widget):
        app.widgetapp.share_feed()

    def _on_auto_download_changed(self, widget, setting):
        messages.AutodownloadChange(self.id, setting).send_to_backend()

    def _expand_lists_initially(self):
        item_downloaded = self.downloaded_view.item_list.get_count() > 0
        feed_info = widgetutil.get_feed_info(self.id)
        autodownload_mode = feed_info.autodownload_mode
        self.downloaded_section.expand()
        self.full_section.show()
        all_items = self.full_view.item_list.get_items()
        viewed_items = [item for item in all_items \
                if item.downloaded or item.item_viewed]
        if not (item_downloaded and len(all_items) == len(viewed_items)):
            self.full_section.expand()
        if item_downloaded and 0 < len(viewed_items) < len(all_items):
            text = ngettext('Show %(count)d More Item',
                            'Show %(count)d More Items',
                            len(viewed_items),
                            {"count": len(viewed_items)})
            self.show_more_button.set_text(text + u" >>")
            self.show_more_button.set_size(widgetconst.SIZE_SMALL)
            self.show_more_container.show()
            self.full_view.item_list.set_new_only(True)
            self.full_view.model_changed()
            self._show_more_count = len(viewed_items)
        else:
            self._show_more_count = 0

    def on_initial_list(self):
        # We wait for the initial list of items to pack our item views because
        # we need to know which ones should be expanded
        self._expand_lists_initially()
        self._update_counts()

    def on_items_changed(self):
        self._update_counts()

    def _update_counts(self):
        downloads = self.downloading_view.item_list.get_count()
        watchable = self.downloaded_view.item_list.get_count()
        full_count = (self.full_view.item_list.get_count() +
                self._show_more_count)
        info = widgetutil.get_feed_info(self.id)
        if info.autodownload_mode == 'off' or info.unwatched < info.max_new:
            # don't count videos queued for other reasons
            autoqueued_count = 0
        else:
            autoqueued_count = len([i for i in
                                    self.full_view.item_list.get_items()
                                    if i.pending_auto_dl])
        self._update_downloading_section(downloads)
        self._update_downloaded_section(watchable)
        self._update_full_section(downloads, full_count, autoqueued_count)

    def _update_downloading_section(self, downloads):
        if downloads > 0:
            text = ngettext("%(count)d Downloading",
                            "%(count)d Downloading",
                            downloads,
                            {"count": downloads})
            self.downloading_section.set_header(text)
            self.downloading_section.show()
        else:
            self.downloading_section.hide()

    def _update_downloaded_section(self, watchable):
        if watchable > 0:
            text = ngettext("%(count)d Item",
                            "%(count)d Items",
                            watchable,
                            {"count": watchable})
            text = u"|  %s  " % text
            self.downloaded_section.set_info(text)
            self.downloaded_section.show()
        else:
            self.downloaded_section.hide()

    def _update_full_section(self, downloads, items, autoqueued_count):
        if self._search_text == '':
            itemtext = ngettext("%(count)d Item",
                                "%(count)d Items",
                                items,
                                {"count": items})
            downloadingtext = ngettext("%(count)d Downloading",
                                       "%(count)d Downloading",
                                       downloads,
                                       {"count": downloads})
            if autoqueued_count:
                queuedtext = ngettext("%(count)d Download Queued Due To Unplayed Items (See Settings)",
                                      "%(count)d Downloads Queued Due To Unplayed Items (See Settings)",
                                      autoqueued_count,
                                      {"count": autoqueued_count})

            text = u"|  %s" % itemtext
            if downloads:
                text = text + u"  |  %s" % downloadingtext
            if autoqueued_count:
                text = text + u"  |  %s" % queuedtext
        else:
            text = ngettext("%(count)d Item Matches Search",
                    "%(count)d Items Match Search",
                    items, {"count": items})
            text = u"|  %s" % text
        self.full_section.set_info(text)
