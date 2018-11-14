"""
analytics.py

started 8nov18

Class will hold different (dumb) analytic routines.
"""

from hlt import Position, Direction

from . import seek_n_nav
from . import myglobals as glo


class MapChunk:
    """
    Class will hold 5x5 grids comprising the primary map's data, with specific
    routines available to help plot courses through without wasting halite,
    determination on whether or not there is a shipyard or drop site available
    locally, etc.
    """

    Width = glo.Const.Max_Chunk_Width
    Height = glo.Const.Max_Chunk_Height

    x_start = -1
    y_start = -1

    # gotta use the list comprehension for arrays here I guess
    cell_data = [[0 for x in range(glo.Const.Max_Chunk_Width)] for y in range(glo.Const.Max_Chunk_Height)]

    # NOTE: we're not going to be using arrays to hold multiple shipyards or
    # dropoff points at this point, so if there's more than one we'll just
    # not bother with anything beyond the first
    has_shipyard = None
    has_dropoff = None

    def __init__(self, me, map, init_x, init_y):
        # NOTE: init will need to be run again after a shipyard or dropoff is
        # built within this chunk

        self.x_start = init_x
        self.y_start = init_y

        dropoffs = me.get_dropoffs()

        for x in range(0, self.Width - 1):
            for y in range(0, self.Height - 1):
                # determine halite amount
                self.cell_data[x][y] = map[Position(x + self.x_start, y + self.y_start)].halite_amount

                # structures?
                if Position(x + self.x_start, y + self.y_start).has_structure and not (self.has_shipyard and
                        self.has_dropoff):
                    # is it mine?
                    try:
                        for drop in dropoffs:
                            if drop.owner == me.id and (drop.position.x >= self.x_start and
                                  drop.position.x < (self.x_start + self.Width) and (drop.position.y >= self.y_start
                                  and drop.position.y < self.y_start + self.Height)):
                                # we have a drop
                                self.has_dropoff = True
                                break
                    except:
                        self.has_dropoff = False

                    if me.shipyard.position.x >= self.x_start and me.shipyard.position.x < (self.x_start + self.Width) \
                            and me.shipyard.position.y >= self.y_start and \
                            me.shipyard.position.y < (self.y_start + self.Height):
                        self.has_shipyard = True
                    else:
                        self.has_shipyard = False

                    if self.has_dropoff is None:
                        self.has_dropoff = False

    def mark_devoid_cells(self, ship, map):
        """
        Method goes through the cells in this particular chunk and, for this
        ship, marks them as 'unsafe' when they have no halite, in order to
        make naive_navigate() keep us in halite laden squares.

        NOTE: There will have to be a backup when no halite is present to give
        a path to percolate through.

        :param ship:
        :param map:
        :return:
        """
        for x in range(self.x_start, self.x_start + self.Width - 1):
            for y in range(self.y_start, self.y_start - self.Height):
                if map[Position(x, y)].halite_amount == 0:
                    map[Position(x, y)].mark_unsafe(ship)

    @staticmethod
    def create_centered_chunk(me, ship, map):
        return MapChunk(me, map, ship.position.x - (MapChunk.Width % 2), ship.position.y - (MapChunk.Height % 2))


class HaliteAnalysis:
    """
    Different static methods for analyzing the halite content of the map in
    general and in other non-MapChunk situations.
    """
    @staticmethod
    def find_best_dir(ship, game_map):
        """
        Method will use the ship's position to scan the 4 cardinal directions
        for the most profitable halite move.  Will return the direction.  Note
        that this will be taking into account whether or not that cell is
        currently occupied.

        :param ship:
        :param game_map:
        :return: Direction
        """
        halite_best = 0
        best_dir = seek_n_nav.Nav.generate_random_offset()

        glo.Misc.log_w_shid('seek', 'info', ship.id, "Entered analytics.HaliteAnalysis.find_best_dir()")

        for da_way in Direction.get_all_cardinals():
            glo.Misc.log_w_shid('seek', 'debug', ship.id, " - considering " +
                                str(ship.position.directional_offset(da_way)))

            if game_map[ship.position.directional_offset(da_way)].halite_amount > halite_best and \
                    game_map[ship.position.directional_offset(da_way)].is_empty:
                glo.Misc.log_w_shid('seek', 'debug', ship.id, " - * currently found " +
                                    str(ship.position.directional_offset(da_way)) + " to be best w/" +
                                    str(game_map[ship.position.directional_offset(da_way)].halite_amount) +
                                    " halite & empty")

                halite_best = game_map[ship.position.directional_offset(da_way)].halite_amount
                best_dir = da_way

        return best_dir

