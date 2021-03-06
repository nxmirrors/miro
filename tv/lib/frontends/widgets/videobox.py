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

"""Contains the videobox (the widget on the bottom of the right side with
video controls).
"""

from miro import app
from miro import displaytext
from miro.frontends.widgets import style
from miro.frontends.widgets import imagepool
from miro.frontends.widgets import widgetutil
from miro.frontends.widgets import imagebutton
from miro.frontends.widgets.widgetconst import MAX_VOLUME
from miro.plat.frontends.widgets import widgetset
from miro.plat import resources

class PlaybackControls(widgetset.HBox):
    def __init__(self):
        widgetset.HBox.__init__(self, spacing=2)
        self.previous = self.make_button('skip_previous', True)
        self.stop = self.make_button('stop', False)
        self.play = self.make_button('play', False)
        self.forward = self.make_button('skip_forward', True)
        self.fullscreen = self.make_button('play_fullscreen', True)
        self.pack_start(widgetutil.align_middle(self.previous))
        self.pack_start(widgetutil.align_middle(self.stop))
        self.pack_start(widgetutil.align_middle(self.play))
        self.pack_start(widgetutil.align_middle(self.fullscreen))
        self.pack_start(widgetutil.align_middle(self.forward))
        app.playback_manager.connect('selecting-file', self.handle_selecting)
        app.playback_manager.connect('will-play', self.handle_play)
        app.playback_manager.connect('will-pause', self.handle_pause)
        app.playback_manager.connect('will-stop', self.handle_stop)

    def make_button(self, name, continous):
        if continous:
            button = imagebutton.ContinuousImageButton(name)
            button.set_delays(0.6, 0.3)
        else:
            button = imagebutton.ImageButton(name)
        button.disable()
        return button
    
    def handle_new_selection(self, has_playable):
        if app.playback_manager.is_playing:
            self.play.enable()
        else:
            self.play.set_disabled(not has_playable)

    def handle_selecting(self, obj, item_info):
        self.previous.enable()
        self.stop.enable()
        self.play.disable()
        self.play.set_image('pause')
        self.forward.enable()
        if item_info.file_type == 'video':
            self.fullscreen.enable()
        self.queue_redraw()
    
    def handle_play(self, obj, duration):
        self.previous.enable()
        self.stop.enable()
        self.play.set_image('pause')
        self.play.enable()
        self.forward.enable()
        if not obj.is_playing_audio:
            self.fullscreen.enable()
        self.queue_redraw()

    def handle_pause(self, obj):
        self.play.set_image('play')
        self.play.queue_redraw()

    def handle_stop(self, obj):
        self.handle_pause(obj)
        self.previous.disable()
        self.stop.disable()
        self.play.disable()
        self.forward.disable()
        self.fullscreen.disable()
        self.queue_redraw()

