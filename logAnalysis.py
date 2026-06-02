import sqlite3
import yaml
import sys
from tenhouLogMaster import TenhouDecoder
import xml.etree.ElementTree as ET
import bz2
from numpy import *  
from contextlib import redirect_stdout
import csv
import math


#adds a h onto front of honor tiles for ease of sorting. 
# they will always lead the hand.

##this could very well be changed to convery the tiles to
## objects instead of just strings.
def simplifyTile(tile):
    newTile = tile[:2]
    if(tile[0].isdigit()):
        newTile = 'n' + tile[1] + tile[0]
    else:
        newTile = 'h' + newTile
    return newTile

def simplifyHand(hand: list):
    for i in range(len(hand)):
        hand[i] = simplifyTile(hand[i])
    hand.sort()



def xmlToGames(dbFile: str, limit: int):
    con = sqlite3.connect(dbFile)
    cursor = con.cursor()

    #this selects all 4 player south games 
    cursor.execute(f"SELECT log_content FROM logs WHERE (is_hirosima = 0) and (is_tonpusen = 0) LIMIT {limit};")
    rows = cursor.fetchall()
    con.close()
    
    games = getGames(rows)

    return games

def getGames(compressedGameData):
    #could change this to an input once ENG is debugged
    lang = 'DEFAULT'
    
    games = []
    for data in compressedGameData:
        data = data[0]
        data = bz2.decompress(data)
        game = TenhouDecoder.Game(lang)
        game.decode(data)
        games = games + [game]
    return games

    


def getGame(gameData, index: int):
    #this changes data from a 1 element tuple into a string so that etree can parse it later
    #also im pretty sure it's selecting 1 of the 10 games lol, check that so we ca itterate
    
    data = gameData[index][0]
    data = bz2.decompress(data)



    #eng is technically an option but it's very buggy so def is used instead
    lang = 'DEFAULT'
    game = TenhouDecoder.Game(lang)
    game.decode(data)


    return game

def displayHand(hand):
    tempHand = hand.copy()
    simplifyHand(tempHand)
    tempHand.sort()
    print(tempHand)

def getFirstRiichi(round):
    reaches = round["reach_turns"]
    if(len(reaches) == 0):
        return None
    else:
        return reaches[0]
    


#check this later to see if reaches are in sorted order to start with
# START HERE NEXT :)
def calcAvrgRiichi(games):
    sum = 0
    riichiRoundCounter = 0
    roundCounter = 0
    for game in games:
        gameData = game.asdata()
        rounds  = gameData["rounds"]
        for round in rounds:
            
            roundCounter += 1

            firstRiichi = getFirstRiichi(round)
            if firstRiichi is None:
                continue
            else:
                sum += firstRiichi
                riichiRoundCounter += 1
    riichiPercentage = riichiRoundCounter / roundCounter
    averageRiichiTurn = sum / riichiRoundCounter
    return riichiPercentage, averageRiichiTurn

def makeSujiTable(games, limit):
    
    #data will be filled with tuples of key val pairs
    data = []

    i = 0
    x = 1
    for game in games:
        if(i / limit >= (0.01 * x)):
            print(math.floor((i / limit)*100+1), r"% complete ")
            x += 1
        i += 1
        gameData = game.asdata()
        rounds  = gameData["rounds"]

        roundNumber = 0

        for round in rounds:
        # this should all be a round parsing function realisitically {
            roundNumber += 1

            if(len(round["reach_turns"]) == 0):
                #not including games where riichi wasn't called
                continue
            else:
                player = round["reaches"][0]
                riichiTurn = round["reach_turns"][0]
                hand = round["hands"][player]

                tilesSuji, tilesGenbutsu, eventCount, numRyanmanAvailable = getSafeTiles(round, hand, player, riichiTurn)
                remainingEvents = round["events"][(eventCount+1):]
                

                ## NEEDS TO BE UPDATED TO CHECK IF IS GENBUTSU
                sujiDiscardOutput = checkFirstDiscard(remainingEvents, tilesSuji, player)
                genbutsuDiscardOutput = checkFirstDiscard(remainingEvents, tilesGenbutsu, player)
                
                try:
                    isGenbutsu, discardPlayer =  (e for e in genbutsuDiscardOutput)
                    isSuji, discardPlayer = (e for e in sujiDiscardOutput)
                    
                except TypeError:
                    continue

                #maybe change this to is loss and include tsumo losses it will be interesting
                isWinner = checkWinners(round, discardPlayer)
                if(isWinner):
                    isLoser = False
                else :
                    isLoser = checkLosers(round, discardPlayer)
                
                
                isGenbutsu = int(isGenbutsu)
                isSuji = int(isSuji)
                isWinner = int(isWinner)
                
                tableRow = [dict({" isSuji ": isSuji, " isGenbutsu": isGenbutsu, " round ":roundNumber, " isWinner ": isWinner, " isLoser ": isLoser, " numRyanmanAvailable ":numRyanmanAvailable  })]

                data += tableRow
        # this should all be a round parsing function realisitically }
    return data




def checkWinners(round, discardPlayer):
    for agari in round["agari"]:
        if (agari["player"] == discardPlayer):
            return True
    return False

