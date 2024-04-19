import gi
import subprocess
import threading
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

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
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        self.add(scrolled_window)

        # Create a TextView to show the output
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        scrolled_window.set_policy(Gtk.PolicyType.EXTERNAL, Gtk.PolicyType.EXTERNAL)
        scrolled_window.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))
        self.text_view.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))

        scrolled_window.get_vscrollbar().hide()
        scrolled_window.get_hscrollbar().hide()
        scrolled_window.add(self.text_view)
        self.text_view.connect('size-allocate', self.scroll_to_end)

        # Start a background thread to run journalctl and update the TextView
        self.journalctl_thread = threading.Thread(target=self.run_journalctl)
        self.journalctl_thread.daemon = True
        self.journalctl_thread.start()

    def run_journalctl(self):
        # Run journalctl subprocess
        process = subprocess.Popen(['journalctl', '-f'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        for line in iter(process.stdout.readline, ''):
            GLib.idle_add(self.update_text_view, line)

    def update_text_view(self, text):
        buffer = self.text_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text)
        start_iter = buffer.get_start_iter()
        # Check the number of lines in the buffer
        line_count = buffer.get_line_count()
        # If the line count exceeds 500, delete the oldest lines
        if line_count > 500:
            overflow = line_count - 500
            for _ in range(overflow):
                buffer.delete(start_iter, buffer.get_iter_at_line(1))

    def scroll_to_end(self, text_view, allocation):
        adj = self.text_view.get_vadjustment()
        upper = adj.get_upper()
        page_size = adj.get_page_size()
        offset = 5  # Adjust this value as needed to prevent hidden lines
        adj.set_value(upper - page_size - offset)

win = JournalctlWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
