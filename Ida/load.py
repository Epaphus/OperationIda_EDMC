
import sys
import myNotebook as nb
from config import config

# Python 3
import tkinter as tk
from tkinter import ttk

import csv
import os.path
from os import path

this = sys.modules[__name__]
main = sys.modules["__main__"]

# Originally from https://github.com/takev/OperationIda_EDMC
# Updated by CMDR Epaphus
# v 0.1

def plugin_start3(plugin_dir):
    this.system_filter = config.get_str("Ida_system_filter")
    this.station_filter = config.get_str("Ida_station_filter")
    this.sold = {}
    this.idasold = ""
    this.sold_time = None
    this.current_system = ""
    this.current_station = ""

    this.Dir = plugin_dir
    return "Ida"

def plugin_stop():
    pass

def plugin_prefs(parent, cmd, is_beta):
    PADX=10
    PADY=2

    this.system_filter_setting = tk.StringVar(value=config.get_str("Ida_system_filter"))
    this.station_filter_setting = tk.StringVar(value=config.get_str("Ida_station_filter"))

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
        # s = ", ".join("{} {} \n".format(count, material) for material, count in list(this.sold.items()))
        # s += " @ {}".format(this.sold_time)
        s = ", ".join("{} {} \n".format(count, material) for material, count in list(this.sold.items()))
        this.status["text"] = s

        #this.status["text"] = this.idasold
        
        

def status_clicked(e):
    main.root.clipboard_clear()
    #main.root.clipboard_append(this.status["text"])
    main.root.clipboard_append(this.idasold)
    this.sold_time = None
    this.sold = {}
    this.idasold = ""
    update_status()

def journal_entry(cmdr, is_beta, system, station, entry, state):
    this.current_system = system
    this.current_station = station

    if entry["event"] == "MarketSell":
        count = entry["Count"]
        material = entry["Type"]
        server_time = entry["timestamp"].split("T")[1][:5]
        server_timestamp = entry["timestamp"]

        in_repair_station = system == this.system_filter and station == this.station_filter

        if in_repair_station:
            this.sold_time = server_time
            this.sold[material] = this.sold.get(material, 0) + count

            this.idasold = this.idasold + "{} {} {} \n".format(count, material, server_time)

            update_status()

        