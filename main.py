# Idea:
# Normally (when in safe mode), you can't see the coins and the enemy can't see you
# When you press space, you can see the coins for five seconds, and the enemy can see you
# The more coins you have gathered, the faster the enemy will be (capped at 100ms per enemy move)
#
# When you exit through the door, a new map is generated
#
 
 
# Objective:
# Collect as many coins as possible and exit through the door while avoiding enemies
 
# Score tracker in top left
# When you see coins (dark_mode == True), there will be a timer until go back to safe mode (5 seconds)
import pygame
import random
 
# window specifications
# 720/480 = 12/8 (to make grid squares)
win_width = 720
win_height = 480
 
# grid specs
g_cols = 12
g_rows = 8
 
# colors
wall_color = (255, 255, 255)
bg_color = (50, 50, 50)
score_color = (0, 0, 255)
 
# timing  (frames)
dark_mode_duration_ms = 5000
 
 
class Coin:
    def __init__(self):
        self.img = pygame.image.load("coin.png")
        self.width = self.img.get_width()
        self.height = self.img.get_height()
 
class Player:
    def __init__(self):
        self.img = pygame.image.load("robot.png")
        self.height = self.img.get_height()
        self.width = self.img.get_width()
 
        # resize sprite to fit map
        self.img = pygame.transform.scale(self.img, (int(0.6*self.width), int(0.6*self.height)))
        self.height = self.img.get_height()
        self.width = self.img.get_width()
 
        self.x = 0
        self.y = win_height-self.height
 
class Enemy:
    def __init__(self):
        self.img = pygame.image.load("monster.png")
        self.height = self.img.get_height()
        self.width = self.img.get_width()
 
        # resize sprite to fit map
        self.img = pygame.transform.scale(self.img, (int(0.7*self.width), int(0.7*self.height)))
        self.height = self.img.get_height()
        self.width = self.img.get_width()
 
        self.x = 0
        self.y = 0
 
