INT=python3
DEBUG=pudb3

run:
	$(INT) Game.py -2p -p Heuristic Booger -n 10 -randomLayout
debug:
	$(DEBUG) Game.py -2p -p Heuristic Booger
