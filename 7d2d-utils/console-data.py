#!/usr/bin/env python3
"""Telnet to 7d2d server console, and pull data.
"""

from telnetlib  import Telnet
from time       import sleep
from re         import match
from yaml       import safe_dump , safe_load
from influxdb   import InfluxDBClient
from datetime   import datetime


def load_config( path ):
    with open( path , "r" ) as config_file:
        return safe_load( config_file.read() )

def type_correction( value ):
    """Convert dataytype if it matches the regex for an in, float, or bool"""
    _int_regex = "^-?\d+$"
    _float_regex = "^-?\d+\.\d+$"
    if match( _int_regex , value ):
        return int( value )
    elif match( _float_regex , _value):
        return float( _value )
    elif value.lower() == "true":
        return True
    elif value.lower() == "false":
        return False
    else:
        return value

def idb_now():
    """Return InfluxDB time string for now"""
    return datetime.utcnow().strftime( "%Y-%m-%dT%H:%M:%SZ" )

def is_idb( db_name , idb_client ):
    """Check if an InfluxDB already exists"""
    for idb in idb_client.get_list_database():
        if idb.get( "name" ) == db_name:
            return True
    return False

def idb_point( measurement, tags , fields ):
    """Return an IDB point

        measurement is a string
        tags and fields are dicts
    """
    return {
        "measurement": measurement,
        "tags": tags,
        "time": idb_now(),
        "fields": fields,
        }


if __name__ == '__main__':
    _config = load_config( "console-data.yml" )
    _telnet_server = _config.get( "telnet" , {} )
    _7d2d_passwd = _telnet_server.pop( "password" )
    _idb_server = _config.get( "influxdb" )
    _enable_idb = _idb_server.pop( "enabled" )
    _db = _idb_server.pop( "db" )


    _ret = {}
    with Telnet( **_telnet_server ) as tn:
        tn.read_until( b"Please enter password:" )
        tn.write( f"{_7d2d_passwd}\n".encode() )

        # Get Help
        tn.write( b"help\n" )
        _help = tn.read_until( b"xui => Execute XUi operations\r\n" ).decode()

        # Pull current players
        tn.write( b"lp\n" )
        _response = tn.read_until( b"in the game\r\n" ).decode()
        _list_item_regex = "^[0-9]*\.\ .*$"
        _players = {}
        for line in _response.split( "\n" ):
            if line:
                if match( _list_item_regex , line ):
                    _line_split = line.split( "," )
                    _player = {}
                    for num , data in enumerate( _line_split ):
                        if match( _list_item_regex , data ):
                            data = data.split( ". " )[ 1 ]
                        if data.startswith( " " ):
                            data = data[ 1: ]
                        # Initially skip pos and rot lines
                        if num < 2 or num > 7:
                            # 2 is name
                            if num == 2:
                                _player[ "name" ] = data
                            elif "=" in data:
                                _key , _value = data.split( "=" )
                                if _value.endswith( "\r" ):
                                    _value = _value[ :-1 ]
                                _value = type_correction( _value )
                                _player[ _key ] = _value
                    # Handle pos and rot
                    _pos_rot = [ f"{_line_split[2]}{_line_split[3]}{_line_split[4]}" , f"{_line_split[5]}{_line_split[6]}{_line_split[7]}" ]
                    for data in _pos_rot:
                        _key , _value = data.split( "=" )
                        if _key.startswith( " " ):
                            _key = _key[ 1: ]
                        _vector = []
                        for dimension in _value[ 1:-1 ].split():
                            _vector.append( float( dimension ) )
                        _value = dict( zip( [ "x" , "y" , "z" ] , _vector ) )
                        _player[ _key ] = _value
                    # Set name
                    _name = _line_split[ 1 ]
                    if _name.startswith( " " ):
                        _name = _name[ 1: ]
                    _players[ _name ] = _player
        _ret[ "players" ]  = _players

        # Get GameStat
        tn.write( b"ggs\n" )
        _response = tn.expect( [ b"GameStat.ZombieHordeMeter.*" ] )[ 2 ].decode()
        _game_stats = {}
        for line in _response.split( "\n" ):
            if line.endswith( "\r" ):
                line = line[ :-1 ]
            if line.startswith( "GameStat" ):
                line = line[ len( "GameStat." ): ]
                if " = " in line:
                    _key , _value = line.split( " = " )
                _game_stats[ _key ] = type_correction( _value )
        _ret[ "GameStat" ] = _game_stats

        # GetGame pref
        tn.write( b"gg\n" )
        _response = tn.expect( [ b"GamePref.ZombiePlayers.*" ] )[ 2 ].decode()
        _game_prefs = {}
        for line in _response.split( "\n" ):
            if line.endswith( "\r" ):
                line = line[ :-1 ]
            if line.startswith( "GamePref" ):
                line = line[ len( "GamePref." ): ]
                if " = " in line:
                    _key , _value = line.split( " = " )
                _game_prefs[ _key ] = type_correction( _value )
        _ret[ "GamePref" ] = _game_prefs
        
        # GetGame pref
        tn.write( b"getoptions\n" )
        _response = tn.expect( [ b"GamePref.OptionsZoomMouseSensitivity.*" ] )[ 2 ].decode()
        _game_opts = {}
        for line in _response.split( "\n" ):
            if line.endswith( "\r" ):
                line = line[ :-1 ]
            if line.startswith( "GamePref" ):
                line = line[ len( "GamePref." ): ]
                if " = " in line:
                    _key , _value = line.split( " = " )
                _game_opts[ _key ] = type_correction( _value )
        _ret[ "GameOpts" ] = _game_opts


        # Game Time
        tn.write( b"gt\n" )
        _response = tn.expect( [ b"Day.*" ] )[ 2 ].decode()
        _game_time = {}
        for line in _response.split( "\n" ):
            if line.endswith( "\r" ):
                line = line[ :-1 ]
            if line.startswith( "Day" ):
                _day , _time = line.split( ", " )
                _day = type_correction( _day[ len( "DAY " ): ] )
                _hour , _minute = _time.split( ":" )
                _hour = type_correction( _hour )
                _minute = type_correction( _minute )
        _ret[ "GameTime" ] = {
            "day": _day,
            "hour": _hour,
            "minute": _minute,
            }
            



        # Exit telnet
        tn.write( b"exit\n" )

    # influxDB logging for players
    if _enable_idb:
        _players = _ret.get( "players" , {} )
        _idb_points = []
        for _player_name in _players:
            _player_data = _players.get( _player_name )
            for key in _player_data:
                _value = _player_data.get( key )
                if key == "rot" or key == "pos":
                    # Handle pos and rot seperate, if I really want to graph position
                    pass
                else:
                    _idb_points.append(
                        idb_point(
                            "72d2_players",
                            tags = { "name", _player_name},
                            fields = { key: _value },
                            )
                        )
        idb_client = InfluxDBClient( **_idb_server )
        if not is_idb( _db , idb_client ):
            idb_client.create_database( _db )
        idb_client.switch_database( _db )
        idb_client.write_points( _idb_points )