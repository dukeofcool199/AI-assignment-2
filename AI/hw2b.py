import random
import sys

sys.path.append("./..")  # so other modules can be found in parent dir
# sys.path.insert(2,'..')
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *
from operator import attrgetter
import math

from Game import *


##
# AIPlayer
# Description: The responsbility of this class is to interact with the game by
# deciding a valid move based on a given game state. This class has methods that
# will be implemented by students in Dr. Nuxoll's AI course.
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
        super(AIPlayer, self).__init__(inputPlayerId, "Archie_Samson_Schrader")
        self.myFood = None
        self.isFirstTurn = None
        self.myConstr = None
        self.foodDist = None
        self.enemyFoodDist = None

        self.bestFoodConstr = None
        self.bestFood = None

    ##
    # getPlacement
    #
    # Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    # Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    # Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        self.isFirstTurn = True
        numToPlace = 0
        # implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:  # stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    # Choose any x location
                    x = random.randint(0, 9)
                    # Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    # Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        # Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:  # stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
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
            return [(0, 0)]

    ##
    # getMove
    # Description: Gets the next move from the Player.
    #
    # Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    # Return: The Move to be made
    ##
    def getMove(self, currentState):
        if self.isFirstTurn:  # calc food costs
            self.firstTurn(currentState)

        frontierNodes = []
        expandedNodes = []

        frontierNodes.append(StateNode(None,currentState,0,0,None))

        bn = None
        for x in range(5):
            bn = bestNode(frontierNodes)
            frontierNodes.remove(bn)
            expandedNodes.append(bn)
            frontierNodes.append(self.expandNode(bn))

        return parentMove(bn)

        # selectedMove = moves[random.randint(0, len(moves) - 1)];
        #
        # # don't do a build move if there are already 3+ ants
        # numAnts = len(currentState.inventories[currentState.whoseTurn].ants)
        # while (selectedMove.moveType == BUILD and numAnts >= 3):
        #     selectedMove = moves[random.randint(0, len(moves) - 1)];
        #
        # return selectedMove

    ##
    # firstTurn
    # Description: inits variables
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #
    #
    def firstTurn(self, currentState):
        inventory = getCurrPlayerInventory(currentState)
        tunnel = inventory.getTunnels()[0]
        hill = inventory.getAnthill()
        foods = getConstrList(currentState, None, (FOOD,))
        enemyInv = getEnemyInv(None, currentState)
        enemyTunnel = enemyInv.getTunnels()[0]
        enemyHill = enemyInv.getAnthill()

        minDist = 100000  # arbitrarily large

        for food in foods:
            tunnelDist = self.movesToReach(currentState, tunnel.coords, food.coords, WORKER)
            hillDist = self.movesToReach(currentState, hill.coords, food.coords, WORKER)
            if tunnelDist < minDist:
                minDist = tunnelDist
                self.bestFood = food
                self.bestFoodConstr = tunnel
            if hillDist < minDist:
                minDist = hillDist
                self.bestFood = food
                self.bestFoodConstr = hill

        self.foodDist = minDist
        self.isFirstTurn = False
        self.bestAligned = False
        self.alignmentAxis = None

        if self.bestFood.coords[0] == self.bestFoodConstr.coords[0]:
            self.bestAligned = True
            self.alignmentAxis = 'x'
        elif self.bestFood.coords[1] == self.bestFoodConstr.coords[1]:
            self.bestAligned = True
            self.alignmentAxis = 'y'

    ##
    # heuristicStepsToGoal
    # Description: Calculates the number of steps required to get to the goal
    # Most of this function's code is to prevent a stalemate
    # A tiny amount of it actually wins the game
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #
    #
    def heuristicStepsToGoal(self, currentState):
        # Get common variables
        me = currentState.whoseTurn
        workers = getAntList(currentState, me, (WORKER,))
        inventory = getCurrPlayerInventory(currentState)
        otherInv = getEnemyInv(None, currentState)
        anthillCoords = inventory.getAnthill().coords
        otherAnthillCoords = otherInv.getAnthill().coords
        foodLeft = FOOD_GOAL - inventory.foodCount

        # Special case
        if foodLeft == 0:
            return 0

        # Prevent a jam where we have no food or workers but keep killing Booger drones by having all units rush the anthill
        if inventory.foodCount == 0 and len(workers) == 0:
            return sum(map(lambda ant: self.movesToReach(currentState, ant.coords, otherAnthillCoords, ant.type),
                           inventory.ants))

        # State variables used to compute total heuristic
        adjustment = 0  # Penalty added for being in a board state likely to lose.
        wantWorker = True  # Whether we should see a bonus from having extra workers.
        # Lets us buy defense instead of workers when necessary

        # Unit variables
        drones = getAntList(currentState, me, (DRONE,))
        enemyWorkers = getAntList(currentState, 1 - me, (WORKER,))
        enemyFighters = getAntList(currentState, 1 - me, (DRONE, SOLDIER, R_SOLDIER))
        scaryFighters = list(filter(lambda fighter: fighter.coords[1] < 5, enemyFighters))
        soldiers = getAntList(currentState, me, (SOLDIER,))

        # If the other player is ahead on food or we have a drone, send a drone to kill workers
        if otherInv.foodCount > inventory.foodCount or len(drones) > 0:
            if len(enemyWorkers) > 0:
                if len(drones) == 0:
                    wantWorker = False
                    foodLeft += UNIT_STATS[DRONE][COST]
                    adjustment += sum(map(
                        lambda enemyWorker: self.movesToReach(currentState, anthillCoords, enemyWorker.coords, DRONE),
                        enemyWorkers))
                else:
                    adjustment += sum(map(
                        lambda enemyWorker: self.movesToReach(currentState, drones[0].coords, enemyWorker.coords,
                                                              DRONE), enemyWorkers))
            elif len(drones) > 0:
                # In this case, no reason to just have the drone lying around, so we charge the anthill
                # This cost needs to be negative so that the drone's cost does not go up by killing the last worker
                adjustment -= 1.0 / (
                        self.movesToReach(currentState, drones[0].coords, otherInv.getAnthill().coords, DRONE) + 1)

        # If there are enemy units in our territory, fight them and retreat workers and queen
        if len(scaryFighters) > 0:
            # We are going to increment adjustment by the number of moves necessary for a soldier
            # to reach all the enemy units
            # We are also going to give us a food alloance to buy the soldier
            start = None  # Start of movement paths
            if len(soldiers) == 0:
                wantWorker = False
                adjustment += len(scaryFighters)  # Penalty to incentivize buy
                foodLeft += UNIT_STATS[SOLDIER][COST]
                start = anthillCoords
            else:
                adjustment += len(scaryFighters)
                start = soldiers[0].coords
            adjustment += sum(
                map(lambda target: self.movesToReach(currentState, start, target.coords, SOLDIER), scaryFighters))

            # Retreat workers and queen
            # We ignore this once workers are dead b/c Booger stops playing so there is no longer reason to retreat
            # (and we will jam from perpetual retreat otherwise)
            if len(enemyWorkers) > 0:
                # Find squares under attack
                for enemy in enemyFighters:
                    for coord in listAttackable(enemy.coords,
                                                UNIT_STATS[enemy.type][MOVEMENT] + UNIT_STATS[enemy.type][RANGE]):
                        ant = getAntAt(currentState, coord)
                        # Gently encourage retreat
                        if ant != None and ant.player == me:
                            adjustment += 1 if ant.type == WORKER or ant.type == QUEEN else 0

                        # If anthill in danger, double soldier food allowance and make threatening enemy high priority
                        # Also, this prevents a jam where drone by anthill keeps killing worker while soldier
                        #   is busy killing the newly-spawned drones
                        # These penalties are arbitrary but seem to get the job done
                        if coord == anthillCoords:
                            if len(soldiers) == 0:
                                wantWorker = False
                                foodLeft += UNIT_STATS[SOLDIER][COST]
                            adjustment += self.movesToReach(currentState, enemy.coords, start,
                                                            SOLDIER) * 10  # Arbitrary to make the priority

        # Encourage soldiers to storm the anthill
        start = None
        if len(soldiers) > 0:
            start = soldiers[0].coords
        else:
            start = anthillCoords
        adjustment += self.movesToReach(currentState, start, otherAnthillCoords, SOLDIER)

        # We need a fake worker count to prevent dividing by zero
        # If we don't have a worker, we also allot a food alloance to buy one if we don't have defense units we were saving for
        workerCount = len(workers)
        if workerCount == 0 and wantWorker:
            foodLeft += UNIT_STATS[WORKER][COST]
            workerCount = 1

        # Prevent queen from jamming workers
        queen = inventory.getQueen()
        adjustment += 1.0 / (approxDist(queen.coords, self.bestFoodConstr.coords) + 1) + 1.0 / (
                    approxDist(queen.coords, self.bestFood.coords) + 1)

        # After all workers deliver food, how many trips from the construct to the food and back will we need to end the game
        foodRuns = foodLeft - len(workers)

        raw = 0  # Raw estimate assuming we do not have an opponent
        costs = []  # Cost of each worker to deliver food
        for worker in workers:
            raw += self.getWorkerPenalty(currentState, worker.coords)
            costs.append(self.getWorkerCost(currentState, worker.coords, worker.carrying))

        # First, calculate worker moves + end turns for all workers to deliver food
        if foodLeft < workerCount:
            sortedWorkers = sorted(costs)
            raw = sum(sortedWorkers[:foodLeft])
        elif len(workers) > 0:
            # The min cost here represents an estimated number of end turns
            raw = sum(costs) + min(costs)
        else:
            # Cost for our phantom worker to gather food
            raw = self.getWorkerCost(currentState, anthillCoords, False)

        # Now, calculate cost to complete all the necessary full trips to gather all food
        if foodRuns > 0:
            actions = self.getWorkerCost(currentState, inventory.getAnthill().coords, False, True) * foodRuns

            # Add actions plus estimated cost of end turns
            # To prevent incentivizing worker when we need defense, we prentend there is one worker for this calculation
            #   when we do not want a worker
            raw += actions + math.ceil(actions / workerCount) if wantWorker else 2 * actions

        # Max 1 food per turn, so we cannot go under the number of food remaining
        raw = max(raw, foodLeft)

        # Actual heuristic, accounting for cost from enemy winning
        # Casting to float makes the linter evaluate the return value correctly
        # (and makes our return value consistently float rather than occasionaly)
        return float(raw + adjustment)

    ## Finds the number of move actions it will take to reach a given destination
    def movesToReach(self, currentState, source, dest, unitType):
        taxicabDist = abs(dest[0] - source[0]) + abs(dest[1] - source[1])
        cost = float(taxicabDist) / UNIT_STATS[unitType][MOVEMENT]
        # Ceiling for workers creates a set of equidistant points they may choose between
        # Since the move to stay still is always the last in the list,
        # this encourages the worker to move between equidistant points when stuck
        # This repositioning helps clear up most worker jams so they will always gather food
        return cost if unitType != WORKER else float(math.ceil(cost))

    ##
    # getAttack
    # Description: Gets the attack to be made from the Player
    #
    # Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        # Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    # registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        # method templaste, not implemented
        pass

    ## Gets penalties for workers staying on a construct
    #  This penalty lets the ant go farther away from their target to leave the construct, helping to prevent jams
    def getWorkerPenalty(self, currentState, workerCoords):
        if workerCoords == self.bestFoodConstr.coords or workerCoords == self.bestFood.coords:
            return 1
        return 0

    ##
    # getWorkerCost
    # Params:
    #   currentState: game state
    #
    # Returns:
    #   the number of moves it will take for the worker to deliver a food plus penalties
    def getWorkerCost(self, currentState, workerCoords, carrying, isFakeAnt=False):
        cost = 0
        if carrying:
            cost = self.movesToReach(currentState, workerCoords, self.bestFoodConstr.coords,
                                     WORKER) + 1  # Plus one from the penalty for standing on a tunnel
            if not isFakeAnt:
                nextCoord = min(listAdjacent(workerCoords),
                                key=lambda dest: approxDist(dest, self.bestFoodConstr.coords))
                ant = getAntAt(currentState, nextCoord)
                if ant != None and not ant.carrying:
                    cost += 3  # Lets the other worker move out and back to prevent jam
        else:
            cost = self.movesToReach(currentState, workerCoords, self.bestFood.coords,
                     WORKER) + self.foodDist + 2  # Plus two from the penalty for standing on the food and tunnel
        return cost


    def expandNode(self,node):
        ## ensures the game does not continue if no moves can be made
        movements = listAllMovementMoves(node.state)
        builds = listAllBuildMoves(node.state)
        moves = builds + movements
        if len(movements) == 0:
            moves.append(Move(END))
            return
        gameStates = map(lambda move: (getNextState(node.state, move), move), moves)

        return list(map(lambda stateMove: StateNode(stateMove[1], stateMove[0], node.depth+1, \
                              self.heuristicStepsToGoal(stateMove[0]), node), gameStates))

