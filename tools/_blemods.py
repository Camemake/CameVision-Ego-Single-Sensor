try:
    import dbus
    print("dbus", getattr(dbus, "__file__", "ok"))
except Exception as e:
    print("dbus", type(e).__name__, e)
try:
    import gi
    print("gi", "ok")
except Exception as e:
    print("gi", type(e).__name__, e)
try:
    from gi.repository import GLib
    print("GLib", "ok")
except Exception as e:
    print("GLib", type(e).__name__, e)
