#!/usr/bin/env python3

import json
import os
import sys
import argparse
import csv
from datetime import timezone
from zoneinfo import ZoneInfo, available_timezones
from operator import itemgetter
from dateutil import parser as duparser
import simplekml

__version__ = "1.0.0"
__author__ = "Corey Forman (digitalsleuth)"


def parse_json(json_file, tz="UTC", date=None):
    total_data = []
    with open(json_file, "r") as content:
        for line in content.readlines():
            ride_data = json.loads(line)
            processed_data = process_json(ride_data, tz)
            total_data.append(processed_data)
    all_keys = sorted(set().union(*total_data))
    sorted_data = json.dumps(sorted(total_data, key=itemgetter("createdAt")))
    json_data = json.loads(sorted_data)
    if date:
        filtered_json = []
        for ride in json_data:
            ride_start_date = ride["startedAt"].split("T")[0]
            ride_end_date = ride["completedAt"].split("T")[0]
            if date not in (ride_start_date, ride_end_date):
                continue
            filtered_json.append(ride)
        json_data = filtered_json
    return json_data, all_keys


def process_json(json_content, tz="UTC"):
    non_standard_keys = {
        "birdScanId",
        "canceledAt",
        "endPhotoUrl",
        "endPoint",
        "endSource",
        "fleetId",
        "movedAt",
        "notifiedAt",
        "reservationId",
        "startPoint",
        "startedByDeviceId",
        "startedInNoRideArea",
        "startedOutsideOperatingArea",
        "unlockedAt",
    }
    times = [
        "canceledAt",
        "completedAt",
        "createdAt",
        "dates",
        "movedAt",
        "notifiedAt",
        "startedAt",
        "unlockedAt",
    ]
    for key in non_standard_keys:
        if key not in json_content:
            json_content[key] = "None Identified"
    if tz != "UTC":
        tz = ZoneInfo(str(tz))
        for selected_time in times:
            orig_time = json_content[selected_time]
            if orig_time == "None Identified":
                continue
            if (
                selected_time == "dates"
                and isinstance(orig_time, list)
                and orig_time != []
            ):
                new_dates = []
                for each in orig_time:
                    parsed_time = duparser.parse(each)
                    new_time = parsed_time.replace(tzinfo=timezone.utc)
                    new_time = new_time.astimezone(tz).strftime(
                        f"%Y-%m-%dT%H:%M:%S.%f {tz}"
                    )
                    new_dates.append(new_time)
                json_content["dates"] = new_dates
            else:
                parsed_time = duparser.parse(orig_time)
                new_time = parsed_time.replace(tzinfo=timezone.utc)
                new_time = new_time.astimezone(tz).strftime(
                    f"%Y-%m-%dT%H:%M:%S.%f {tz}"
                )
                json_content[selected_time] = new_time

    return json_content


