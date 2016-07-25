#!/usr/bin/env python

import ujson
import pandas as pd
import numpy as np
import glob
import re
import matplotlib.pyplot as plt
import seaborn as sns

pd.set_option("display.width", 200)


def parse_file(file0):
    "reads json into a pandas datafram"
    # parses file name to get the route and the time
    bus0, time0 = re.match('.*/(\d+)_(\d+)\.json', file0).groups()
    bus0 = int(bus0)
    time0 = (
        pd.to_datetime(time0, unit='s') +
        pd.Timedelta(hours=8)
    )
    # opens json file - note that I use ujson here because it is
    # faster
    data0 = ujson.load(open(file0))
    # list comprehension to get a flat vector from the json
    df = [(bus0, time0, i, j, location0, state0)
          for i, t0 in enumerate(data0)
          for j, (location0, state0) in enumerate(t0)]
    # convert flat vector into a dataframe
    df = pd.DataFrame(
        df,
        columns=["bus", "time", "direction", "loc_no", "loc", "state"]
    )
    return df

# list all files
files = glob.glob("data/*.json")
# parse all files and concat the individual dataframes together
dat = pd.concat([parse_file(file0) for file0 in sorted(files)])

print(dat.head(30))

# construct regex for parsing out the vehicle identifiers
vehicle_chain_re = ["( \d{3}-\w{2})?"] * 5
vehicle_chain_re = "(\d{3}-\w{2})" + "".join(vehicle_chain_re)
print(vehicle_chain_re)

traj_idx = ["time", "direction", "loc_no"]

# extract vehicle numbers at the beginning of strings
vehicle = dat.state.str.extract("^" + vehicle_chain_re, expand=True)
vehicle = pd.concat([dat[traj_idx], vehicle], axis=1)
vehicle = vehicle.set_index(traj_idx)
print(vehicle.head(50))

# extract vehicle numbers at the end of strings
vehicle_post = dat.state.str.extract(vehicle_chain_re + "$", expand=True)
vehicle_post = pd.concat([dat[traj_idx], vehicle_post], axis=1)
# additional two steps to shift the label forward by one, since label
# at the end of the string means the bus has passed that station
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

# due to pandas' lack of a non-sorted groupby, we use the
# unequal + cumsum trick to get groupings, we we call trips

# we also start a new trip whenever there is a gap greater than one
# minute
traj["trip"] = (
    ((((traj[["vehicle", "direction"]] !=
        traj[["vehicle", "direction"]].shift())
       .any(axis=1)) |
      (gap > pd.Timedelta(minutes=1)))
     .cumsum())
)
# only keep trips with more than 10 data points
trip_pts = traj.groupby("trip").time.count()
traj.merge(trip_pts[trip_pts > 10].reset_index()[["trip"]])
traj = traj.merge(trip_pts[trip_pts > 10].reset_index()[["trip"]])
trip_pts = trip_pts.sort_values()
print(trip_pts.tail(10))

# Plot some trips
(traj[traj.trip.isin(trip_pts.tail(10).index)]
 .set_index(["time", "direction", "trip"])
 .unstack([-1, -2]).loc_no.plot())
plt.show()


# investigate anomalies
traj[traj.trip == 209].loc_no.plot()
plt.show()
print(traj[traj.trip == 209])

traj0 = traj[traj.trip == 209].loc[3640:3650][["time", "direction"]].merge(dat)
print(traj0[traj0.loc_no.isin(range(30, 40))]
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
