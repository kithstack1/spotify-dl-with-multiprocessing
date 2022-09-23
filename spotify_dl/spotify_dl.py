#!/usr/bin/env python3
import argparse
import time
import json
import os
import sys
from logging import DEBUG
from pathlib import Path, PurePath
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from spotify_dl.constants import VERSION
from spotify_dl.scaffold import log, get_tokens, console
from spotify_dl.spotify import (
    fetch_tracks,
    parse_spotify_url,
    validate_spotify_urls,
    get_item_name,
)
from spotify_dl.youtube import download_songs, default_filename, playlist_num_filename


def spotify_dl():
    """Main entry point of the script."""
    parser = argparse.ArgumentParser(prog="spotify_dl")
    parser.add_argument(
        "-l",
        "--url",
        action="store",
        help="Spotify Playlist link URL",
        type=str,
        nargs="+",
        required=False,  # this has to be set to false to prevent useless prompt for url when all user wants is the script version
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        action="store",
        help="Specify download directory.",
        required=False,
        default=".",
    )
    parser.add_argument(
        "-d",
        "--download",
        action="store_true",
        help="Download using youtube-dl",
        default=True,
    )
    parser.add_argument(
        "-f",
        "--format_str",
        type=str,
        action="store",
        help="Specify youtube-dl format string.",
        default="bestaudio/best",
    )
    parser.add_argument(
        "-k",
        "--keep_playlist_order",
        default=False,
        action="store_true",
        help="Whether to keep original playlist ordering or not.",
    )
    parser.add_argument(
        "-m",
        "--skip_mp3",
        action="store_true",
        help="Don't convert downloaded songs to mp3",
    )
    parser.add_argument(
        "-s",
        "--skip_non_music_sections",
        default=False,
        action="store_true",
        help="Whether to skip non-music sections using SponsorBlock API.",
    )
    parser.add_argument(
        "-w",
        "--no-overwrites",
        action="store_true",
        help="Whether we should avoid overwriting the target audio file if it already exists",
        default=False,
    )
    parser.add_argument(
        "-V",
        "--verbose",
        action="store_true",
        help="Show more information on what" "s happening.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Shows current version of the program",
    )
    parser.add_argument(
        "-mc",
        "--multi_core",
        action="store",
        type=str,
        default=0,
        help="Use multiprocessing [-m [int:numcores]",
    )
    args = parser.parse_args()
    args.multi_core = int(args.multi_core)
    if args.version:
        console.print(f"spotify_dl [bold green]v{VERSION}[/bold green]")
        sys.exit(0)

    if os.path.isfile(os.path.expanduser("~/.spotify_dl_settings")):
        with open(os.path.expanduser("~/.spotify_dl_settings")) as file:
            config = json.load(file)
            print(config)

        for key, value in config.items():
            if (isinstance(value, bool) and value) or (
                isinstance(value, str) and value and value.lower() in ["true", "t"]
            ):
                setattr(args, key, True)
            else:
                setattr(args, key, value)
    else:
        print("no config file")

    if args.verbose:
        log.setLevel(DEBUG)
    if not args.url:
        raise (Exception("No playlist url provided:"))

    console.log(f"Starting spotify_dl [bold green]v{VERSION}[/bold green]")
    log.debug("Setting debug mode on spotify_dl")

     
    C_ID, C_SECRET = 'a7f37282a11042e78fd0014047f6faea', '050617d5d562441da4e5b82178b216fa'
    sp = spotipy.Spotify(
        auth_manager=SpotifyClientCredentials(client_id=C_ID, client_secret=C_SECRET)
    )
    log.debug("Arguments: %s ", args)

    valid_urls = validate_spotify_urls(args.url)
    if not valid_urls:
        sys.exit(1)

    url_data = {'urls' : []}

    for url in valid_urls:
        url_dict = {}
        item_type, item_id = parse_spotify_url(url)
        directory_name = get_item_name(sp, item_type, item_id)
        url_dict["save_path"] = Path(
            PurePath.joinpath(Path(args.output), Path(directory_name))
        )
        url_dict["save_path"].mkdir(parents=True, exist_ok=True)
        console.print(
            f"Saving songs to [bold green]{directory_name}[/bold green] directory"
        )
        url_dict["songs"] = fetch_tracks(sp, item_type, url)
        url_data["urls"].append(url_dict.copy())
    if args.download is True:
        file_name_f = default_filename
        if args.keep_playlist_order:
            file_name_f = playlist_num_filename

        download_songs(
            songs=url_data,
            output_dir=args.output,
            format_str=args.format_str,
            skip_mp3=args.skip_mp3,
            keep_playlist_order=args.keep_playlist_order,
            no_overwrites=args.no_overwrites,
            skip_non_music_sections=args.skip_non_music_sections,
            file_name_f=file_name_f,
            multi_core=args.multi_core,
        )


if __name__ == "__main__":
    starttime = time.time()
    spotify_dl()
    print(f"[*] finished in {time.time() - starttime}")
