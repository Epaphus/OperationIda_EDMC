
import sys
import myNotebook as nb
from config import config

# Python 3
import tkinter as tk
from tkinter import ttk

import csv
import os.path
from os import path

from typing import Optional

from theme import theme

frame: Optional[tk.Frame] = None

this = sys.modules[__name__]
main = sys.modules["__main__"]

# Originally from https://github.com/takev/OperationIda_EDMC
# Updated by CMDR Epaphus (https://github.com/Epaphus/OperationIda_EDMC)
this.plugin_version = "1.3"

def plugin_start3(plugin_dir):
    this.system_filter = config.get_str("Ida_system_filter")
    this.station_filter = config.get_str("Ida_station_filter")
    this.log_current = config.get_str("Ida_log_current")
    this.log_all = config.get_str("Ida_log_all")
    this.sold = {}
    this.idasold = ""
    this.sold_time = None
    this.current_system = ""
    this.current_station = ""
    this.delivery_count_text = "None"

    this.Dir = plugin_dir
    return "Ida"

def plugin_stop():
    pass

def plugin_prefs(parent, cmd, is_beta):
    PADX=10
    PADY=2

    this.system_filter_setting = tk.StringVar(value=config.get_str("Ida_system_filter"))
    this.station_filter_setting = tk.StringVar(value=config.get_str("Ida_station_filter"))
    this.log_current_setting = tk.StringVar(value=config.get_str("Ida_log_current"))
    this.log_all_setting = tk.StringVar(value=config.get_str("Ida_log_all"))

    frame = nb.Frame(parent)
    nb.Label(frame, text="Station under repair").grid(row=0, column=0, padx=PADX, pady=PADY)
    nb.Label(frame, text="System").grid(row=1, column=0, padx=PADX, sticky=tk.W)
    nb.Entry(frame, text="System", textvariable=this.system_filter_setting).grid(row=1, column=1, padx=PADX, pady=PADY, sticky=tk.EW)
    nb.Label(frame, text="Station").grid(row=2, column=0, padx=PADX, sticky=tk.W)
    nb.Entry(frame, text="Station", textvariable=this.station_filter_setting).grid(row=2, column=1, padx=PADX, pady=PADY, sticky=tk.EW)
    button = nb.Button(frame, text="Use current station", command=use_current_station).grid(row=3, column=1, padx=PADX, pady=PADY, sticky=tk.EW)
    nb.Label(frame, text="").grid(row=4, column=0, padx=PADX, pady=PADY, sticky=tk.W)
    nb.Checkbutton(frame, text="Log goods sold at repair station to csv file", variable=this.log_current_setting).grid(row=5, column=0, padx=PADX, pady=PADY, sticky=tk.W)
    nb.Checkbutton(frame, text="Log goods sold at any station to csv file", variable=this.log_all_setting).grid(row=6, column=0, padx=PADX, pady=PADY, sticky=tk.W)
    nb.Label(frame, text="CSV files will be stored in the plugin folder").grid(row=7, column=0, padx=PADX, pady=PADY, sticky=tk.W)
    nb.Label(frame, text="CSV file format - Date, Station, Material, Amount sold ").grid(row=8, column=0, padx=PADX, pady=PADY, sticky=tk.W)

    nb.Label(frame, text="").grid(row=20, column=0, padx=PADX, pady=PADY, sticky=tk.W)
    nb.Label(frame, text="Plugin Version: %s" % this.plugin_version).grid(row=21, column=0, padx=PADX, pady=PADY, sticky=tk.W)

    return frame

def plugin_app(parent: tk.Frame) -> tk.Frame:
    global frame
    frame = tk.Frame(parent)
    row = frame.grid_size()[1]

    title_widget = tk.Label(frame, text="Operation Ida")
    title_widget.grid(row=0, column=0, sticky=tk.W)

    update_station_widget = tk.Button(frame, text="Use current station", command=use_current_station)
    update_station_widget.bind("<Button-1>", use_current_station)
    update_station_widget.grid(row=0, column=1, sticky=tk.W)

    logging_widget = tk.Label(frame, text="Logging for:")
    logging_widget.grid(row=1, column=0, sticky=tk.W)
    this.station_widget = tk.Label(frame, text=this.station_filter)
    this.station_widget.grid(row=1, column=1, sticky=tk.W)

    delivery_widget = tk.Label(frame, text="Deliveries:")
    delivery_widget.grid(row=2, column=0, sticky=tk.W)
    this.delivery_count_widget = tk.Label(frame, text="")
    this.delivery_count_widget.grid(row=2, column=1, sticky=tk.W)
    this.delivery_count_widget.bind("<Button-1>", status_clicked)

    reset_btn = tk.Button(frame, text="Copy to Clipboard", command=status_clicked)
    reset_btn.bind("<Button-1>", status_clicked)
    reset_btn.grid(row=3, column=0, sticky=tk.W)

    return frame

def prefs_changed(cmdr, is_beta):
    config.set("Ida_system_filter", this.system_filter_setting.get())
    config.set("Ida_station_filter", this.station_filter_setting.get())
    config.set("Ida_log_current", this.log_current_setting.get())
    config.set("Ida_log_all",this.log_all_setting.get())
    this.system_filter = this.system_filter_setting.get()
    this.station_filter = this.station_filter_setting.get()
    this.log_current = this.log_current_setting.get()
    this.log_all = this.log_all_setting.get()
    this.station_widget ["text"] = this.station_filter


def use_current_station():
    this.system_filter_setting.set(current_system)
    this.station_filter_setting.set(current_station)
    #this.station_widget ["text"] = current_station
    prefs_changed(None, False)

def update_status():
    if sold_time is None:
        this.status["text"] = ""
    else:
        s = ", ".join("{} {} \n".format(count, material) for material, count in list(this.sold.items()))
        this.delivery_count_widget["text"] = s

def status_clicked(e):
    main.root.clipboard_clear()
    main.root.clipboard_append(this.idasold)
    this.sold_time = None
    this.sold = {}
    this.idasold = ""
    this.delivery_count_widget["text"] = "None"
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

        if this.log_all == "1":
            update_file('any-station-log.csv',server_timestamp,station,material,count)

        if in_repair_station:
            this.sold_time = server_time
            this.sold[material] = this.sold.get(material, 0) + count

            this.idasold = this.idasold + "{} {} {} \n".format(count, material, server_time)

            update_status()
            if this.log_current == "1":
                update_file('repair-station-log.csv',server_timestamp,station,material,count)

def update_file(filename, time, station, material, count):
    file = os.path.join(this.Dir, filename)
    with open(file, 'a', newline='') as csvfile:
        fieldnames = ['Time','Station','Material','Count']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'Time':time, 'Station': station , 'Material': material , 'Count': count })
        csvfile.close
        