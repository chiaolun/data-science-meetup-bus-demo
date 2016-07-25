#!/usr/bin/env python

import ujson
import pandas as pd
import numpy as np
import glob
import re
import matplotlib.pyplot as plt

pd.set_option("display.width", 200)

files = glob.glob("data/*.json")


def parse_file(file0):
    bus0, time0 = re.match('.*/(\d+)_(\d+)\.json', file0).groups()
    bus0 = int(bus0)
    time0 = (
        pd.to_datetime(time0, unit='s') +
        pd.Timedelta(hours=8)
    )
    data0 = ujson.load(open(file0))
    df = pd.DataFrame(
        [(bus0, time0, i, j, location0, state0)
         for i, t0 in enumerate(data0)
         for j, (location0, state0) in enumerate(t0)],
        columns=["bus", "time", "direction", "loc_no",
                 "loc", "state"]
    )
    return df

dat = pd.concat([parse_file(file0) for file0 in sorted(files)])

print(dat.head(30))

vehicle_chain_re = ["( \d{3}-\w{2})?"] * 5
vehicle_chain_re = "(\d{3}-\w{2})" + "".join(vehicle_chain_re)
print(vehicle_chain_re)

traj_idx = ["time", "direction", "loc_no"]

vehicle = dat.state.str.extract("^" + vehicle_chain_re, expand=True)
vehicle = pd.concat([dat[traj_idx], vehicle], axis=1)
vehicle = vehicle.set_index(traj_idx)
print(vehicle.head(50))

vehicle_post = dat.state.str.extract(vehicle_chain_re + "$", expand=True)
vehicle_post = pd.concat([dat[traj_idx], vehicle_post], axis=1)
vehicle_post = vehicle_post.set_index(traj_idx)
vehicle_post = vehicle_post.groupby(level=["time", "direction"]).shift()
print(vehicle_post.head(50))

traj = pd.concat([vehicle, vehicle_post], axis=1)
print(traj.head(10))

traj = traj.stack()
print(traj.head(10))

traj = traj.reset_index(-1, drop=True)
print(traj.head(10))

traj = traj.rename("vehicle").reset_index()
print(traj.head(10))

traj = traj.sort_values(["vehicle", "time"])
traj = traj.reset_index(drop=True)
print(traj.head(10))

gap = traj.groupby(["vehicle", "direction"]).time.diff()

traj["trip"] = (
    ((((traj[["vehicle", "direction"]] !=
        traj[["vehicle", "direction"]].shift())
       .any(axis=1)) |
      (gap > pd.Timedelta(minutes=1)))
     .cumsum())
)
trip_pts = traj.groupby("trip").time.count()
traj.merge(trip_pts[trip_pts > 10].reset_index()[["trip"]])
traj = traj.merge(trip_pts[trip_pts > 10].reset_index()[["trip"]])
print(traj.head(10))

print(traj[traj.trip == 7].loc[50:58].merge(dat))

traj0 = traj[traj.trip == 7].loc[50:58][["time", "direction"]].merge(dat)
print(traj0[traj0.loc_no.isin(range(26, 29))]
      .set_index(["time", "loc_no"])
      .unstack().state)


# locations = (
#     traj[["direction", "loc_no"]]
#     .drop_duplicates()
#     .sort_values(["direction", "loc_no"])
#     .reset_index(drop=True)
# )


# def add_missing_locs(df):
#     df = df.merge(
#         locations[locations.direction
#                   .isin(df.direction)],
#         how="right"
#     )
#     df["trip"] = (
#         df.trip.fillna(method="ffill")
#     )
#     df = df.sort_values(["loc_no"]).reset_index(drop=True)
#     df["time"] = df.time.fillna(method="bfill")
#     df["vehicle"] = df.vehicle.fillna(method="bfill")
#     return df
# traj = traj.groupby("trip", as_index=False).apply(add_missing_locs)
# traj = traj[traj.time.notnull()]

# arrival_times = (
#     traj
#     .groupby(["trip", "direction", "loc_no"]).time.min()
#     .groupby(level="trip").shift(-1).dropna()
#     .rename("arrival_time")
#     .reset_index("trip")
#     .sort_values("arrival_time")
#     .sort_index()
#     [["arrival_time"]]
# )
