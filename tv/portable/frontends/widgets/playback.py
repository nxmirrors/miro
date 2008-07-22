# Miro - an RSS based video player application
# Copyright (C) 2005-2008 Participatory Culture Foundation
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

from miro import app
from miro import signals
from miro import eventloop
from miro.frontends.widgets.displays import VideoDisplay
#from miro.frontends.widgets.displays import AudioDisplay
#from miro.frontends.widgets.displays import ExternalVideoDisplay

class PlaybackManager (signals.SignalEmitter):
    
    def __init__(self):
        signals.SignalEmitter.__init__(self)
        self.previous_left_width = 0
        self.previous_display = None
        self.video_display = None
        self.is_playing = False
        self.is_paused = False
        self.create_signal('will-play')
        self.create_signal('will-pause')
        self.create_signal('will-stop')
        self.create_signal('did-stop')
        self.create_signal('playback-did-progress')
    
    def play_pause(self):
        if not self.is_playing or self.is_paused:
            self.play()
        else:
            self.pause()
    
    def start_with_movie_file(self, path):
        self.video_display = VideoDisplay()
        self.previous_display = app.display_manager.current_display
        self.previous_left_width = app.widgetapp.window.splitter.get_left_width()
        app.widgetapp.window.splitter.set_left_width(0)
        app.display_manager.select_display(self.video_display)
        app.menu_manager.handle_playing_selection()
        self.video_display.setup(path)
    
    def schedule_update(self):
        def notify_and_reschedule():
            if self.is_playing and not self.is_paused:
                self.notify_update()
                self.schedule_update()
        eventloop.addTimeout(0.5, notify_and_reschedule, "Notifying playback progress")

    def notify_update(self):
        if self.video_display is not None:
            elapsed = self.video_display.get_elapsed_playback_time()
            total = self.video_display.get_total_playback_time()
            self.emit('playback-did-progress', elapsed, total)
    
    def play(self):
        duration = self.video_display.get_total_playback_time()
        self.emit('will-play', duration)
        self.video_display.play()
        self.notify_update()
        self.schedule_update()
        self.is_playing = True
        self.is_paused = False

    def pause(self):
        if self.is_playing:
            self.emit('will-pause')
            self.video_display.pause()
            self.is_paused = True

    def stop(self):
        self.emit('will-stop')
        self.video_display.stop()
        app.display_manager.select_display(self.previous_display)
        app.widgetapp.window.splitter.set_left_width(self.previous_left_width)
        self.previous_display = None
        self.video_display = None
        self.is_playing = False
        self.is_paused = False
        self.emit('did-stop')

    def suspend(self):
        if self.is_playing and not self.is_paused:
            self.video_display.pause()
    
    def resume(self):
        if self.is_playing and not self.is_paused:
            self.video_display.play()

    def seek_to(self, progress):
        self.video_display.seek_to(progress)
        self.notify_update()