class PlaybackInfo(widgetset.DrawingArea):
    LEFT_MARGIN = 8
    RIGHT_MARGIN = 8
    TOTAL_MARGIN = LEFT_MARGIN + RIGHT_MARGIN
    
    def __init__(self):
        widgetset.DrawingArea.__init__(self)
        self.video_icon = imagepool.get_surface(resources.path('images/mini-icon-video.png'))
        self.audio_icon = imagepool.get_surface(resources.path('images/mini-icon-audio.png'))
        self.reset()
        app.playback_manager.connect('selecting-file', self.handle_selecting)
        app.playback_manager.connect('will-play', self.handle_play)
        app.playback_manager.connect('will-stop', self.handle_stop)

    def handle_selecting(self, obj, item_info):
        self.item_name = item_info.name
        self.feed_name = item_info.feed_name
        self.is_audio = (item_info.file_type == 'audio')

    def handle_play(self, obj, duration):
        self.queue_redraw()

    def handle_stop(self, obj):
        self.reset()
        self.queue_redraw()
    
    def reset(self):
        self.item_name = ""
        self.feed_name = ""
        self.is_audio = False
    
    def get_full_text(self):
        if self.feed_name is None:
            return self.item_name
        return "%s - %s" % (self.item_name, self.feed_name)
    
    def size_request(self, layout):
        layout.set_font(0.8)
        sizer_text = layout.textbox(self.get_full_text())
        width, height = sizer_text.get_size()
        if self.is_audio:
            width = width + 20
        return width, height

    def draw(self, context, layout):
        if not app.playback_manager.is_playing:
            return

        width, height = self.size_request(layout)
        x = int((context.width - width - self.TOTAL_MARGIN) / 2.0)
        if x < self.LEFT_MARGIN:
            width = context.width - self.TOTAL_MARGIN + x
            x = self.LEFT_MARGIN

        if self.is_audio:        
            self.audio_icon.draw(context, x, 0, 15, 12, 1.0)
            x = x + 20

        layout.set_text_color((0.9, 0.9, 0.9))
        text = layout.textbox(self.item_name)
        width1, height1 = text.get_size()
        width1 = min(width1, context.width - self.TOTAL_MARGIN - x)
        text.set_wrap_style('truncated-char')
        text.set_width(width1)
        text.draw(context, x, 0, width1, height1)

        if self.feed_name is not None:
            layout.set_text_color((0.7, 0.7, 0.7))
            text = layout.textbox(" - %s" % self.feed_name)
            width2, height2 = text.get_size()
            width2 = min(width2, context.width - self.TOTAL_MARGIN - width1 - x)
            text.set_wrap_style('truncated-char')
            text.set_width(width2)
            text.draw(context, x + width1, 0, width2, height2)

class ProgressTime(widgetset.DrawingArea):
    def __init__(self):
        widgetset.DrawingArea.__init__(self)
        self.current_time = None
        app.playback_manager.connect('playback-did-progress', self.handle_progress)
        app.playback_manager.connect('selecting-file', self.handle_selecting)
        app.playback_manager.connect('will-stop', self.handle_stop)

    def size_request(self, layout):
        layout.set_font(0.75)
        sizer_text = layout.textbox('9999:99')
        return sizer_text.get_size()

    def handle_progress(self, obj, elapsed, total):
        self.set_current_time(elapsed)
        
    def handle_stop(self, obj):
        self.set_current_time(None)

    def handle_selecting(self, obj, item_info):
        self.set_current_time(None)
    
    def set_current_time(self, current_time):
        self.current_time = current_time
        self.queue_redraw()

    def draw(self, context, layout):
        if not app.playback_manager.is_playing:
            return
        if self.current_time is not None:
            layout.set_font(0.75)
            layout.set_text_color(widgetutil.WHITE)
            text = layout.textbox(displaytext.short_time_string(self.current_time))
            width, height = text.get_size()
            text.draw(context, context.width-width, 0, width, height)

class ProgressTimeRemaining(widgetset.CustomButton):
    def __init__(self):
        widgetset.CustomButton.__init__(self)
        self.duration = self.current_time = None
        self.display_remaining = True
        app.playback_manager.connect('selecting-file', self.handle_selecting)
        app.playback_manager.connect('will-play', self.handle_play)
        app.playback_manager.connect('playback-did-progress', self.handle_progress)
        app.playback_manager.connect('will-stop', self.handle_stop)

    def size_request(self, layout):
        layout.set_font(0.75)
        sizer_text = layout.textbox('-9999:99')
        return sizer_text.get_size()

    def handle_play(self, obj, duration):
        self.set_duration(duration)

    def handle_selecting(self, obj, item_info):
        self.set_current_time(None)

    def handle_progress(self, obj, elapsed, total):
        self.set_current_time(elapsed)
        self.set_duration(total)

    def handle_stop(self, obj):
        self.set_current_time(None)

    def set_current_time(self, current_time):
        self.current_time = current_time
        self.queue_redraw()

    def set_duration(self, duration):
        self.duration = duration
        self.queue_redraw()

    def toggle_display(self):
        self.display_remaining = not self.display_remaining
        self.queue_redraw()

    def draw(self, context, layout):
        # Maybe we should have different style when self.state == 'pressed'
        # for user feed back?
        if not app.playback_manager.is_playing:
            return
        if self.current_time is None or self.duration is None:
            return
        elif self.display_remaining:
            text = '-' + displaytext.short_time_string(self.duration - self.current_time)
        else:
            text = displaytext.short_time_string(self.duration)
        layout.set_font(0.75)
        layout.set_text_color(widgetutil.WHITE)
        text = layout.textbox(text)
        width, height = text.get_size()
        text.draw(context, 10, 0, width, height)