class Game:
    def __init__(self):
        pygame.init()
        # time
        self.ticks = 0
        self.enemy_move_delay_ms = 400
 
        # window and grid
        self.width, self.height = win_width, win_height
        self.cols, self.rows = g_cols, g_rows
 
        #sprites
        self.coin = Coin()
        self.player = Player()
        self.enemy = Enemy()
        self.exit_door = pygame.image.load("door.png")
 
        # initial game state
        self.score = 0
        self.dark_mode = False
        self.dark_mode_ends_at = 0
        self.last_enemy_move = 0
        self.state = 'title'
        
        # load highscore
        self.highscore = 0
        try:
            with open('highscore.txt', 'r') as f:
                self.highscore = int(f.read().strip())
        except:
            pass
        
        # font
        self.font = pygame.font.SysFont("arial", 24)
        
        # create first map
        self.new_map()
 
        # window 
        self.window = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Coin Escape")
        # pygame clock
        self.clock = pygame.time.Clock()
 
        self.main_loop()
 
    # helper for finding cells in map which are argument (0, 1 or 2 (wall, path or coin))
    def pos_with(self, number):
        positions = []
        for y in range(self.rows):
            for x in range(self.cols):
                if self.map[y][x] == number:
                    positions.append((x, y))
        return positions

    def save_highscore(self):
        with open('highscore.txt', 'w') as f:
            f.write(str(self.highscore))

    # helper for choosing random cell (used to place enemy)
    def random_path_cell(self, exclude=None):
        paths = self.pos_with(1)
        if exclude:
            paths = [p for p in paths if p not in exclude]
        if not paths:
            return None
        return random.choice(paths)
 
    def new_map(self):
        # 0 = wall
        # 1 = path
        # 2 = coin
 
        # bottom left is spawn
        # top right is exit
        # the paths in the middle are to ensure a level isn't impossible, so you can (technically) always lure the enemy to walk in a circle if you're fast enough
        self.map = [
            [0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        ]
 
        def random_points(map, amount):
            available_positions = self.pos_with(0)
            a = min(amount, len(available_positions))
            r_points = []
            n = 0
            while n < a:
                for (px, py) in available_positions:
                    if random.randint(0, 11) == 0:
                        map[py][px] = 1
                        r_points.append((px, py))
                        n += 1
                        if n >= a:
                            break
                if not r_points:
                    break
            return r_points
 
        def connect_points(map, points):
            for (sx, sy), (tx, ty) in zip(points, points[1:]):
                x, y = sx, sy
                while x != tx:
                    if tx > x:
                        x += 1
                    else:
                        x -= 1
                    map[y][x] = 1
                while y != ty:
                    if ty > y:
                        y += 1
                    else:
                        y -= 1
                    map[y][x] = 1
 
        def spawn_coins(map, amount):
            available_positions = self.pos_with(1)
            a = min(amount, len(available_positions))
            coin_points = []
            n = 0
            while n < a:
                for (px, py) in available_positions:
                    if random.randint(0, 11) == 0:
                        map[py][px] = 2
                        coin_points.append((px, py))
                        n += 1
                        if n >= a:
                            break
                if not coin_points:
                    break
            return coin_points
 
        # choose random points
        rpoints = random_points(self.map, 5)
        # add start and exit to points which should be connected
        rpoints.append((0, 7))
        rpoints.append((11, 0))
        # connect rpoints on map with path (path = 1)
        connect_points(self.map, rpoints)
        # spawn coins
        spawn_coins(self.map, 20)
 
        # player spawn
        self.player.x, self.player.y = 0, 7
        
        # place enemy on random path cell
        # exclude player spawn & exit & adjacent cells to player spawn
        exclude = {(self.player.x, self.player.y), (11, 0), (1, 7), (1, 6), (0, 6)}
        pos = self.random_path_cell(exclude=exclude)
        if pos:
            self.enemy.x, self.enemy.y = pos
        else:
            self.enemy.x, self.enemy.y = 1, 7
 
        # reset dark mode and timers
        self.dark_mode = False
        self.dark_mode_ends_at = 0
        self.last_enemy_move = self.ticks
 
    # helpers for movement
    def can_move_to(self, x, y):
        if 0 <= x < self.cols and 0 <= y < self.rows:
            return self.map[y][x] in (1, 2)
        return False
 
    def adjacent_path_cells(self, x, y):
        neighbors = []
        for dx, dy in ((1, 0),(-1, 0),(0, 1),(0, -1)):
            nx, ny = x+dx, y+dy
            if self.can_move_to(nx, ny):
                neighbors.append((nx, ny))
        return neighbors
 
    def enemy_take_step(self):
        now = self.ticks
        if now - self.last_enemy_move < self.enemy_move_delay_ms:
            return
        self.last_enemy_move = now
 
        ex, ey = self.enemy.x, self.enemy.y
        neighbors = self.adjacent_path_cells(ex, ey)
        if not neighbors:
            return
 
        if self.dark_mode:
            # if dark mode make enemy faster and faster when higher score
            if 300 - (5*self.score) <= 100:
                self.enemy_move_delay_ms = 100
            else:
                self.enemy_move_delay_ms = 300 - (5 * self.score)
            # Find shortest path to player
            best = []
            best_dist = abs(ex - self.player.x) + abs(ey - self.player.y)
            for nx, ny in neighbors:
                # loop through to find best choice in neighboring cells
                d = abs(nx - self.player.x) + abs(ny - self.player.y)
                if d < best_dist:
                    best_dist = d
                    best = [(nx, ny)]
                elif d == best_dist:
                    best.append((nx, ny))
            if best:
                # if there are best distances found, take a random step of those best 
                nx, ny = random.choice(best)
                self.enemy.x, self.enemy.y = nx, ny
                return
            # otherwise take random step
            nx, ny = random.choice(neighbors)
            self.enemy.x, self.enemy.y = nx, ny
        else:
            # when dark_mode == False, take random step, and enemy slower
            self.enemy_move_delay_ms = 400
            nx, ny = random.choice(neighbors)
            self.enemy.x, self.enemy.y = nx, ny
 
    # main loop
    def main_loop(self):
        while True:
            if self.state == 'title':
                button_rect = self.render_title()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if button_rect.collidepoint(event.pos):
                            self.state = 'playing'
                            self.new_map()
                pygame.display.flip()
                self.clock.tick(60)
                continue
            
            self.ticks += 1/60 * 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.try_move_player(self.player.x - 1, self.player.y)
                    elif event.key == pygame.K_RIGHT:
                        self.try_move_player(self.player.x + 1, self.player.y)
                    elif event.key ==pygame.K_UP:
                        self.try_move_player(self.player.x, self.player.y - 1)
                    elif event.key ==pygame.K_DOWN:
                        self.try_move_player(self.player.x, self.player.y +1)
 
                    elif event.key == pygame.K_SPACE:
                        self.dark_mode = True
                        self.dark_mode_ends_at = self.ticks + dark_mode_duration_ms
            
            # turn off dark mode after timer runs out
            if self.dark_mode and self.ticks >= self.dark_mode_ends_at:
                self.dark_mode = False
 
            # enemy movement
            self.enemy_take_step()
 
            #check collision with enemy
            if (self.enemy.x, self.enemy.y) == (self.player.x, self.player.y):
                self.score = 0
                self.new_map()
 
            self.render_window()
            self.clock.tick(60)
 
    def try_move_player(self, nx, ny):
        if self.can_move_to(nx, ny):
            self.player.x, self.player.y = nx, ny
            # pick up coin if in dark_mode
            if self.map[ny][nx] == 2 and self.dark_mode:
                self.score += 1
                self.map[ny][nx] = 1
 
            # if player gets to door generate new map
            if (nx, ny) == (11, 0):
                if self.score > self.highscore:
                    self.highscore = self.score
                    self.save_highscore()
                self.new_map()
                
    def render_title(self):
        self.window.fill(bg_color)
        title = self.font.render("Coin Escape", True, (255,255,255))
        self.window.blit(title, (self.width//2 - title.get_width()//2, 100))
        lines = [
            "Collect coins while avoiding the enemy!",
            "Press SPACE to see the coins for 5 seconds (but the enemy sees you too)",
            "Exit through the door to advance. The game will become progressively harder.",
            f"Highscore: {self.highscore}",
            "Click START to begin."
        ]
        y = 150
        for line in lines:
            text = self.font.render(line, True, (255,255,255))
            self.window.blit(text, (self.width//2 - text.get_width()//2, y))
            y += 30
        button_text = self.font.render("START", True, (0,0,0))
        button_rect = pygame.Rect(self.width//2 - 50, y + 20, 100, 40)
        pygame.draw.rect(self.window, (255,255,255), button_rect)
        self.window.blit(button_text, (button_rect.x + 50 - button_text.get_width()//2, button_rect.y + 20 - button_text.get_height()//2))
        return button_rect
                
    # rendering
    def render_window(self):
        # bg color depends on dark mode
        if not self.dark_mode:
            self.window.fill(bg_color)
        else:
            self.window.fill((0, 0, 0))
        # wall color depends on dark_mode
        if not self.dark_mode:
            wall_color = (255, 255, 255)
        else:
            wall_color = (100, 5, 5)
    
        cell_w = self.width / self.cols
        cell_h = self.height / self.rows
 
        # draw walls
        for y in range(self.rows):
            for x in range(self.cols):
                if self.map[y][x] == 0:
                    # make rect coordinates integers
                    rect = (
                        int(x * cell_w),
                        int(y * cell_h),
                        int(cell_w),
                        int(cell_h)
                    )
                    pygame.draw.rect(self.window, wall_color, rect)
                #draw coins if dark_mode
                if self.dark_mode and self.map[y][x] == 2:
                    self.window.blit(Coin().img, (x*cell_w + (cell_w - Coin().width)/2, y*cell_h + (cell_h - Coin().height)/2))

 
        #draw exit
        door_x = int(11 * cell_w + (cell_w - self.exit_door.get_width()) / 2)
        door_y = int(0 * cell_h + (cell_h - self.exit_door.get_height()) / 2)
        self.window.blit(self.exit_door, (door_x, door_y))
 
        #draw enemy
        ex = int(self.enemy.x * cell_w + (cell_w - self.enemy.width) / 2)
        ey = int(self.enemy.y * cell_h + (cell_h - self.enemy.height) / 2)
        self.window.blit(self.enemy.img, (ex, ey))
 
        # draw player
        px = int(self.player.x * cell_w + (cell_w - self.player.width) / 2)
        py = int(self.player.y * cell_h + (cell_h - self.player.height) / 2)
        self.window.blit(self.player.img, (px, py))
 
        # draw score
        score_img = self.font.render(f"Score: {self.score}", True, score_color)
        self.window.blit(score_img, (8, 6))

        # draw highscore
        highscore_img = self.font.render(f"Highscore: {self.highscore}", True, score_color)
        self.window.blit(highscore_img, (8, 6 + score_img.get_height() + 4))

        # draw timer if dark_mode
        if self.dark_mode:
            remaining_ms = max(0, self.dark_mode_ends_at - self.ticks)
            remaining_s = remaining_ms / 1000.0
            timer_img = self.font.render(f"{remaining_s:.1f}s", True, score_color)
            self.window.blit(timer_img, (8, 6 + score_img.get_height() + 4 + highscore_img.get_height() + 4))
 
        pygame.display.flip()
 
game = Game()