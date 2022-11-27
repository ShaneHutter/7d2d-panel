#!/usr/bin/env python3
"""Telnet to 7d2d server console, and pull data.
"""

from telnetlib  import Telnet
from time       import sleep
from re         import match
from yaml       import safe_dump

_telnet_server = {
    "host": "gamer.intentropycs.com",
    "port": 8081,
    }

_7d2d_passwd = "7DaysAdmin"


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
    
    


if __name__ == '__main__':

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
        _players = []
        for line in _response.split( "\n" ):
            if line:
                if match( _list_item_regex , line ):
                    _line_split = line.split( "," )
                    _player = {}
                    _are_int = ( 0 , 9 , 10 ,11 , 12 , 13 , 14 , 18 )  # These are indexes where values are int and not str
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
                                if num in _are_int:
                                    _value = int( _value )
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
                        _value = tuple( _vector )
                        _player[ _key ] = _value
                    # Set Remote to Bool
                    _player[ "remote" ] = _player.get( "remote" ) == "True"
                    
                    _players.append( _player )
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

        # Exit telnet
        tn.write( b"exit\n" )

    
    print( safe_dump( _ret ) )