def checkLosers(round, discardPlayer):
    for agari in round["agari"]:
        if(agari["type"] == "TSUMO"):
            return True
        else:
            #agari is RON implicitly here
            if(agari["player"] == discardPlayer):
                return True
            else:
                continue
    return False
    



#finds the first non dealer discard after riichi
#returns if it was a suji discard and who discarded
def checkFirstDiscard(events, tilesSafe, player):
    
    for event in events:
        
        if(event["type"] == "Dora"):
            continue
        
        if( (event["player"] != player) and (event["type"] == "Discard") ):
            tile = event["tile"]
            if(tile in tilesSafe):
                return True, event["player"]
            else:
                return False, event["player"]

    #need some error handling down here

def getSafeTiles(round, hand, player, riichiTurn):
    def getSuji(tile):
        sujiTiles = []
        value = int(tile[0])
        # loops to cover all 4 version of the tile
        for i in range(4):

            if(value <= 3):
                sujiTiles += [str(value + 3) + tile[1:2] + str(i)] 
            elif(value >= 7):
                sujiTiles += [str(value - 3) + tile[1:2] + str(i)]
            else:
                sujiTiles += [ str(value + 3) + tile[1:2] + str(i) , str(value - 3) + tile[1:3] + str(i) ]
        return sujiTiles
    
    def getGenbutsu(tile):
        genbutsuTiles = []
        # loops to cover all 4 version of the tile
        for i in range(4):
            genbutsuTiles += [tile[:2] + str(i)]
            
                 
        return genbutsuTiles

    sujiTiles = []
    genbutsuTiles =[]
    eventCount = 0
    turnCounter = 0
    ryanmanCounter = RyanmanCounter()
    for event in round["events"]:
        
        
        # so that we can track where in the events we are outside of this function
        
        match event["type"]:
            case "Dora":
                continue

        if( (event["player"] == player) ):
            
            #only tracking riichi player from here
            if(event["type"] == "Call"):
                turnCounter += 1
            elif(event["type"] == "Draw"):
                turnCounter += 1
                tile = event["tile"]
                hand.append(tile)
            elif(event["type"] == "Discard"):
                
                tile = event["tile"]
                hand.remove(tile)
                #need to add tiles to suji here
                if (isNumeric(tile)):
                    ryanmanCounter.updateRyanman(tile)
                    sujiTiles.extend(getSuji(tile))
                    genbutsuTiles.extend(getGenbutsu(tile))
                else:
                    continue
            else:
                #there needs to be something to account for Kan calls here... edge cases are a nightmare
                continue
            
        
        eventCount += 1
        
        if(turnCounter >= riichiTurn):
            #could remove dupes here for small efficiency bump
            numRyanmanAvailable = ryanmanCounter.ryanmanAvailable()
            return sujiTiles, genbutsuTiles, eventCount, numRyanmanAvailable

# works great 

def isNumeric(tile):
    return tile[0].isdigit()

class RyanmanCounter:
    def __init__(self):
        # FALSE MEANS
        self.ryanman = []
        for i in range(18):
            self.ryanman.append(True)

        
    def ryanmanAvailable(self):
        count = 0
        for i in range(18):
            if(self.ryanman[i]):
                count += 1

        return count
    
    def updateRyanman(self, tile):
        if(isNumeric(tile)):
            value = int(tile[0])
            suit = tile[1]
            suitShift = None
            match suit:
                case "m":
                    suitShift = 0
                case "p":
                    suitShift = 6
                case "s":
                    suitShift = 12
            if(value <= 3):
                self.ryanman[(value - 1) + suitShift] = False
            elif(value >= 7):
                self.ryanman[(value - 4) + suitShift] = False
            else:
                self.ryanman[(value - 4) + suitShift] = False
                self.ryanman[(value - 1) + suitShift] = False

class fileManager:

    #can only be called on list of dicts
    def makeCSV(data):
        keys = data[0].keys()
        with open('data.csv', 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            dict_writer.writerows(data)
    
    def makeTXT(data):
        with open('out.txt', 'w') as f:
            with redirect_stdout(f):
                print(data)

#def isSujiVulnerable(hand) -> bool:
#    hand.sort()

def dump(game):
    yaml.dump(game.asdata(), sys.stdout, default_flow_style=False, allow_unicode=True)

def main():
    dbName = "2018.db"
    limit = 1000
    
    #uncomment this to get things working
    #this is such bad object oriented work lol
    games = xmlToGames(dbName, limit)

    output = makeSujiTable(games, limit)

    #fileManager.makeTXT(output)
    fileManager.makeCSV(output)



    #gameData = game.asdata() #<- looks like a dictionary
    # rounds = gameData["rounds"]
    # round0 = rounds[0]
    # hands  = round0["hands"]
    # hand0 = hands[0]
    # simplifyHand(hand0)


# * GameData map / game.asdata
# 'suppress_draws' --- 
# 'lang' ---
# 'gameType' ---
# 'lobby' ---
# 'players' ---
# 'rounds' 
    # list rounds you need to index into
        # * round
        # 'dealer',
        # 'hands',
        #  'round',
        #  'agari',
        #  'events',
        #  'ryuukyoku',
        #  'ryuukyoku_tenpai',
        #  'reaches',
        #  'reach_turns',
        #  'turns',
        #  'deltas'
# 'owari' ---


    

if __name__ == "__main__":
    main()