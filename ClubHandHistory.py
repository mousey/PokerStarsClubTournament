#Imports
import regex as re
import pprint
from pathlib  import Path
from decimal  import Decimal
from datetime import datetime

# Variable to hold the hand history
handhistory = {}
# Variable to hold the number of hands in a tournament
tournamenthands = {}
# Variable to hold the time a tournament started
tournamenttime = {}
# Variable to hold the number of chips
tournamentchips = {}
# Variable to hold the cash made in a tournament
tournamentcash = {}
# Variable to hold seat names
seatnames = {2:{0: "BTN-SB",1: "BB"},
             3:{0: "BTN",1: "SB",2: "BB"},
             4:{0: "BTN",1: "SB",2: "BB",3: "CO"},
             5:{0: "BTN",1: "SB",2: "BB",3: "HJ",4: "CO"},
             6:{0: "BTN",1: "SB",2: "BB",3: "UTG",4: "HJ",5: "CO"},
             7:{0: "BTN",1: "SB",2: "BB",3: "UTG",4: "MP1",5: "HJ",6: "CO"},
             8:{0: "BTN",1: "SB",2: "BB",3: "UTG",4: "MP1",5: "MP2",6: "HJ",7: "CO"},
             9:{0: "BTN",1: "SB",2: "BB",3: "UTG",4: "UTG+1",5: "MP1",6: "MP2",7: "HJ",8: "CO"}}

# Function for adding Prize Money to the player for each tournament
def _add_prize(tournament, playe, prize):
    if tournament in tournamentcash.keys():
        if playe in tournamentcash[tournament]:
            if 'prize' in tournamentcash[tournament][playe]:
                tournamentcash[tournament][playe]['prize'] = tournamentcash[tournament][playe]['prize'] + prize
            else:
                tournamentcash[tournament][playe].update({'prize': prize})
        else:
            tournamentcash[tournament].update({playe: {'prize': prize}})
    else:
        tournamentcash[tournament] = {playe: {'prize': prize}}

# Function for adding finishing position to the player for each tournament
def _add_position(tournament, playe, position):
    if tournament in tournamentcash.keys():
        if playe in tournamentcash[tournament]:
            tournamentcash[tournament][playe]['position'] = position
        else:
            tournamentcash[tournament].update({playe: {'position': position}})
    else:
        tournamentcash[tournament] = {playe: {'position': position}}

# Function for adding who knocked out the player and on which hand for each tournament
def _add_knockout(tournament, playe, victo, hand, kotime):

    if tournament in tournamentcash.keys():
        if playe in tournamentcash[tournament]:
            tournamentcash[tournament][playe]['ko-by'] = victo
            tournamentcash[tournament][playe]['ko-hand'] = hand
            tournamentcash[tournament][playe]['ko-time'] = kotime
        else:
            tournamentcash[tournament].update({playe: {'ko-by': victo}})
            tournamentcash[tournament].update({playe: {'ko-hand': hand}})
            tournamentcash[tournament].update({playe: {'ko-time': kotime}})
    else:
        tournamentcash[tournament] = {playe: {'ko-by': victo}}
        tournamentcash[tournament][playe].update({'ko-hand': hand})
        tournamentcash[tournament][playe].update({'ko-time': kotime})

# Function for adding hands played to the player for each tournament
def _add_played(tournament, playe):
    if tournament in tournamentcash.keys():
        if playe in tournamentcash[tournament]:
            if 'played-hand' in tournamentcash[tournament][playe]:
                tournamentcash[tournament][playe]['played-hand'] = tournamentcash[tournament][playe]['played-hand'] + 1
            else:
                tournamentcash[tournament][playe].update({'played-hand': 1})
        else:
            tournamentcash[tournament].update({playe: {'played-hand': 1}})
    else:
        tournamentcash[tournament] = {playe: {'played-hand': 1}}