class ProgressSlider(widgetset.CustomSlider):
    def __init__(self):
        widgetset.CustomSlider.__init__(self)
        self.background_surface = widgetutil.ThreeImageSurface('playback_track')
        self.progress_surface = widgetutil.ThreeImageSurface('playback_track_progress')
        self.progress_cursor = widgetutil.make_surface('playback_cursor')
        app.playback_manager.connect('playback-did-progress', self.handle_progress)
        app.playback_manager.connect('selecting-file', self.handle_selecting)
        app.playback_manager.connect('will-play', self.handle_play)
        app.playback_manager.connect('will-stop', self.handle_stop)
        self.disable()
        self.duration = 0

    def handle_progress(self, obj, elapsed, total):
        if elapsed is None or total is None:
            self.set_value(0)
        elif total > 0:
            self.set_value(float(elapsed)/total)
        else:
            self.set_value(0)

    def handle_play(self, obj, duration):
        self.duration = duration
        self.enable()

    def handle_selecting(self, obj, item_info):
        self.disable()

    def handle_stop(self, obj):
        self.duration = 0
        self.set_value(0)
        self.disable()

    def is_horizontal(self):
        return True

    def is_continuous(self):
        return False

    def size_request(self, layout):
        return (60, 11)

    def slider_size(self):
        return 1

    def draw(self, context, layout):
        if not app.playback_manager.is_playing:
            return
        min, max = self.get_range()
        progress_width = int(round(self.get_value() / max * context.width))
        self.progress_surface.draw(context, 0, 0, progress_width)
        if progress_width == 0:
            self.background_surface.draw(context, 0, 0, context.width)
        else:
            self.background_surface.draw_right(context, progress_width, 0, context.width - progress_width)
        if self.duration > 0:
            if progress_width <= 3:
                self.progress_cursor.draw(context, 0, 0, self.progress_cursor.width, self.progress_cursor.height)
            else:
                self.progress_cursor.draw(context, progress_width-3, 0, self.progress_cursor.width, self.progress_cursor.height)