class StateNode:
    def __init__(self, move, state, depth, heuristic, parent):
        self.move = move
        self.state = state
        self.depth = depth
        self.cost = heuristic + depth
        self.parent = parent

##
#   bestNode
# Param: list of nodes
# returns lowest cost node
def bestNode(nodes):
    # move = min(nodes, key=attrgetter('cost'))
    # return move

    if len(nodes) < 1:
        return nodes[0]
    else:
        bestNode = nodes[0]
        for node in nodes[1:]:
            if node.cost < bestNode.cost:
                bestNode = node

    return bestNode

##
#   parentMove()
# param(node with best move)
# returns move of the parent node of the node that had the best score
def parentMove(node):
    if node.depth == 1:
        return node.move
    else:
        return parentMove(node.parent)



###################################################################
#  Unit Testing
#
#
#
#
# Initialize needed objects
testPlayer = AIPlayer(0)
basicState = GameState.getBasicState()

foodConstr1 = Construction((3,3), FOOD)
foodConstr2 = Construction((3,4), FOOD)
basicState.inventories[NEUTRAL].constrs.append(foodConstr1)
basicState.inventories[NEUTRAL].constrs.append(foodConstr2)


# begin testing of methods
testPlayer.firstTurn(basicState) # test out init method
if testPlayer.bestFood.coords != (3,3) or testPlayer.bestFoodConstr.coords != (0,0) \
        or testPlayer.foodDist != 3.0:
    print("Error with firstTurn Initialization, Incorrect food or food Construction")