# Function for adding hands won to the player for each tournament
def _add_won(tournament, playe):
    if tournament in tournamentcash.keys():
        if playe in tournamentcash[tournament]:
            if 'won-hand' in tournamentcash[tournament][playe]:
                tournamentcash[tournament][playe]['won-hand'] = tournamentcash[tournament][playe]['won-hand'] + 1
            else:
                tournamentcash[tournament][playe].update({'won-hand': 1})
        else:
            tournamentcash[tournament].update({playe: {'won-hand': 1}})
    else:
        tournamentcash[tournament] = {playe: {'won-hand': 1}}

def _add_action(tournament, section, line):
    name, _, action = line.partition(": ")
    action, _, amount = action.partition(" ")
    amount, _, _ = amount.partition(" ")

    if amount:
        if amount.isnumeric(): 
            actions.append(section + ": " + name + " - " + action + " - " + amount)
            # We're only interested in bets not the Ante
            if not action == "ante":
                if section in bets:
                    if name in bets[section]:
                        bets[section][name] = bets[section][name] + Decimal(amount or 0)
                    else:
                        bets[section].update({name: Decimal(amount or 0)})
                else:
                    bets[section] = {name: Decimal(amount or 0)}
    else:
        if action:
            actions.append(section + ": " + name + " - " + action)

def _add_collected(tournament, section, line):
    first_space_index = line.find(" ")
    name = line[:first_space_index]
    second_space_index = line.find(" ", first_space_index + 1)
    third_space_index = line.find(" ", second_space_index + 1)
    amount = line[second_space_index + 1 : third_space_index]

    actions.append(section + ": " + name + " - collected - " + amount)

def _parse_actions(tournament, section, line):  
    if "collected" in line:
        _add_collected(tournament, section, line)
    elif ":" in line:
        # shrink the wording to Ante, SmallBlind, BigBlind
        line = line.replace("posts the ","")
        line = line.replace("posts small blind","SmallBlind")
        line = line.replace("posts big blind","BigBlind")

        # we only want the end value not the value they raised
        if "raises" in line:
            raisesline = line.split()
            raisedline = [raisesline[0], raisesline[1] + "-to", raisesline[4]]
            line =  ' '.join(raisedline)

        _add_action(tournament, section, line)
    elif "Uncalled" in line and section == "preflop":
        first_paren_index = line.find("(")
        second_paren_index = line.find(")")
        amount = line[first_paren_index + 1 : second_paren_index]
        name_start_index = line.find("to ") + 3
        name = line[name_start_index:]

        if name == seats["BB"] and amount == str(bb - sb):
            if tournament in tournamentcash.keys():
                if name in tournamentcash[tournament]:
                    if 'free-bb' in tournamentcash[tournament][name]:
                        tournamentcash[tournament][name]['free-bb'] = tournamentcash[tournament][name]['free-bb'] + 1
                    else:
                        tournamentcash[tournament][name].update({'free-bb': 1})
                else:
                    tournamentcash[tournament].update({name: {'free-bb': 1}})