def generate_kml(filename, json_content):
    """Generates a KML file from the ride data"""
    normal_icon = "https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png"
    highlight_icon = (
        "https://www.gstatic.com/mapspro/images/stock/503-wht-blank_maps.png"
    )
    kml = simplekml.Kml()
    for i, this_ride in enumerate(json_content, start=1):
        folder = kml.newfolder()
        ride = folder.newlinestring(name=f"Ride {i}", tessellate=1)
        ride.stylemap.normalstyle.labelstyle.scale = 0
        ride.stylemap.normalstyle.iconstyle.color = "ff3644db"
        ride.stylemap.normalstyle.iconstyle.scale = 1
        ride.stylemap.normalstyle.iconstyle.icon.href = normal_icon
        ride.stylemap.normalstyle.iconstyle.hotspot.x = 32
        ride.stylemap.normalstyle.iconstyle.hotspot.xunits = "pixels"
        ride.stylemap.normalstyle.iconstyle.hotspot.y = 64
        ride.stylemap.normalstyle.iconstyle.hotspot.yunits = "insetPixels"
        ride.stylemap.normalstyle.linestyle.color = "ffff6712"
        ride.stylemap.normalstyle.linestyle.width = 5
        ride.stylemap.highlightstyle.labelstyle.scale = 1
        ride.stylemap.highlightstyle.iconstyle.color = "ff3644db"
        ride.stylemap.highlightstyle.iconstyle.scale = 1
        ride.stylemap.highlightstyle.iconstyle.icon.href = highlight_icon
        ride.stylemap.highlightstyle.iconstyle.hotspot.x = 32
        ride.stylemap.highlightstyle.iconstyle.hotspot.xunits = "pixels"
        ride.stylemap.highlightstyle.iconstyle.hotspot.y = 64
        ride.stylemap.highlightstyle.iconstyle.hotspot.yunits = "insetPixels"
        ride.stylemap.highlightstyle.linestyle.color = simplekml.Color.red
        ride.stylemap.highlightstyle.linestyle.width = 7.5
        this_ride_coords = []
        start_time = this_ride["startedAt"]
        end_time = this_ride["completedAt"]
        has_start = False
        has_end = False
        if this_ride["startPoint"] != "None Identified":
            start_lat = this_ride["startPoint"]["latitude"]
            start_long = this_ride["startPoint"]["longitude"]
            has_start = True
        if this_ride["endPoint"] != "None Identified":
            end_lat = this_ride["endPoint"]["latitude"]
            end_long = this_ride["endPoint"]["longitude"]
            has_end = True
        ride.stylemap.highlightstyle.balloonstyle.text = f"""
    <![CDATA[
        <div style="width: 300px;">
            <h2>Ride {i}</h2>
            <p>Starts at {start_time}</p>
            <p>Ends at {end_time}</p>
            <p>End Photo URL:</p>
            <p>{this_ride["endPhotoUrl"]}</p>
            <p>User ID: {this_ride["userId"]}</p>
        </div>
    ]]>
    """
        ride.stylemap.highlightstyle.balloonstyle.bgcolor = simplekml.Color.white
        ride.stylemap.highlightstyle.balloonstyle.textcolor = simplekml.Color.black
        ride.description = ""
        if has_start:
            this_ride_coords.append((start_long, start_lat))
        if has_end:
            this_ride_coords.append((end_long, end_lat))
        coord_len = len(this_ride_coords)
        if coord_len != 0:
            for coord in this_ride_coords:
                ride.description += f"{coord[0]},{coord[1]}\n"
            ride.coords = this_ride_coords
            if has_start:
                start_point = folder.newpoint(name=f"Start - {start_time}")
                start_point.coords = [this_ride_coords[0]]
                start_point.style.iconstyle.icon.href = (
                    "http://maps.google.com/mapfiles/kml/paddle/A.png"
                )
            if has_end:
                end_point = folder.newpoint(name=f"End - {end_time}")
                end_point.coords = [this_ride_coords[-1]]
                end_point.style.iconstyle.icon.href = (
                    "http://maps.google.com/mapfiles/kml/paddle/B.png"
                )
            folder.name = f"Ride {i} - {start_time} - {end_time}"
        else:
            continue
    try:
        kml.save(f"{filename}.kml")
        print(f"KML file generated - {filename}.kml")
    except IOError as err:
        print(f"Error encountered trying to save KML file - {err}")


def generate_psv(filename, parsed_data, all_columns):
    output_file = f"{filename}.psv"
    with open(output_file, "w", newline="", encoding="utf-8") as out_psv:
        header = all_columns
        try:
            writer = csv.DictWriter(out_psv, header, delimiter="|")
            writer.writeheader()
            for ride in parsed_data:
                writer.writerow(ride)
            out_psv.close()
        except IOError as err:
            print(f"Unable to write PSV file: {err}")
            sys.exit(1)
        print(f"PSV file generated - {output_file}")


def print_available_timezones():
    all_tz = []
    for tz in available_timezones():
        all_tz.append(tz)
    tzs = sorted(all_tz)
    for tz in tzs:
        print(tz)


def main():
    arg_parse = argparse.ArgumentParser(description=f"Bird Scooter Ride JSON parser v{__version__}")
    arg_parse.add_argument("file", help="Ride JSON file")
    arg_parse.add_argument(
        "-d", "--date", help="Specific date to filter on - 'YYYY-MM-DD'", default=None
    )
    arg_parse.add_argument("-k", "--kml", help="Output a KML file", action="store_true")
    arg_parse.add_argument(
        "-l", "--list", help="List available timezones", action="store_true"
    )
    arg_parse.add_argument(
        "-p",
        "--psv",
        help="Output a Pipe (|) Separated Value (.psv) file",
        action="store_true",
    )
    arg_parse.add_argument(
        "-t",
        "--tz",
        help="Select a timezone for output, in quotes: 'TZ_NAME'",
        type=str,
        default="UTC",
    )
    if len(sys.argv[1:]) == 0:
        arg_parse.print_help()
        arg_parse.exit()
    if len(sys.argv[1:]) > 0 and ("-l" in sys.argv or "--list" in sys.argv):
        print_available_timezones()
        sys.exit(0)
    args = arg_parse.parse_args()
    if not os.path.exists(args.file) or not os.path.isfile(args.file):
        print(f"Cannot process {args.file}. Please check your path and try again")
        sys.exit(1)
    if args.tz and args.tz not in available_timezones():
        print(
            "Your selected timezone cannot be identified. Please run this script with -l / --list to see the available timezones and try again."
        )
        sys.exit(1)
    parsed_json, json_keys = parse_json(args.file, args.tz, args.date)
    if args.kml:
        generate_kml(args.file, parsed_json)
    if args.psv:
        generate_psv(args.file, parsed_json, json_keys)


if __name__ == "__main__":
    main()
