import gi
import subprocess
import threading
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')

from gi.repository import Gtk, GLib, Gdk, Wnck

class JournalctlWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Journalctl Output")
        self.maximize()
        self.set_decorated(False)
        self.set_type_hint(Gdk.WindowTypeHint.DESKTOP)
        # Enable RGBA window
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        # Set transparent background
        self.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))

        # Create a ScrolledWindow to contain the TextView
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)
        self.add(self.scrolled_window)

        # Create a TextView to show the output
        self.label = Gtk.Label()
        #self.label.set_selectable(True)
        self.label.set_line_wrap(True)
        self.label.set_justify(Gtk.Justification.LEFT)
        self.label.set_valign(Gtk.Align.START)
        self.label.set_halign(Gtk.Align.START)
        self.label.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            label {
                color: rgba(212, 245, 213, 0.4); /* White color with 80% opacity */
                background-color: rgba(0, 0, 0, 0); /* Transparent background */
            }
        """)
        Wnck.Screen.get_default().force_update()
        
        # Connect to the active-workspace-changed signal
        screen = Wnck.Screen.get_default()
        screen.connect("active-workspace-changed", self.on_active_workspace_changed)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.scrolled_window.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.EXTERNAL)
        self.scrolled_window.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))

        self.scrolled_window.get_vscrollbar().hide()
        self.scrolled_window.get_hscrollbar().hide()
        self.scrolled_window.add(self.label)

        # Start a background thread to run journalctl and update the TextView
        self.journalctl_thread = threading.Thread(target=self.run_journalctl)
        self.journalctl_thread.daemon = True
        self.journalctl_thread.start()
        self.on_active_workspace_changed(screen, screen.get_active_workspace())

    def run_journalctl(self):
        # Run journalctl subprocess
        process = subprocess.Popen(['journalctl', '-f'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            GLib.idle_add(self.update_text_view, line)

    def update_text_view(self, text):
        current_text = self.label.get_text()
        new_text = current_text + text
        self.label.set_text(new_text)
        lines = new_text.split('\n')
        if len(lines) > 500:
            trimmed_text = '\n'.join(lines[-500:])
            self.label.set_text(trimmed_text)
        self.scroll_to_bottom()
        # Check the number of lines in the buffer
       
    def scroll_to_bottom(self):
        # Obtain the vertical Gtk.Adjustment of the scrolled window
        vadjustment = self.scrolled_window.get_vadjustment()

        # The upper value may not be updated immediately, so we use idle_add to wait
        # until the main loop is idle and then set the value to the upper bound
        GLib.idle_add(vadjustment.set_value, vadjustment.get_upper())

        # Process pending main loop events to ensure the adjustment bounds are updated
        while Gtk.events_pending():
            Gtk.main_iteration()

    def on_active_workspace_changed(self, screen, previously_active_space):
        active_workspace = screen.get_active_workspace()
        if active_workspace:
            workspace_number = active_workspace.get_number()
            if workspace_number != 0:
                self.hide()
            else:
                self.show_all()
            print(f"Workspace switched to {workspace_number}")




win = JournalctlWindow()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