# RegEx values we'll use later
_hands_re  = re.compile(r"\n\n\n\n")            # Used to split the full file into hands where we see 4 \n values (\n = new line)
_split_re = re.compile(r" ?\*\*\* ?\n?|\n")     # Used to split a hand into different sections HOLE CARDS, FLOP, TURN, RIVER, SHOW DOWN, SUMMARY
_header_re = re.compile(r"""
^PokerStars\s+(.+)?                             # Line starts with PokerStars
Hand\s+\#(?P<ident>\d+):\s+                     # Get the Hand History ID
(\{Club\s+\#(?P<club_ident>\d+)\}\s+)?          # Get the Club ID
(Tournament\s+\#(?P<tournament_ident>\d+),\s+   # Get the Tournament ID
((?P<freeroll>Freeroll)|(                       # Are we playing Freeroll
\$?(?P<buyin>\d+(\.\d+)?)                       # Get the Buy-In Value
(\+\$?(?P<knockrake>\d+(\.\d+)?))?              # Get the Rake Value or Knockout Value if we're playing Knockout
(\+\$?(?P<rake>\d+(\.\d+)?))?                   # Get the Rake Value if we're playing Knockout
(\s+(?P<currency>[A-Z]+))?                      # Get the Currency
))\s+
)?
(?P<game>.+?)\s+                                # What type of Poker are we playing
(?P<limit>(?:Pot\s+|No\s+|)Limit)\s+            # Is there a limit
(-\s+Level\s+(?P<tournament_level>\S+)\s+)?     # Tournament Level (how many times has the BB/SB gone up)
\(
(((?P<sb>\d+)\/(?P<bb>\d+))|(                   # Tournament SB and BB
\$(?P<cash_sb>\d+(\.\d+)?)\/                    # Cash Game SB
\$(?P<cash_bb>\d+(\.\d+)?)                      # Cash Game BB
(\s+(?P<cash_currency>\S+))?                    # Casg Game Currency
))
\)\s+
-\s+(?P<ldate>.+?\s+.+?)                        # Local Date
(?(?=\s\[.+?\])\s\[(?P<edate>.+?)\]|$)          # Date in ET
""", re.VERBOSE,)
_table_re = re.compile(
    r"^Table '(.*)' (\d+)-max Seat #(?P<button>\d+) is the button"                  # Get Button on Table
)
_seat_re = re.compile(
    r"^Seat (?P<seat>\d+): (?P<name>.+?) \(\$?(?P<stack>\d+(\.\d+)?) in chips\)"    # Get Seat, Name, and Stack Count for each player
) 
_hero_re = re.compile(r"^Dealt to (?P<hero_name>.+?) \[(..) (..)\]")                # Get Player Name who's file this is
_pot_re = re.compile(r"^Total pot (\d+(?:\.\d+)?) .*\| Rake (\d+(?:\.\d+)?)")       # Total Pot value
_winner_re = re.compile(r"^Seat (\d+): (\S+?) .+?ollected \((\d+(?:\.\d+)?)\)")     # Winner of the Hand if no cards are shown
_showdown_re = re.compile(r"^Seat (\d+): (.+?) showed \[(.+?)\] and won")           # Winner of the Hand if cards shown
_mucked_re = re.compile(r"^Seat (\d+): (\S+?)\s.+?\[(.+?)\]")                       # Cards Mucked by a player
_folded_re = re.compile(r"^Seat (\d+): (\S+?)\s.")                                 # Hand played but folded
_ante_re = re.compile(r".*posts the ante (\d+(?:\.\d+)?)")                          # Who posted the Ante
_board_re = re.compile(r"(?<=[\[ ])(..)(?=[\] ])")                                  # Final Board
_knockout_re = re.compile(r"^(?P<victor>.+?) wins the \$(?P<bounty>\d+(\.\d+)?)? bounty for eliminating (?P<loser>.+)?")         # Who Knocked out Who
_finisher_re = re.compile(r"^(?P<finisher>.+?) finished the tournament in (?P<position>\d+)(.+\$(?P<fprize>\d+(?:\.\d+)?))?")   # Player finished position and if they got cash
_tournament_winner_re = re.compile(r"^(?P<winner>.+?) wins the tournament and receives \$(?P<prize>\d+(?:\.\d+)?)")             # Tournament Winner and their winnings


