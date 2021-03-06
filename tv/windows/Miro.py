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

"""Startup the Main Miro process."""

def startup():
    theme = None
    # Should have code to figure out the theme.

    from miro.plat import pipeipc
    try:
        pipe_server = pipeipc.Server()
    except pipeipc.PipeExists:
        pipeipc.send_command_line_args()
        return
    pipe_server.start_process()

    from miro.plat import prelogger
    prelogger.install()

    from miro.plat.utils import initialize_locale
    initialize_locale()

    from miro import bootstrap
    bootstrap.bootstrap()

    from miro.plat import fontinfo
    fontinfo.init()

    from miro.plat import commandline
    args = commandline.get_command_line()[1:]
    if '--theme' in args:
        index = args.index('--theme')
        theme = args[index + 1]
        del args[index:index+1]

    from miro import startup
    startup.initialize(theme)

    from miro.plat import migrateappname
    migrateappname.migrateSupport('Democracy', 'Miro')

    from miro import commandline
    commandline.set_command_line_args(args)

    # Kick off the application
    from miro.plat.frontends.widgets.application import WindowsApplication
    WindowsApplication().run()
    pipe_server.quit()

    # sys.exit isn't sufficient--need to really end the process
    from miro.plat.utils import exit_miro
    exit_miro(0)

if __name__ == "__main__":
    startup()
