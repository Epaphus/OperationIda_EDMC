
import sys
import Tkinter as tk
import myNotebook as nb
from config import config

this = sys.modules[__name__]
main = sys.modules["__main__"]

def plugin_start(plugin_dir):
    this.system_filter = config.get("Ida_system_filter")
    this.station_filter = config.get("Isa_station_filter")
    this.sold = {}
    this.sold_time = None
    this.current_system = ""
    this.current_station = ""
    return "Ida"

def plugin_stop():
    pass

def plugin_prefs(parent, cmd, is_beta):
    PADX=10
    PADY=2

    this.system_filter_setting = tk.StringVar(value=config.get("Ida_system_filter"))
    this.station_filter_setting = tk.StringVar(value=config.get("Ida_station_filter"))

    frame = nb.Frame(parent)
    nb.Label(frame, text="Station under repair").grid(row=0, column=0, padx=PADX, pady=PADY)
    nb.Label(frame, text="System").grid(row=1, column=0, padx=PADX, sticky=tk.W)
    nb.Entry(frame, text="System", textvariable=this.system_filter_setting).grid(row=1, column=1, padx=PADX, pady=PADY, sticky=tk.EW)
    nb.Label(frame, text="Station").grid(row=2, column=0, padx=PADX, sticky=tk.W)
    nb.Entry(frame, text="Station", textvariable=this.station_filter_setting).grid(row=2, column=1, padx=PADX, pady=PADY, sticky=tk.EW)
    button = nb.Button(frame, text="Use current station", command=use_current_station).grid(row=3, column=1, padx=PADX, pady=PADY, sticky=tk.EW)
    return frame

def plugin_app(parent):
    label = tk.Label(parent, text="Ida:")
    this.status = tk.Label(parent, text="", foreground="white")
    this.status.bind("<Button-1>", status_clicked)
    return (label, this.status)

def prefs_changed(cmdr, is_beta):
    config.set("Ida_system_filter", this.system_filter_setting.get())
    config.set("Ida_station_filter", this.station_filter_setting.get())
    this.system_filter = this.system_filter_setting.get()
    this.station_filter = this.station_filter_setting.get()

def use_current_station():
    this.system_filter_setting.set(current_system)
    this.station_filter_setting.set(current_station)
    prefs_changed(None, False)

def update_status():
    if sold_time is None:
        this.status["text"] = ""
    else:
        s = ", ".join("{} {}".format(count, material) for material, count in this.sold.items())
        s += " @ {}".format(this.sold_time)
        this.status["text"] = s

def status_clicked(e):
    main.root.clipboard_clear()
    main.root.clipboard_append(this.status["text"])
    this.sold_time = None
    this.sold = {}
    update_status()

def journal_entry(cmdr, is_beta, system, station, entry, state):
    this.current_system = system
    this.current_station = station

    if entry[u"event"] == u"MarketSell":
        count = entry[u"Count"]
        material = entry[u"Type"]
        server_time = entry[u"timestamp"].split("T")[1][:5]

        in_repair_station = system == this.system_filter and station == this.station_filter

        if in_repair_station:
            this.sold_time = server_time
            this.sold[material] = this.sold.get(material, 0) + count
            update_status()