# Open the Hand History Log File
with open(Path(__file__).absolute().parent / "S02E04.txt", mode='r', encoding='utf-8-sig') as f:

    # Read the file in as a String
    raw_file = f.read()

    # split the file up into the different hands using the regex above
    hands = _hands_re.split(raw_file.rstrip())

    # loop through each hand
    for hand in hands:
        # Variable to determine if we're playing knockout
        knocko = False

        # split the hand into the different sections (FLOP, RIVER, TURN, SUMMARY)
        split_hand = _split_re.split(hand)
        sections = [ind for ind, elem in enumerate(split_hand) if not elem]

        # extract all the information from the header section
        header = _header_re.match(split_hand[0])

        # Set variables from the regex we performed
        tournament = header.group('tournament_ident')
        club       = header.group('club_ident')
        handid     = header.group('ident')
        buyin      = Decimal(header.group('buyin') or 0)
        knock      = Decimal(header.group('knockrake') or 0)
        sb         = Decimal(header.group("sb") or header.group("cash_sb"))
        bb         = Decimal(header.group("bb") or header.group("cash_bb"))
        strdtime   = header.group('ldate') or header.group("edate")
        splitdtime = strdtime.split()
        dtime      = datetime.strptime(splitdtime[0] + " " + splitdtime[1], '%Y/%m/%d %H:%M:%S')
        # if the value rake is set then we're playing knockout so there's a seperate value for knockout and rake
        if header.group('rake'):
            rake       = Decimal(header.group('rake') or 0)
            knocko      = True
        else:
        # if the value for rake is not set then the rake value was captured by the knock variable so set rake to be that
            rake = knock

        # if we haven't seen this tournament before set the start time
        if not tournament in tournamenttime.keys():
            tournamenttime[tournament] = dtime
            ditim = "0"
        else:
            kodiff = dtime - tournamenttime[tournament]
            komin  = divmod(kodiff.seconds, 60)
            kohour = divmod(komin[0], 60)
            ditim = str(kohour[0]) + ':' + str(kohour[1]) + ':' + str(komin[1])

        # extract the information about the table
        table = _table_re.match(split_hand[1])
        button = int(table.group('button'))

        # extract all the information about the players at the start of the hand (Player Names and Chip Count)
        # variable to store the players on each hand (this resets each hand as the number of players could change)
        players = {}
        buttonplayer = ""
        buttonseat = 0

        playerlines = 2
        for line in split_hand[playerlines:]:
            player = _seat_re.match(line)
            # we reached the end of the players section
            if not player:
                break
        
            name=player.group("name")
            stack=int(player.group("stack"))
            seat=int(player.group("seat"))

            # if the seat number matches the button number record the players name
            if seat == button:
                buttonplayer = name
                buttonseat = playerlines - 1

            # add players stack to the players variable
            players[name] = stack
            playerlines += 1
        
        
        # Set the players seat names
        seats = {}
        j = 0
        seatorder = []
        
        # Loop through the number of players 
        while j < len(players):
            seatorder.append(j)
            j += 1

        # switch the seats around to correct where the button seat is
        j = 0
        while j < buttonseat - 1:
            seatorder = seatorder[-1:] + seatorder[:-1]
            j += 1

        i = 0
        # Loop through the player names and assign their seat name
        for handplayers in players.keys():
            j = seatnames[len(players)][seatorder[i]]
            seats[j] = handplayers
            i += 1
        
        # if we've seen this tournament ID before
        if tournament in tournamenthands.keys():
            # add one for each hand we're recording of the tournament
            tournamenthands[tournament] = tournamenthands[tournament] + 1
        else:
            # otherwise add the tournament to our tournamenthands variable and start the count at 1
            tournamenthands[tournament] = 1

        bets = {}
        actions = []

        # extract all the action from the PRE-FLOP
        for line in split_hand[playerlines: sections[1]]:
            _parse_actions(tournament, "preflop", line)

        # extract all the action from the FLOP
        flop_happend = "FLOP" in split_hand
        
        if flop_happend:
            start   = sections[1] + 3
            end     = sections[2]

            if start < end: 
                for line in split_hand[start:end]:
                    _parse_actions(tournament, "flop", line)

        # extract all the action from the TURN
        turn_happend = "TURN" in split_hand

        if turn_happend:
            start   = sections[2] + 3
            end     = sections[3]

            if start < end: 
                for line in split_hand[start:end]:
                    _parse_actions(tournament, "turn", line)

        # extract all the action from the RIVER
        river_happend = "RIVER" in split_hand

        if river_happend:
            start   = sections[3] + 3
            end     = sections[4]

            if start < end: 
                for line in split_hand[start:end]:
                    _parse_actions(tournament, "river", line)

        # extract all the information from the SHOWDOWN section
        show_down = "SHOW DOWN" in split_hand

        if show_down:
            start = sections[-2] + 2
            end   = sections[-1]

            knockouts = {}
            for line in split_hand[start:end]:
                if "bounty" in line:
                    # record the person who got knocked out and by who
                    knockout = _knockout_re.match(line)
                    _add_knockout(tournament, knockout.group('loser'), knockout.group('victor'), tournamenthands[tournament], ditim)

                    # add the knockout bonus to the victors total
                    _add_prize(tournament, knockout.group('victor'), Decimal(knockout.group('bounty') or 0))

                elif "finished" in line: 
                    position = _finisher_re.match(line)
                    # add the name of the person who has gone out to the tournament position variable
                    _add_position(tournament, position.group('finisher'), position.group('position'))
                    
                    # if the person who has gone out finished in the money, add their prize to their total
                    if position.group('fprize'):
                        _add_prize(tournament, position.group('finisher'), Decimal(position.group('fprize') or 0))
                        
                elif "wins the tournament" in line:
                    twinner = _tournament_winner_re.match(line)
                    prize = Decimal(twinner.group('prize') or 0)
                    # if we're playing knockout add the winners own knockout value to their winnings
                    if knocko:
                        prize += knock

                    # add the winner to the tournament position variable
                    _add_position(tournament, twinner.group('winner'), "1")

                    # add the winners cash to the cash variable for the tournament
                    _add_prize(tournament, twinner.group('winner'), prize)

                    # knocked themselves out
                    _add_knockout(tournament, twinner.group('winner'), twinner.group('winner'), tournamenthands[tournament], ditim)

                elif "collected" in line:
                    _add_collected(tournament, "showdown", line)

        # extract all the information about the Cards on the Table
        board = {}
        boardline = split_hand[sections[-1] + 3]
        if not boardline.startswith("Board"):
            board = {}
        else:
            cards = _board_re.findall(boardline)
            board['flop1'] = cards[0]
            board['flop2'] = cards[1]
            board['flop3'] = cards[2]
            if len(cards) > 3:
                board['turn'] = cards[3] 
            if len(cards) > 4:
                board['river'] = cards[4]

        # extract the hand winners and players who played in the hand
        playedhand = {}
        winners = []
        # pick where to start looking at the lines if a Board is shown or not
        start = sections[-1] + 4
        if not split_hand[sections[-1] + 3].startswith("Board"):
            start = sections[-1] + 3
        
        for line in split_hand[start:]:
            # If there was no showdown then someone COLLECTED a winning without showing their cards
            if not show_down and "collected" in line:
                winner = _winner_re.match(line)
                winners.append(winner.group(2))
                playedhand[winner.group(2)] = "Not Shown"
                _add_played(tournament, winner.group(2))
                _add_won(tournament, winner.group(2))
            # If there is a showdown then someone(s) WON the hand and showed their cards
            elif show_down and "won" in line:
                winner = _mucked_re.match(line)
                winners.append(winner.group(2))
                playedhand[winner.group(2)] = winner.group(3)
                _add_played(tournament, winner.group(2))
                _add_won(tournament, winner.group(2))
            # Get the card information of everyone else in the Showdown
            elif not "before Flop" in line:
                played  = _mucked_re.match(line)
                
                if played is not None:
                    playedhand[played.group(2)] = played.group(3)
                    _add_played(tournament, played.group(2))
                else:
                    played = _folded_re.match(line)
                    playedhand[played.group(2)] = "Folded"
                    _add_played(tournament, played.group(2))

        if tournament in handhistory.keys():
            handhistory[tournament].append({'hand': {'id': handid, 'time': ditim, 'no': tournamenthands[tournament], 'chips': players, 'played': playedhand, 'board': board, 'winners': winners, 'bets': bets, 'actions': actions, 'seats': seats}})
        else:
            handhistory[tournament] = [{'hand': {'id': handid, 'time': ditim, 'no': tournamenthands[tournament], 'chips': players, 'played': playedhand, 'board': board, 'winners': winners, 'bets': bets, 'actions': actions, 'seats': seats}}]

        if tournament in tournamentchips.keys():
            tournamentchips[tournament].append({'hand': {'id': handid, 'time': ditim, 'no': tournamenthands[tournament], 'chips': players}})
        else:
            tournamentchips[tournament] = [{'hand': {'id': handid, 'time': ditim, 'no': tournamenthands[tournament], 'chips': players}}]

pprint.pprint(tournamentcash) # Tournament standings
#print.pprint(tournamentchips) # Chips each player had on each hand
#pprint.pprint(handhistory) # Everything