class ProgressTimeline(widgetset.Background):
    def __init__(self):
        widgetset.Background.__init__(self)
        self.duration = self.current_time = None
        self.info = PlaybackInfo()
        self.slider = ProgressSlider()
        self.slider.set_range(0, 1)
        self.time = ProgressTime()
        self.slider.connect('pressed', self.on_slider_pressed)
        self.slider.connect('moved', self.on_slider_moved)
        self.slider.connect('released', self.on_slider_released)
        self.remaining_time = ProgressTimeRemaining()
        self.remaining_time.connect('clicked', self.on_remaining_clicked)
        vbox = widgetset.VBox()
        vbox.pack_start(widgetutil.align_middle(self.info, top_pad=6))
        slider_box = widgetset.HBox()
        slider_box.pack_start(widgetutil.align_middle(self.time), expand=False, padding=5)
        slider_box.pack_start(widgetutil.align_middle(self.slider), expand=True)
        slider_box.pack_start(widgetutil.align_middle(self.remaining_time, left_pad=20, right_pad=5))
        vbox.pack_end(widgetutil.align_middle(slider_box, bottom_pad=5))
        self.add(vbox)

    def on_remaining_clicked(self, widget):
        self.remaining_time.toggle_display()

    def on_slider_pressed(self, slider):
        app.playback_manager.suspend()
        
    def on_slider_moved(self, slider, new_time):
        app.playback_manager.seek_to(new_time)

    def on_slider_released(self, slider):
        app.playback_manager.resume()

    def set_duration(self, duration):
        self.slider.set_range(0, duration)
        self.slider.set_increments(5, min(20, duration / 20.0))
        self.remaining_time.set_duration(duration)

    def set_current_time(self, current_time):
        self.slider.set_value(current_time)
        self.time.set_current_time(current_time)
        self.remaining_time.set_current_time(current_time)

    def get_height(self, layout):
        # this assumes that the height is 14 pixels of space plus the
        # height of two labels--one for the time and one for the
        # title.  we do the max thing so there's a minimum height that
        # comes out of this.
        layout.set_font(0.8)
        sizer_text = layout.textbox("Foo")
        dummy, height = sizer_text.get_size()
        return max(40, 14 + (height * 2))

    def size_request(self, layout):
        layout.set_font(0.8)
        sizer_text = layout.textbox("Foo")
        dummy, height = sizer_text.get_size()
        return -1, self.get_height(layout)

    def draw(self, context, layout):
        if self.get_window().is_active():
            c = (40.0 / 255.0, 40.0 / 255.0, 40.0 / 255.0)
        else:
            c = (145.0 / 255.0, 145.0 / 255.0, 145.0 / 255.0)

        widgetutil.round_rect(context, 0, 0, context.width, context.height, 5)
        context.set_color(c)
        context.fill()

class VolumeSlider(widgetset.CustomSlider):
    def __init__(self):
        widgetset.CustomSlider.__init__(self)
        self.set_range(0.0, MAX_VOLUME)
        self.set_increments(0.05, 0.20)
        self.track = widgetutil.make_surface('volume_track')
        self.knob = widgetutil.make_surface('volume_knob')

    def is_horizontal(self):
        return True

    def is_continuous(self):
        return True

    def size_request(self, layout):
        return (self.track.width, max(self.track.height, self.knob.height))

    def slider_size(self):
        return self.knob.width

    def draw(self, context, layout):
        self.draw_track(context)
        self.draw_knob(context)

    def draw_track(self, context):
        y = (context.height - self.track.height) / 2
        self.track.draw(context, 0, y, self.track.width, self.track.height)

    def draw_knob(self, context):
        portion_right = self.get_value() / MAX_VOLUME
        x_max = context.width - self.slider_size()
        slider_x = int(round(portion_right * x_max))
        slider_y = (context.height - self.knob.height) / 2
        self.knob.draw(context, slider_x, slider_y, self.knob.width,
                self.knob.height)

class VideoBox(style.LowerBox):
    def __init__(self):
        style.LowerBox.__init__(self)
        self.controls = PlaybackControls()
        self.timeline = ProgressTimeline()
        if hasattr(widgetset, 'VolumeMuter'):
            self.volume_muter = widgetset.VolumeMuter()
        else:
            self.volume_muter = imagebutton.ImageButton('volume')
        if hasattr(widgetset, 'VolumeSlider'):
            self.volume_slider = widgetset.VolumeSlider()
        else:
            self.volume_slider = VolumeSlider()
        self.time_slider = self.timeline.slider

        hbox = widgetset.HBox(spacing=20)
        hbox.pack_start(self.controls, expand=False)
        hbox.pack_start(widgetutil.align_middle(self.timeline), expand=True)
        volume_hbox = widgetset.HBox(spacing=4)
        volume_hbox.pack_start(widgetutil.align_middle(self.volume_muter))
        volume_hbox.pack_start(widgetutil.align_middle(self.volume_slider))
        hbox.pack_start(volume_hbox)
        self.add(widgetutil.align_middle(hbox, 0, 0, 25, 25))

    def handle_new_selection(self, has_playable):
        self.controls.handle_new_selection(has_playable)
