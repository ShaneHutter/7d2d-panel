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
    """Load the players xml.  
        `path` is the directory of the world data.
            Saves/{area_name}/{world_name}
    """
    _ret = {}
    with open( f"{path}/players.xml" , "r" ) as players_xml_file:
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
        _playername = player.get( "@playername" )
        _ret[ _playername ] = {
            "platform": _platform,
            "userid": _userid,
            "ttpfile": f"{_platform}_{_userid}.ttp",
            "lastlogin": player.get( "@lastlogin"),
            "lpblock": _lpblock,
            "bedroll": _beadroll,
            "playername": _playername,
            }
    return _ret


def load_ttp_bin( player , path ):
    """Load data from player ttp file.  
        `player` is the dictionary returned from load_players_xml for a single player
        `path` is the directory of the world data.
            Saves/{area_name}/{world_name}
    """
    _ttp_file_name = player.get( "ttpfile" )
    _ttp_file_path = f"{path}/Player/{_ttp_file_name}"
    with open( _ttp_file_path , "rb" ) as _ttp_file:
        _ttp_bin = _ttp_file.read()
    return _ttp_bin

def parse_ttp_bin( ttp_bin ):
    """An attempt to parse player stats from the players ttp file"""
    _ret = {}
    ATTRIBUTES = ( 
        "attperception", "attstrength", "attfortitude", 
        "attagility", "attintellect", "attbooks",
        )
    PERKS = ( 
        "perkdeadeye", "perkdemolitionsexpert", "perkjavelinmaster",
        "perklockpicking", "perkinfiltrator", "perkanimaltracker",
        "perkpenetrator", "perkluckylooter", "perktreasurehunter",
        "perksalvageoperations", "perkboomstick", "perkpummelpete",
        "perkskullcrusher", "perksexualtrex", "perkheavyarmor",
        "perkpackmule", "perkmasterchef", "perkminer69r",
        "perkmotherlode", "perkbrawler", "perkmachinegunner",
        "perkthehuntsman", "perkwellinsulated", "perklivingofftheland",
        "perkpaintolerance", "perkhealingfactor", "perkslowmetabolism",
        "perkruleonecardio", "perkarchery", "perkgunslinger",
        "perkdeepcuts", "perkrunandgun", "perkflurryofblows",
        "perklightarmor", "perkparkour", "perkhiddenstrike",
        "perkfromtheshadows", "perkelectrocutioner", "perkturrets",
        "perkbetterbarter", "perkdaringadventurer", "perkcharismaticnature",
        "perkphysician", "perkadvancedengineering", "perkgreasemonkey",
        "perkfiremansalmanacheat", "perkfiremansalmanacaxes", "perkfiremansalmanacspeed",
        "perkfiremansalmanacmolotov", "perkfiremansalmanacprevention", "perkfiremansalmanacharvest",
        "perkfiremansalmanacequipment", "perkfiremansalmanaccomplete", "perkneedleandthreadwinterwear",
        "perkneedleandthreadlegwear", "perkneedleandthreadfootwear", "perkneedleandthreaddesertwear",
        "perkneedleandthreaddusters", "perkneedleandthreadpuffercoats", "perkneedleandthreadpockets",
        "perkneedleandthreadcomplete", "perknightstalkerstealthdamage", "perknightstalkersilentnight",
        "perknightstalkerblades", "perknightstalkerthiefadrenaline", "perknightstalkerarchery",
        "perknightstalkertwilightthief", "perknightstalkerslumberparty", "perknightstalkercomplete",
        "perkluckylooterdukes", "perkluckylooterammunition", "perkluckylooterbrass",
        "perkluckylooterlead", "perkluckylooterbooks", "perkluckylooterfood",
        "perkluckylootermedical", "perkluckylootercomplete", "perkenforcerdamage",
        "perkenforcerapparel", "perkenforcerpunks", "perkenforcerintimidation",
        "perkenforcerapammo", "perkenforcerhpammo", "perkenforcercriminalpursuit",
        "perkenforcercomplete", "perkbatterupbighits", "perkbatterupgear",
        "perkbatterupslowpitch", "perkbatterupknockdown", "perkbatterupmaintenance",
        "perkbatterupbaseballbats", "perkbatterupmetalchain", "perkbatterupcomplete",
        "perkgreatheistsafes", "perkgreatheistgems", "perkgreatheisttimedcharge",
        "perkgreatheistclaimed", "perkgreatheistadrenalinefall", "perkgreatheistsprintsneak",
        "perkgreatheistmotiondetection", "perkgreatheistcomplete", "perkwastetreasureshoney",
        "perkwastetreasurescoffins", "perkwastetreasuresacid", "perkwastetreasureswater",
        "perkwastetreasuresdoors", "perkwastetreasurescloth", "perkwastetreasuressinks",
        "perkwastetreasurescomplete", "perkhuntingjournalbears", "perkhuntingjournalwolves",
        "perkhuntingjournalcoyotes", "perkhuntingjournalmountainlions", "perkhuntingjournaldeer",
        "perkhuntingjournalvultures", "perkhuntingjournalselfdefense", "perkhuntingjournalcomplete",
        "perkartofminingluckystrike", "perkartofminingdiamondtools", "perkartofminingcoffee",
        "perkartofminingblackstrap", "perkartofminingpallets", "perkartofminingavalanche",
        "perkartofmininglantern", "perkartofminingcomplete", "perkrangersarrowrecovery",
        "perkrangersexplodingbolts", "perkrangerscripplingshot", "perkrangersapammo",
        "perkrangersflamingarrows", "perkrangersforestguide", "perkrangersknockdown",
        "perkrangerscomplete", "perkpistolpetetakeaim", "perkpistolpeteswissknees",
        "perkpistolpetesteadyhand", "perkpistolpetemaintenance", "perkpistolpetehpammo",
        "perkpistolpeteapammo", "perkpistolpetedamage", "perkpistolpetecomplete",
        "perkshotgunmessiahdamage", "perkshotgunmessiahbreachingslugs", "perkshotgunmessiahlimbshot",
        "perkshotgunmessiahslugs", "perkshotgunmessiahmaintenance", "perkshotgunmessiahmagazine",
        "perkshotgunmessiahpartystarter", "perkshotgunmessiahcomplete", "perksniperdamage",
        "perksnipercripplingshot", "perksniperheadshot", "perksniperreload",
        "perksnipercontrolledbreathing", "perksniperapammo", "perksniperhpammo",
        "perksnipercomplete", "perkautoweaponsdamage", "perkautoweaponsuncontrolledburst",
        "perkautoweaponsmaintenance", "perkautoweaponsdrummag", "perkautoweaponsrecoil",
        "perkautoweaponsragdoll", "perkautoweaponsmachineguns", "perkautoweaponscomplete",
        "perkurbancombatlanding", "perkurbancombatcigar", "perkurbancombatsneaking",
        "perkurbancombatjumping", "perkurbancombatlandmines", "perkurbancombatadrenalinerush",
        "perkurbancombatroomclearing", "perkurbancombatcomplete", "perktechjunkie1damage",
        "perktechjunkie2maintenance", "perktechjunkie3apammo", "perktechjunkie4shells",
        "perktechjunkie5repulsor", "perktechjunkie6batoncharge", "perktechjunkie7hydraulics",
        "perktechjunkie8complete", "perkbarbrawling1basicmoves", "perkbarbrawling2dropabomb",
        "perkbarbrawling3killerinstinct", "perkbarbrawling4finishingmoves", "perkbarbrawling6ragemode",
        "perkbarbrawling7boozedup", "perkbarbrawling8complete", "perkspearhunter1damage",
        "perkspearhunter2maintenance", "perkspearhunter3steelspears", "perkspearhunter4strongarm",
        "perkspearhunter5rapidstrike", "perkspearhunter6puncturedlung", "perkspearhunter7quickstrike",
        "perkspearhunter8complete",
        )
    SKILLS = (
        "skillPointTip", "skillperceptioncombat", "skillperceptiongeneral",
        "skillperceptionscavenging", "skillstrengthcombat", "skillstrengthgeneral",
        "skillstrengthconstruction", "skillfortitudecombat", "skillfortitudesurvival",
        "skillfortituderecovery", "skillagilitycombat", "skillagilityathletics",
        "skillagilitystealth", "skillintellectcombat", "skillintellectinfluence",
        "skillintellectcraftsmanship", "skillartofmining", "skillautoweapons",
        "skillbatterup", "skillbarbrawling", "skillfiremansalmanac",
        "skillgreatheist", "skillhuntingjournal", "skillluckylooter",
        "skillenforcer", "skillneedleandthread", "skillnightstalker",
        "skillpistolpete", "skillarchery", "skillshotguns",
        "skillsniper", "skillspearhunter", "skillurbancombat",
        "skilltechjunkie", "skillwastetreasures",
        )
    return _ret

if __name__ == '__main__':
    _players_xml_path = "player_data"
    players = load_players_xml( _players_xml_path )

    #print( safe_dump( players ) )
    lordie_wolfe = players.get( "Lordie Wolfe" )
    ttp_bin = load_ttp_bin( lordie_wolfe , _players_xml_path )

    print( ttp_bin )
