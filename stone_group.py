class StoneGroup:
    def __init__(self, x, y, field, processed_cells=None):
        self.field = field
        self.field_size = len(field)
        self.stones = []
        if processed_cells == None:
            processed_cells = [[0 for x in range(self.field_size)] for y in range(self.field_size)]
        self.__add_stones(field[x][y], x, y, processed_cells)

    def __str__(self):
        return str(self.stones)

    def __repr__(self):
        return str(self.stones)

    def __add_stones(self, target_color, x, y, processed_cells):
        color = self.field[x][y]
        print("color", target_color, color, processed_cells[x][y])
        if target_color == color and processed_cells[x][y] is not True:
            self.stones.append((x, y))
            processed_cells[x][y] = True
            if x - 1 >= 0:
                self.__add_stones(target_color, x - 1, y, processed_cells)
            if x + 1 < self.field_size:
                self.__add_stones(target_color, x + 1, y, processed_cells)
            if y - 1 >= 0:
                self.__add_stones(target_color, x, y - 1, processed_cells)
            if y + 1 < self.field_size:
                self.__add_stones(target_color, x, y + 1, processed_cells)

    def has_liberties(self, game):
        for x, y in self.stones:
            if game.stone_has_liberties(x, y):
                return True
        return False
