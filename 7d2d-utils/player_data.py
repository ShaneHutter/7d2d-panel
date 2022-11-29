#!/usr/bin/env python3
"""Read character ttp files to pull stats
"""

from xmltodict  import (
    parse as xml_parse,
    unparse as xml_unparse,
    )
from yaml       import safe_dump
from copy       import deepcopy


def load_players_xml( path ):
    _ret = {}
    with open( path , "r" ) as players_xml_file:
        _players = xml_parse( players_xml_file.read() )
    _players = _players.get( "persistentplayerdata" , {} ).get( "player" )
    for player in _players:
        _platform = player.get( "@platform" )
        _userid = player.get( "@userid" )
        _lpblock =  player.get( "lpblock" , {} ).get( "@pos" , "" ).split( "," )
        for num , val in enumerate( deepcopy( _lpblock ) ):
            if val:
                _lpblock[ num ] = int( val )
            else:
                _lpblock = None
                break
        _beadroll =  player.get( "bedroll" , {} ).get( "@pos" , "" ).split( "," )
        for num , val in enumerate( deepcopy( _beadroll ) ):
            if val:
                _beadroll[ num ] = int( val )
            else:
                _beadroll = None
                break


        _ret[ player.get( "@playername" ) ] = {
            "platform": _platform,
            "userid": _userid,
            "ttpfile": f"{_platform}_{_userid}.ttp",
            "lastlogin": player.get( "@lastlogin"),
            "lpblock": _lpblock,
            "bedroll": _beadroll,
            }
    return _ret


if __name__ == '__main__':
    _players_xml_path = "player_data/players.xml"
    players = load_players_xml( _players_xml_path )

    print( safe_dump( players ) )
