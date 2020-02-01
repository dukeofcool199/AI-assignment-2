# -*- coding: latin-1 -*-
import random
import sys

sys.path.append("..")  # so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import addCoords
from AIPlayerUtils import *


##
# AIPlayer
# Description: The responsbility of this class is to interact with the game by
# deciding a valid move based on a given game state. This class has methods that
# have been implemented by students in the AI course
#
# Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    # __init__
    # Description: Creates a new Player
    #
    # Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer, self).__init__(inputPlayerId, "HeuristicAI")
        # the coordinates of the agent's food and tunnel will be stored in these
        # variables (see getMove() below)
        self.myFood = None
        self.myTunnel = None

        #Number of each type of ant to spawn
        self.antList = {
                   "WORKER": 1,
                    "DRONE": 2,
                   "SOLDIER": 3
                   }

    ##
    # getPlacement
    #
    # The agent uses a hardcoded arrangement for phase 1
    #   Enemy food is placed randomly.
    #
    def getPlacement(self, currentState):
        self.myFood = None
        self.myTunnel = None
        if currentState.phase == SETUP_PHASE_1:
            return [(2, 2), (7, 2),
                    (1, 1), (2, 1), (3, 1), (1, 2), \
                    (1, 3), (2, 3), (3, 3), \
                    (2, 0), (3, 0)];
        elif currentState.phase == SETUP_PHASE_2:
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace): # uses the same random food placement as booger
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return None  # should never happen


    ##
    # getMove
    #
    # Our agent controls workers, drones and soldiers separately.
    # It will attack and continue spawning ants
    #
    ##
    def getMove(self, currentState):
        # asciiPrintState(currentState)
        # Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn

        # the first time this method is called, the food and tunnel locations
        # need to be recorded in their respective instance variables
        if (self.myTunnel == None):
            self.myTunnel = getConstrList(currentState, me, (TUNNEL,))[0]
        if (self.myFood == None):
            self.myFood = getConstrList(currentState, None, (FOOD,))

        antSpawn = self.spawnAnts(currentState,myInv,me)
        if antSpawn is not None:
            return antSpawn


        # move the drone(s) we have towards the workers and other soldiers
        droneMove = self.getDroneMove(currentState,me)
        if droneMove is not None:
            return droneMove


        soldierList = getAntList(currentState, me, (SOLDIER,))
        if (len(soldierList) > 0):
            soldierMove = self.soldierHelper(currentState, soldierList)
            if soldierMove is not None:
                return soldierMove


        workerList = getAntList(currentState, me, (WORKER,))
        if (len(workerList) > 0):
            tempMove = self.moveWorker(currentState, workerList)
            if tempMove is not None:
                return tempMove

        queenMove = self.moveQueen(currentState, myInv, me)
        if queenMove is not None:
            return queenMove


        # This should be the default behaviour if no other moves have already been returned
        return Move(END, None, None)

    ##
    # getDroneMove
    # Parameters:
    #   currentState: the current state of the game
    #   me: refernce variable to AIs playerid
    # moves the drones mainly to attack the worker ants, but it will attack whatever is closest
    def getDroneMove(self, currentState,me):
        player = currentState.whoseTurn
        drones = getAntList(currentState,me,(DRONE,) )
        enemyAnts = getAntList(currentState,1-me, (SOLDIER, WORKER, R_SOLDIER, DRONE,QUEEN))
        randomNum = random.randint(0,101)
        # chill out 25% of the time so it doesnt stale-mate itself
        if randomNum > 75:
            return None
        # if the list is empty then just chill out
        if enemyAnts == []:
            return None
        for drone in drones:
            if not (drone.hasMoved):
                # find the closest non queen ant and attack it
                closestDistance = stepsToReach(currentState, drone.coords, enemyAnts[0].coords)
                closestAnt = enemyAnts[0]
                for eAnt in enemyAnts:
                    newDistance = stepsToReach(currentState, drone.coords, eAnt.coords)
                    if newDistance < closestDistance:
                        closestDistance = newDistance
                        closestAnt = eAnt
                return Move(MOVE_ANT,createPathToward
                    (currentState,drone.coords,closestAnt.coords,UNIT_STATS[DRONE][MOVEMENT]))

    ##
    # moveQueen
    # Parameters:
    #   currentState: state of the game
    #   myInv: the AI's inventory
    #   me: the AI's PID
    #
    # Moves the Queen
    def moveQueen(self, currentState, myInv, me):
        # if the queen is on the anthill move her off
        myQueen = myInv.getQueen()
        if myQueen.coords == myInv.getAnthill().coords and not myQueen.hasMoved \
                or (myQueen.coords != (3,1) and not myQueen.hasMoved):
            return Move(MOVE_ANT, createPathToward(currentState,
                    myInv.getQueen().coords, (3, 1), UNIT_STATS[QUEEN][MOVEMENT]) , None)


        # move queen in place to attack
        if (not myQueen.hasMoved):
            return Move(MOVE_ANT, [myQueen.coords], None)

    ##
    # spawnAnts
    #
    # Parameters:
    #   currentState: state of the game
    #   myInv: the AI's inventory
    #   me: the AI's PID
    #
    # Spawns ants if there is enough food, and the number of ants are below the limits in
    # self.antList
    # Returns none if no available spawns
    def spawnAnts(self, currentState, myInv, me):
        legalBuilds = listAllBuildMoves(currentState)
        if len(legalBuilds) <1:
            return
        ants = getAntList(currentState, me, (WORKER, DRONE, SOLDIER, R_SOLDIER))

        antNums = {"WORKER":[0,any(a.buildType == WORKER for a in legalBuilds)],
                   "DRONE":[0,any(a.buildType == DRONE for a in legalBuilds)],
                   "SOLDIER":[0,any(a.buildType == SOLDIER for a in legalBuilds)],
                   "R_SOLDIER":[0,any(a.buildType == R_SOLDIER for a in legalBuilds)]}
        for ant in ants:
            antNums[antTypeToStr(ant.type)][0] += 1


        if (antNums["WORKER"][0] < self.antList["WORKER"]) and antNums["WORKER"][1]:
            return Move(BUILD, [myInv.getAnthill().coords], WORKER)
        elif (antNums["DRONE"][0] < self.antList["DRONE"]) and antNums["DRONE"][1]:
            return Move(BUILD, [myInv.getAnthill().coords], DRONE)
        elif (antNums["SOLDIER"][0] < self.antList["SOLDIER"]) and antNums["SOLDIER"][1]:
            return Move(BUILD, [myInv.getAnthill().coords], SOLDIER)

        else:
            return None


    ##
    # moveWorker
    # Parameters:
    #   currentState: game state
    #   workerList: list of worker ants owned by us
    #
    # Finds moves for worker ants
    # Assumes One Tunnel in player's inventory
    def moveWorker(self, currentState, workerList):
        inventory = getCurrPlayerInventory(currentState)
        for ant in workerList:
            if not ant.hasMoved:
                if(ant.carrying): # has food, move toward hill/tunnell, whichever is closer

                    target = self.findClosestTo(currentState,ant.coords,
                            ((inventory.getAnthill()).coords, (inventory.getTunnels())[0].coords))

                    path = createPathToward(currentState, ant.coords, target, UNIT_STATS[WORKER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)
                else: # get food
                    foodCoords = []
                    for food in self.myFood:
                        foodCoords.append(food.coords)

                    target = self.findClosestTo(currentState, ant.coords, foodCoords)

                    path = createPathToward(currentState, ant.coords, target, UNIT_STATS[WORKER][MOVEMENT])
                    return Move(MOVE_ANT, path, None)

    ##
    # findClosestTo
    #
    # Parameters:
    #   currentState: game state
    #   sourceCoords: Tuple of source Coordinates
    #   destCoordsList: List of Tuples of possible destinations
    # Returns the tuple of destination coordinates that is closer
    def findClosestTo(self, currentState, sourceCoords, destCoordsList):

        shortestCoord = (10000,()) #arbitrarily large cost
        for x in destCoordsList:
            dest = stepsToReach(currentState, sourceCoords, x)
            if shortestCoord[0] > dest:
                shortestCoord = (dest, x)
        return shortestCoord[1]

    ##
    # soldierHelper
    #
    # Parameters:
    #   CurrentState: current game state
    #
    # Returns a move for every soldier that we control

    def soldierHelper(self, currentState, soldierList):
        enemyInventory = getEnemyInv(None,currentState)
        enemyQueen = enemyInventory.getQueen()
        for soldier in soldierList:
            if not (soldier.hasMoved):
                # move Soldiers toward queen
                path = createPathToward(currentState, soldier.coords, enemyQueen.coords,
                                        UNIT_STATS[SOLDIER][MOVEMENT])
                return Move(MOVE_ANT,path,None)

    ##
    # getAttack
    # parameters:
    #   currentState: current state of the game
    #   attackingAnt: the ant that is attacking
    #   enemyLocations: locations of nearby enemy ants
    #
    # determines which ant to attack
    def getAttack(self, currentState, attackingAnt, enemyLocations):

        # if attackingAnt type is soldier, prioritize the queen
        if (attackingAnt.type == SOLDIER):
            for location in enemyLocations:
                returntype = getAntAt(currentState, location)
                if (returntype is not None):
                    if (returntype.type == QUEEN):
                        return location
        # otherwise don't care

        return enemyLocations[0]

    ##
    # registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        # method templaste, not implemented
        pass
