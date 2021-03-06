# Miro - an RSS based video player application
# Copyright (C) 2010, 2011
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

import logging
import os

import gio

from miro import app
from miro.plat.frontends.widgets import timer

class DeviceTracker(object):
    def __init__(self):
        self._unix_device_to_drive = {}
        self._disconnecting = {}

    def start_tracking(self):
        volume_monitor = gio.volume_monitor_get()
        volume_monitor.connect('drive-connected', self._drive_connected)
        volume_monitor.connect('drive-changed', self._drive_changed)
        volume_monitor.connect('mount-added', self._mount_added)
        volume_monitor.connect('drive-disconnected', self._drive_disconnected)

        for drive in volume_monitor.get_connected_drives():
            self._drive_connected(volume_monitor, drive)

    def _get_device_info(self, drive):
        volumes = drive.get_volumes()
        if volumes:
            for volume in volumes:
                id_ = volume.get_identifier('unix-device')
                mount = size = remaining = None
                mount = volume.get_mount()
                if mount:
                    mount = mount.get_root().get_path()
                    if mount and os.path.exists(mount):
                        if mount[-1] != os.path.sep:
                            mount = mount + os.path.sep # make sure
                                                                  # it ends
                                                                  # with a /
                        statinfo = os.statvfs(mount)
                        size = statinfo.f_frsize * statinfo.f_blocks
                        remaining = statinfo.f_frsize * statinfo.f_bavail

                self._unix_device_to_drive[id_] = drive
                yield id_, {
                    'name': drive.get_name(),
                    'visible_name': volume.get_name(),
                    'mount': mount,
                    'size': size,
                    'remaining': remaining
                    }
        elif drive.get_name() != 'CD/DVD Drive':
            # we tack on the 1 so that the unmounted device maps to the same ID
            # as the first partition
            id_ = drive.get_identifier('unix-device') + '1'
            self._unix_device_to_drive[id_] = drive
            yield id_, {'name': drive.get_name()}

    def _drive_connected(self, volume_monitor, drive):
        if drive is None:
            # can happen when a CD is inserted
            return
        logging.debug('seen device: %r', drive.get_name())
        for id_, info in self._get_device_info(drive):
            if id_ in self._disconnecting:
                # Gio sends a disconnect/connect pair when the device is
                # mounted so we wait a little and check for spurious ones
                timeout_id = self._disconnecting.pop(id_)
                timer.cancel(timeout_id)
                return
            app.device_manager.device_connected(id_, **info)

    def _drive_changed(self, volume_monitor, drive):
        if drive is None:
            # can happen when a CD is inserted
            return
        for id_, info in self._get_device_info(drive):
            app.device_manager.device_changed(id_, **info)

    def _mount_added(self, volume_monitor, mount):
        self._drive_changed(volume_monitor, mount.get_drive())

    def _drive_disconnected(self, volume_monitor, drive):
        if drive is None:
            # can happen when a CD is inserted
            return
        for id_, info in self._get_device_info(drive):
            timeout_id = timer.add(0.5, self._drive_disconnected_timeout, id_)
            self._disconnecting[id_] = timeout_id

    def _drive_disconnected_timeout(self, id_):
        del self._disconnecting[id_]
        try:
            del self._unix_device_to_drive[id_]
        except KeyError:
            pass
        app.device_manager.device_disconnected(id_)

    def eject(self, device):
        if device.id not in self._unix_device_to_drive:
            return
        drive = self._unix_device_to_drive[device.id]
        drive.eject(self._eject_callback,
                    gio.MOUNT_UNMOUNT_NONE, None, None)

    def _eject_callback(self, drive, result, user_info):
        try:
            drive.eject_finish(result)
        except gio.Error:
            # XXX notify the user in some way?
            logging.exception('eject failed for %r' % drive)