moveCost = testPlayer.movesToReach(basicState,(0,0),(0,2),WORKER)
if moveCost != 1.0:
    print("Error with movesToReach.  Value: " + moveCost + " Should be 1.0")


heuristic = testPlayer.heuristicStepsToGoal(basicState)
if heuristic != 9.0:
    print("Error with heuristicStepsToGoal.  Value: " + heuristic + " Should be 9.0")

workerCost = testPlayer.getWorkerCost(basicState,(0,1),False)
if workerCost != 8.0:
    print("Error with getWorkerCost.  Value: " + workerCost + " Should be 8.0")

workerPenalty = testPlayer.getWorkerPenalty(basicState,testPlayer.bestFoodConstr.coords)
if workerPenalty != 1:
    print("Error with workerPenalty.  Value: " + workerPenalty + " Should be 1")


##Test bestNode return from node list
workerBuild = Move(BUILD, [basicState.inventories[0].getAnthill().coords], WORKER)
queenMove = Move(MOVE_ANT, [basicState.inventories[0].getQueen().coords], None)

nextState1 = getNextState(basicState,queenMove)
nextState2 = getNextState(basicState,workerBuild)

nodeList = [StateNode(queenMove,basicState,0,testPlayer.heuristicStepsToGoal(nextState1),None)
    ,StateNode(workerBuild,basicState,0,testPlayer.heuristicStepsToGoal(nextState2),None)]

returnedNode = bestNode(nodeList)
if returnedNode.move.coordList != [(0,0)] or returnedNode.move.moveType != 0 or returnedNode.move.buildType != None:
    print("Error with bestNode Return")







