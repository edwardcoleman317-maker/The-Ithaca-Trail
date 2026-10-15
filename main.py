import pygame
import sys
import random
import math

# --- Constants & Setup ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
CRT_GREEN = (50, 255, 50)
GREEN = (0, 220, 0)
OLIVE_GREEN = (107, 142, 35)
RED = (255, 50, 50)
ORANGE = (255, 140, 0)
YELLOW = (255, 255, 0)
GOLD = (255, 215, 0)
BLUE = (50, 150, 255)
DARK_BLUE = (15, 15, 45)
BROWN = (139, 69, 19)
DARK_GREY = (30, 30, 30)
CYAN = (0, 255, 255)
PINK = (255, 182, 193)
GHOST_PURPLE = (180, 160, 230)
PURPLE = (128, 0, 128)

# Interior of the white animation frame (x, y, width, height)
FRAME = (53, 83, 694, 434)


def _mix(c1, c2, k):
    """Blend two colours; k=0 gives c1, k=1 gives c2."""
    k = max(0.0, min(1.0, k))
    return tuple(int(c1[i] + (c2[i] - c1[i]) * k) for i in range(3))


def _rot(pts, cx, cy, ang):
    """Rotate a list of points around (cx, cy)."""
    ca, sa = math.cos(ang), math.sin(ang)
    return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]


_star_rng = random.Random(11)
STAR_FIELD = [(_star_rng.randint(60, 740), _star_rng.randint(90, 330), _star_rng.randint(0, 20)) for _ in range(46)]


# ---------- The Slaughter of the Suitors (top-down battle, after Book 22) ----------
BT_L, BT_T, BT_R, BT_B = 70, 130, 730, 505          # the floor of the hall
BT_MAXHP = 7
BT_CIRCLES = [(250, 225, 17), (550, 225, 17), (250, 410, 17), (550, 410, 17), (400, 318, 28)]   # columns and the hearth
BT_TABLES = [(104, 288, 78, 48), (618, 288, 78, 48)]  # overturned feast tables: block movement, not arrows
BT_SPAWNS = [(110, 160), (250, 152), (400, 152), (550, 152), (690, 160), (692, 330), (110, 480),
             (250, 488), (400, 488), (550, 488), (690, 480), (140, 330)]
BT_SUITOR_COLS = [(120, 60, 160), (40, 110, 170), (190, 60, 60), (30, 130, 90), (210, 150, 40), (150, 60, 110), (60, 90, 150), (180, 100, 50)]
# 108 suitors came to Ithaca; Antinous is already dead, leaving 107: 15 + 17 + 22 + 24 + 18 + 11
BT_WAVES = [
    {"title": "WAVE 1", "sub": "The suitors have only their swords. They raise tables to ward off your arrows!",
     "spawn": [("sword", 14)], "first": ["eurymachus"], "tables": True},
    {"title": "WAVE 2", "sub": "Amphinomus rushes you with his sword while the others hide behind their tables!",
     "spawn": [("sword", 16)], "first": ["amphinomus"], "tables": True},
    {"title": "WAVE 3", "sub": "Melanthius fetches arms from the storeroom: shields, spears and helmets! Athena turns their first volley aside.",
     "spawn": [("sword", 17), ("armed", 1)], "named": ["demoptolemus", "euryades", "elatus", "peisander"], "athena": 5},
    {"title": "WAVE 4", "sub": "The second volley of spears flies, and Agelaus bellows for more!",
     "spawn": [("sword", 19), ("armed", 1)], "named": ["eurydamas", "amphimedon", "polybus", "ctesippus"]},
    {"title": "WAVE 5", "sub": "Athena lifts her aegis from the rafters, and terror seizes the suitors!",
     "spawn": [("armed", 1), ("panic", 12)], "named": ["agelaus", "leocritus"], "aegis": True},
    {"title": "FINAL WAVE", "sub": "They flee like cattle stung by gadflies, and fall like fish in a net.",
     "spawn": [("panic", 13)], "last": ["leodes"]},
]
# The suitors who fall in Book 22, in the order the poem gives. Exactly twelve are armed from the storeroom.
BT_NAMED = {
    "eurymachus": ("sword", "EURYMACHUS", 2), "amphinomus": ("sword", "AMPHINOMUS", 2),
    "demoptolemus": ("armed", "DEMOPTOLEMUS", 2), "euryades": ("armed", "EURYADES", 2), "elatus": ("armed", "ELATUS", 2), "peisander": ("armed", "PEISANDER", 2),
    "eurydamas": ("armed", "EURYDAMAS", 2), "amphimedon": ("armed", "AMPHIMEDON", 2), "polybus": ("armed", "POLYBUS", 2), "ctesippus": ("armed", "CTESIPPUS", 2),
    "agelaus": ("armed", "AGELAUS", 4), "leocritus": ("sword", "LEOCRITUS", 2), "leodes": ("leodes", "LEODES", 1),
}

# ---------- The three swords of the armory (all weapons of the Bronze Age world of the poem) ----------
# reach in pixels, arc in radians, cd = frames between swings, dmg = damage per hit, pierce = foes hit in a line
BT_SWORDS = [
    {"key": 0, "art": 4, "name": "Two Spears from the Storeroom", "reach": 82, "arc": 0.6, "cd": 16, "dmg": 1, "pierce": 2, "knock": 3.0, "heal": 0,
     "boost": "A long thrust that runs through two foes.",
     "lore": "Telemachus carried four shields, eight spears and four helmets from the storeroom. Odysseus took two spears for himself.",
     "stats": (5, 4, 2)},
    {"key": 1, "art": 3, "name": "A Suitor's Bronze Sword", "reach": 52, "arc": 2.0, "cd": 18, "dmg": 1, "pierce": 0, "knock": 5.0, "heal": 0,
     "boost": "A wide sweep that clears a crowd.",
     "lore": "The suitors wore sharp, double-edged bronze swords, like the one Eurymachus drew. The hall floor is strewn with them.",
     "stats": (3, 3, 3)},
]

# ---------- Weather and time of day while sailing ----------
SAIL_KINDS = {1: "dawn", 2: "storm", 3: "sunny", 4: "noon", 5: "overcast", 6: "sunset",
              7: "fog", 8: "night", 9: "dawn", 10: "overcast", 11: "noon"}
SAIL_SKIES = {
    "dawn":     {"top": (88, 104, 170), "bot": (255, 196, 150), "sun": (150, 345), "sun_col": (255, 214, 150), "cloud": (255, 214, 196), "n": 4, "tint": 0.05},
    "sunny":    {"top": (62, 146, 236), "bot": (186, 224, 250), "sun": (610, 110), "sun_col": (255, 250, 214), "cloud": (255, 255, 255), "n": 5, "tint": 0.0},
    "noon":     {"top": (44, 128, 232), "bot": (156, 210, 250), "sun": (400, 76), "sun_col": (255, 255, 228), "cloud": (255, 255, 255), "n": 3, "tint": 0.0},
    "sunset":   {"top": (84, 62, 134), "bot": (255, 150, 92), "sun": (620, 338), "sun_col": (255, 170, 90), "cloud": (255, 176, 126), "n": 5, "tint": 0.10},
    "overcast": {"top": (108, 118, 134), "bot": (176, 184, 194), "sun": None, "cloud": (150, 158, 172), "n": 9, "tint": 0.25},
    "storm":    {"top": (24, 30, 44), "bot": (82, 92, 110), "sun": None, "cloud": (46, 52, 66), "n": 10, "tint": 0.50, "rain": True, "bolt": True},
    "fog":      {"top": (150, 158, 170), "bot": (206, 210, 216), "sun": None, "cloud": (192, 196, 204), "n": 3, "tint": 0.30, "fog": True},
    "night":    {"top": (6, 8, 26), "bot": (32, 38, 80), "sun": None, "cloud": (38, 44, 72), "n": 4, "tint": 0.60, "stars": True},
}


# Length of each cutscene in frames (60 frames = 1 second). Anything not listed uses the length it is started with.
ANIM_LENGTHS = {
    "cicones_flee": 300,
    "lotus_drag": 300,
    "cyclops_stab": 300,
    "cyclops_escape_rams": 300,
}


class OdysseyPygame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("The Ithaca Trail")
        self.clock = pygame.time.Clock()
        
        # Retro Fonts
        self.font = pygame.font.SysFont('courier', 18, bold=True)
        self.title_font = pygame.font.SysFont('courier', 36, bold=True)
        self.small_font = pygame.font.SysFont('courier', 14, bold=True)

        # Screen shake offset
        self.shake_timer = 0
        self.shake_offset = (0, 0)

        self.reset_stats()
        
        # Intro Text
        self.intro_text = (
            "Sing to me of the man, Muse, the man of twists and turns, "
            "driven time and again off course, once he had plundered "
            "the hallowed heights of Troy. Many cities of men he saw "
            "and learned their minds, many pains he suffered, heartsick "
            "on the open sea, fighting to save his life and bring his "
            "comrades home."
        )
        self.intro_char_index = 0
        self.intro_timer = 0
        
        # Locations
        self.locations = [
            {"id": "troy", "name": "Coast of Troy", "text": "The war is over. Troy lies in ashes. It is time to go home.", "can_hunt": False, "x": 720, "y": 150},
            {"id": "cicones", "name": "Ismarus (Cicones)", "text": "You have landed at Ismarus.|1. Stay the night, slaughter sheep & drink.|2. Force the crew to leave at nightfall.", "can_hunt": False, "x": 660, "y": 280},
            {"id": "lotus", "name": "Lotus-Eaters", "text": "Locals offer your men a sweet, intoxicating flower.|1. Send scouts to investigate.|2. Sail past quickly without stopping.", "can_hunt": False, "x": 600, "y": 420},
            {"id": "cyclops", "name": "Cyclopes Isle", "text": "You are trapped in a cave with a giant!|1. Attempt to negotiate.|2. Offer him strong unmixed wine.", "can_hunt": True, "x": 520, "y": 300},
            {"id": "aeolus", "name": "Isle of Aeolia", "text": "King Aeolus gives you a bag of stormy winds.|1. Guard the bag yourself and don't let crew touch it.|2. Let the crew guard it.", "can_hunt": False, "x": 440, "y": 160},
            {"id": "laestrygonians", "name": "Laestrygonians", "text": "Giant cannibals inhabit this narrow fjord!|1. Send a scouting party inland.|2. Dock safely inside the harbor.", "can_hunt": False, "x": 380, "y": 280},
            {"id": "circe", "name": "Aeaea (Circe)", "text": "You land on Aeaea, home of Circe.|1. Send half of the men to investigate.|2. Hunt for food.", "can_hunt": True, "x": 320, "y": 420},
            {"id": "hades", "name": "House of Hades", "text": "You reach the edge of the world, entering the realm of the dead.|1. Listen to the dead.|2. Ignore the dead and sail on.", "can_hunt": False, "x": 280, "y": 500},
            {"id": "circe_return", "name": "Aeaea (Returning to Circe)", "text": "You return to Aeaea to bury Elpenor and hear Circe's warnings.", "can_hunt": False, "x": 250, "y": 380},
            {"id": "sirens", "name": "Sirens' Strait", "text": "You approach the island of the deadly Sirens!|1. Plug everyone's ears with beeswax.|2. Plug everyone's ears with beeswax and tie yourself to the mast.", "can_hunt": False, "x": 210, "y": 260},
            {"id": "scylla", "name": "Scylla & Charybdis", "text": "You must pass between two horrors!|1. Sail past Charybdis.|2. Sail past Scylla.", "can_hunt": False, "x": 160, "y": 360},
            {"id": "helios", "name": "Thrinacia (Cattle of Helios)", "text": "Unfavorable winds trap you here and food runs out!|1. Allow the men to eat the sacred cattle.|2. Make the men starve.", "can_hunt": False, "x": 120, "y": 230},
            {"id": "ogygia", "name": "Ogygia (Calypso's Isle)", "text": "You have washed ashore alone on Calypso's island.", "can_hunt": False, "x": 80, "y": 340},
            {"id": "phaeacia", "name": "Scheria (Phaeacians)", "text": "You have reached the land of the Phaeacians.", "can_hunt": False, "x": 130, "y": 460},
            {"id": "ithaca", "name": "Ithaca (Home)", "text": "You have reached your home!", "can_hunt": False, "x": 40, "y": 200}
        ]
        
        self.message = ""
        self.animal = None
        self.hunting_timer = 0
        self.crosshair_pos = (WIDTH//2, HEIGHT//2)
        self.arrows = []
        self.fallen_boar = None
        self.shot_age = 99
        self._hunt_bg = None
        self._hunt_fg = None
        self.anim_len = 180
        self.bt = None
        self._bt_bg = None
        self._bt_vig = None
        self._map_bg = None
        self._troy_bg = None
        self._troy_fires = []
        self._troy_torches = []
        self.sail_wave_col = BLUE
        self.sail_foam_col = WHITE
        self.mg_phase = "intro"
        self.mg_value = 0.0
        self.mg_tap = 0
        self.mg_timer = 0
        self.mg_attempts = 0
        self.mg_line = 0.5
        self.mg_dir = 1
        self.mg_gtop = 0.4
        self.mg_gh = 0.2
        self.mg_off = 0.0
        
        # UI Elements
        self.set_sail_button = pygame.Rect(WIDTH//2 - 100, HEIGHT - 110, 200, 50)
        
        # Animation Variables
        self.anim_timer = 0
        self.anim_type = ""

    def reset_stats(self):
        self.state = "INTRO"
        self.location_index = 0
        self.crew = 600
        self.ships = 12
        self.food = 15000
        self.hunted_here = False
        self.rations = "Filling" 
        self.ration_multiplier = 3
        self.intro_char_index = 0
        self.encounter_step = 0
        self.circe_after_hunt = False

    def wrap_line(self, line, font, max_width):
        if font.size(line)[0] <= max_width:
            return [line]
        stripped = line.lstrip(' ')
        indent = line[:len(line) - len(stripped)]
        # Hanging indent so wrapped menu options ("1. ...") line up neatly
        hang = indent + ('   ' if stripped[:2] in ('1.', '2.', '3.', '4.') else '')
        lines, cur, prefix = [], '', indent
        for word in stripped.split(' '):
            test = word if not cur else cur + ' ' + word
            if not cur or font.size(prefix + test)[0] <= max_width:
                cur = test
            else:
                lines.append(prefix + cur)
                prefix = hang
                cur = word
        lines.append(prefix + cur)
        return lines

    def draw_text(self, text, font, color, x, y, center=False, max_width=None):
        if max_width is None:
            if center:
                max_width = max(100, 2 * min(x, WIDTH - x) - 40)
            else:
                max_width = max(150, WIDTH - x - 40)
        lines = []
        for segment in text.split('|'):
            lines.extend(self.wrap_line(segment, font, max_width))
        for i, line in enumerate(lines):
            img = font.render(line, True, color)
            rect = img.get_rect()
            if center:
                rect.centerx = x
                rect.y = y + (i * (font.get_height() + 5))
            else:
                rect.topleft = (x, y + (i * (font.get_height() + 5)))
            self.screen.blit(img, rect)

    def draw_title_fit(self, text, color, x, y, center=False):
        """Single-line title that shrinks its font slightly if it would run off screen."""
        if not hasattr(self, "_fit_fonts"):
            self._fit_fonts = {}
        size = 36
        avail = (WIDTH - 40) if center else (WIDTH - 20 - x)
        while size > 14:
            if size not in self._fit_fonts:
                self._fit_fonts[size] = self.title_font if size == 36 else pygame.font.SysFont('courier', size, bold=True)
            font = self._fit_fonts[size]
            if font.size(text)[0] <= avail:
                break
            size -= 2
        img = font.render(text, True, color)
        rect = img.get_rect()
        if center:
            rect.centerx = x
            rect.y = y
        else:
            rect.topleft = (x, y)
        self.screen.blit(img, rect)

    def draw_wrapped_text(self, text, font, color, x, y, max_width):
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            fw, fh = font.size(' '.join(current_line))
            if fw > max_width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))
        
        for i, line in enumerate(lines):
            img = font.render(line, True, color)
            self.screen.blit(img, (x, y + (i * 30)))

    def advance_journey(self):
        food_consumed = self.crew * self.ration_multiplier
        self.food -= food_consumed
        if self.food < 0:
            self.food = 0
        
        self.location_index += 1
        self.hunted_here = False
        self.encounter_step = 0 
        
        if self.location_index >= len(self.locations) - 1:
            self.state = "VICTORY"
        else:
            self.state = "SAILING"
            self.hunting_timer = 240
            self.message = f"Sailing... Consumed {food_consumed} lbs of food."

    def trigger_animation(self, anim_type, duration=180):
        duration = ANIM_LENGTHS.get(anim_type, duration)
        self.state = "ANIMATION"
        self.anim_type = anim_type
        self.anim_timer = duration
        self.anim_len = duration

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if self.state == "INTRO":
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if self.intro_char_index < len(self.intro_text):
                        self.intro_char_index = len(self.intro_text)
                    else:
                        self.state = "TITLE"

            elif self.state == "TITLE":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.set_sail_button.collidepoint(event.pos):
                        self.state = "MENU"
                elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self.state = "MENU"

            elif self.state == "MENU":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1: 
                        self.advance_journey()
                    elif event.key == pygame.K_2: 
                        self.state = "MAP"
                    elif event.key == pygame.K_3: 
                        self.state = "RATIONS"
                    elif event.key == pygame.K_4: 
                        current_loc = self.locations[self.location_index]
                        if current_loc["can_hunt"] and not self.hunted_here:
                            self.state = "HUNTING"
                            self.hunting_timer = 600
                            self.animal = pygame.Rect(-64, random.randint(280, HEIGHT-100), 64, 36)
                            pygame.mouse.set_visible(False)
                        elif self.hunted_here:
                            self.message = "The game here is depleted."
                        else:
                            self.message = "No hunting available on the open sea."

            elif self.state in ["MAP", "RATIONS"]:
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if self.state == "RATIONS" and event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_1:
                            self.rations, self.ration_multiplier = "Filling", 3
                        elif event.key == pygame.K_2:
                            self.rations, self.ration_multiplier = "Meager", 2
                        elif event.key == pygame.K_3:
                            self.rations, self.ration_multiplier = "Bare Bones", 1
                    self.state = "MENU"

            elif self.state == "ANIMATION":
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    if self.anim_type not in ("drifting_ogygia", "odysseus_crying", "drifting_phaeacia", "phaeacian_voyage", "phaeacian_landing", "athena_disguise", "eumaeus_false_tale", "eumaeus_leaves", "athena_reveals", "odysseus_to_palace", "suitors_abuse", "penelope_contest", "suitors_fail", "odysseus_steps_up", "odysseus_shoots", "antinous_killed", "odysseus_proves_himself", "odysseus_laertes"):
                        self.anim_timer = 0

            elif self.state == "ENCOUNTER":
                if event.type == pygame.KEYDOWN:
                    current_loc = self.locations[self.location_index]
                    event_id = current_loc["id"]
                    
                    if event_id == "ogygia":
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                            if self.encounter_step == 0:
                                self.encounter_step = 1
                            elif self.encounter_step == 1:
                                self.message = "With a bronze axe from Calypso, you build a raft."
                                self.trigger_animation("raft_building", duration=540)

                    elif event_id == "phaeacia":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.told_story = False
                            self.message = "You accepted the gifts and left quickly."
                            self.trigger_animation("phaeacian_voyage", duration=480)
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.told_story = True
                            self.message = "You told your story, accepted the gifts, and left."
                            self.trigger_animation("phaeacian_voyage", duration=480)

                    elif event_id == "ithaca":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.encounter_step = 1
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.trigger_animation("eumaeus_false_tale", duration=540)
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_2, pygame.K_KP2):
                                self.trigger_animation("eumaeus_false_tale", duration=540)
                        elif self.encounter_step == 2:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.trigger_animation("eumaeus_leaves", duration=540)
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.encounter_step = 3
                        elif self.encounter_step == 3:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.trigger_animation("eumaeus_leaves", duration=540)

                    elif event_id == "cicones":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.crew -= 72
                                self.message = "Cicones reinforcements arrived! Lost 72 men."
                                self.trigger_animation("cicones_flee")
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.encounter_step = 1
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.crew -= 72
                                self.message = "Cicones reinforcements arrived! Lost 72 men."
                                self.trigger_animation("cicones_flee")
                            
                    elif event_id == "lotus":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.message = "Scouts ate the lotus! Dragged 3 men back."
                            self.trigger_animation("lotus_drag")
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.message = "You sailed past the danger."
                            self.state = "MENU"
                            
                    elif event_id == "cyclops":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.crew -= 2
                                self.message = "Negotiation failed! He ate 2 men."
                                self.encounter_step = 1
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.crew -= 2
                                self.message = "He ate 2 men, drank wine, and passed out."
                                self.encounter_step = 2
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_1, pygame.K_2, pygame.K_KP1, pygame.K_KP2):
                                self.message = "He drank the wine and fell asleep."
                                self.encounter_step = 2
                        elif self.encounter_step == 2:
                            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3):
                                self.message = "You blinded him with a burning olive stake!"
                                self.trigger_animation("cyclops_stab")
                        elif self.encounter_step == 3:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.crew -= 2
                                self.message = "The blind Cyclops blocks the door! 2 men die trying to run!"
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.message = "Escaping under the bellies of the rams!"
                                self.trigger_animation("cyclops_escape_rams")

                    elif event_id == "aeolus":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.message = "While you slept, the crew stole the bag and opened it! Violent winds blow you back to Aeolia."
                            self.trigger_animation("aeolus_winds")
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.message = "Crew opened the bag! Violent winds blow you back to Aeolia."
                            self.trigger_animation("aeolus_winds")

                    elif event_id == "laestrygonians":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.ships = 1
                                self.crew = 48
                                self.message = "Scouts ambushed! Giants hurled boulders, destroying 11 ships."
                                self.trigger_animation("laestrygonians_boulders")
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.encounter_step = 1
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_1, pygame.K_2, pygame.K_KP1, pygame.K_KP2):
                                self.ships = 1
                                self.crew = 48
                                self.message = "The harbor was a trap! Giants hurled boulders, destroying 11 ships."
                                self.trigger_animation("laestrygonians_boulders")

                    elif event_id == "circe":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.trigger_animation("circe_pigs")
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                if not self.hunted_here:
                                    self.state = "HUNTING"
                                    self.hunting_timer = 600
                                    self.animal = pygame.Rect(-64, random.randint(280, HEIGHT-100), 64, 36)
                                    pygame.mouse.set_visible(False)
                                    self.circe_after_hunt = True
                                else:
                                    self.message = "The game here is already depleted."
                        elif self.encounter_step == 5:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.trigger_animation("circe_pigs")
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_3, pygame.K_KP3, pygame.K_1, pygame.K_KP1):
                                self.trigger_animation("hermes_moly")
                        elif self.encounter_step == 2:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.message = "You accepted the Moly! Circe grants a full year of hospitality."
                                self.trigger_animation("circe_feast")
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.message = "Hermes forces you to take the Moly! Circe grants a full year of hospitality."
                                self.trigger_animation("circe_feast")

                    elif event_id == "hades":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.trigger_animation("hades_shades_rising")
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.shake_timer = 30
                                self.encounter_step = 1
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_1, pygame.K_KP1, pygame.K_2, pygame.K_KP2, pygame.K_SPACE, pygame.K_RETURN):
                                self.trigger_animation("hades_shades_rising")
                        elif self.encounter_step == 10:
                            self.encounter_step = 11
                        elif self.encounter_step == 11:
                            self.encounter_step = 12
                        elif self.encounter_step == 12:
                            self.encounter_step = 13
                        elif self.encounter_step == 13:
                            self.message = "Having honored the dead, you prepare to return to Circe's island."
                            self.state = "MENU"
                            self.encounter_step = 0

                    elif event_id == "circe_return":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.trigger_animation("elpenor_grave")
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3):
                                self.message = "Circe's warnings ring in your ears. You set sail."
                                self.state = "MENU"
                                self.encounter_step = 0

                    elif event_id == "sirens":
                        if event.key in (pygame.K_1, pygame.K_KP1):
                            self.message = "Passed the Sirens in silence with beeswax. 0 men lost!"
                            self.trigger_animation("sirens_singing")
                        elif event.key in (pygame.K_2, pygame.K_KP2):
                            self.message = "Tied to the mast, you heard the song without losing any men!"
                            self.trigger_animation("sirens_singing_tied")

                    elif event_id == "scylla":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.encounter_step = 1
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.crew = max(0, self.crew - 6)
                                self.message = "Scylla snatched 6 of your men, but everyone else survived!"
                                self.trigger_animation("scylla_attack")
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_2, pygame.K_KP2):
                                self.crew = max(0, self.crew - 6)
                                self.message = "Scylla snatched 6 of your men, but everyone else survived!"
                                self.trigger_animation("scylla_attack")

                    elif event_id == "helios":
                        if self.encounter_step == 0:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.food = 3000
                                self.message = "The men eat the sacred cattle and regain strength."
                                self.trigger_animation("lightning_strike")
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.trigger_animation("helios_eating_night")
                        elif self.encounter_step == 1:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.encounter_step = 2
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.trigger_animation("charybdis_fig_tree")
                        elif self.encounter_step == 2:
                            if event.key in (pygame.K_2, pygame.K_KP2):
                                self.trigger_animation("charybdis_fig_tree")
                        elif self.encounter_step == 3:
                            if event.key in (pygame.K_1, pygame.K_KP1):
                                self.encounter_step = 4
                            elif event.key in (pygame.K_2, pygame.K_KP2):
                                self.trigger_animation("charybdis_spit_raft")
                        elif self.encounter_step == 4:
                            if event.key in (pygame.K_2, pygame.K_KP2):
                                self.trigger_animation("charybdis_spit_raft")

            elif self.state == "HUNTING":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.shoot_arrow(event.pos)
                    if self.animal and self.animal.collidepoint(event.pos):
                        if self.arrows:
                            self.arrows[-1]["hit"] = True
                        self.fallen_boar = {"x": self.animal.x, "y": self.animal.y, "w": self.animal.width, "h": self.animal.height, "age": 0}
                        meat = random.randint(200, 500)
                        self.food += meat
                        self.message = f"Perfect strike! Gathered {meat} lbs of food."
                        self.animal = None
                        self.hunting_timer = 60
                        self.hunted_here = True
                        pygame.mouse.set_visible(True)

            elif self.state == "STRING_GAME":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if self.mg_phase == "intro":
                        self.mg_phase = "play"
                    elif self.mg_phase == "play":
                        self.mg_value = min(100.0, self.mg_value + 3.5)
                        self.mg_tap = 8
                        if self.mg_value >= 100.0:
                            self.mg_phase = "done"
                            self.mg_timer = 120

            elif self.state == "TIMING_GAME":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    if self.mg_phase == "intro":
                        self.new_aim_attempt(True)
                    elif self.mg_phase == "play":
                        self.mg_attempts += 1
                        lo, hi = self.mg_gtop, self.mg_gtop + self.mg_gh
                        self.mg_off = self.mg_line - (lo + hi) / 2.0
                        self.mg_timer = 80
                        self.mg_phase = "hit" if lo <= self.mg_line <= hi else "miss"

            elif self.state == "BATTLE":
                if event.type == pygame.KEYDOWN:
                    self.battle_keydown(event.key)

            elif self.state in ["GAME_OVER", "VICTORY"]:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    self.reset_stats()

    def update(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            self.shake_offset = (random.randint(-6, 6), random.randint(-6, 6))
        else:
            self.shake_offset = (0, 0)

        if self.state == "INTRO":
            self.intro_timer += 1
            if self.intro_timer % 2 == 0 and self.intro_char_index < len(self.intro_text):
                self.intro_char_index += 1

        elif self.state in ["MENU", "SAILING"]:
            current_loc_id = self.locations[self.location_index]["id"]
            if current_loc_id in ["ogygia", "phaeacia", "ithaca"]:
                if self.crew <= 0:
                    self.state = "GAME_OVER"
                    pygame.mouse.set_visible(True)
            elif current_loc_id == "helios":
                if self.crew <= 0:
                    self.state = "GAME_OVER"
                    pygame.mouse.set_visible(True)
            else:
                if self.crew <= 0 or self.food <= 0 or self.ships <= 0:
                    self.state = "GAME_OVER"
                    pygame.mouse.set_visible(True)
                
        if self.state == "SAILING":
            self.hunting_timer -= 1
            if self.hunting_timer <= 0:
                self.state = "ENCOUNTER"
                
        elif self.state == "ANIMATION":
            self.anim_timer -= 1
            if self.anim_timer <= 0:
                if self.anim_type == "cyclops_stab":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 3
                elif self.anim_type == "cyclops_escape_rams":
                    self.state = "MENU"
                    self.encounter_step = 0
                elif self.anim_type == "circe_pigs":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 1
                elif self.anim_type == "hermes_moly":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 2
                elif self.anim_type == "circe_feast":
                    self.trigger_animation("man_falls_roof")
                elif self.anim_type == "man_falls_roof":
                    self.state = "MENU"
                    self.encounter_step = 0
                    self.message = "After a year of hospitality, a crew member falls off the roof. You set sail."
                elif self.anim_type == "hades_shades_rising":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 10
                elif self.anim_type == "elpenor_grave":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 1
                elif self.anim_type in ["sirens_singing", "sirens_singing_tied"]:
                    self.state = "MENU"
                    self.encounter_step = 0
                elif self.anim_type == "scylla_attack":
                    self.state = "MENU"
                    self.encounter_step = 0
                elif self.anim_type == "helios_eating_night":
                    self.food = 3000
                    self.trigger_animation("lightning_strike")
                elif self.anim_type == "lightning_strike":
                    self.trigger_animation("shipwreck_drowning")
                elif self.anim_type == "shipwreck_drowning":
                    self.crew = 1
                    self.ships = 0
                    self.trigger_animation("charybdis_suck_raft")
                elif self.anim_type == "charybdis_suck_raft":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 1
                elif self.anim_type == "charybdis_fig_tree":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 3
                elif self.anim_type == "charybdis_spit_raft":
                    self.trigger_animation("drifting_ogygia", duration=540)
                elif self.anim_type == "drifting_ogygia":
                    self.location_index += 1
                    self.encounter_step = 0
                    self.food = 2000
                    self.ships = 0
                    self.crew = 1
                    self.message = "You washed ashore alone on Ogygia, island of Calypso."
                    self.trigger_animation("odysseus_crying", duration=420)
                elif self.anim_type == "odysseus_crying":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 0
                elif self.anim_type == "raft_building":
                    self.trigger_animation("drifting_phaeacia", duration=660)
                elif self.anim_type == "drifting_phaeacia":
                    self.location_index += 1
                    self.state = "ENCOUNTER"
                    self.encounter_step = 0
                    self.message = "You have reached Scheria, the land of the Phaeacians."
                elif self.anim_type == "phaeacian_voyage":
                    self.trigger_animation("phaeacian_landing", duration=480)
                elif self.anim_type == "phaeacian_landing":
                    self.location_index += 1
                    self.encounter_step = 0
                    self.trigger_animation("athena_disguise", duration=420)
                elif self.anim_type == "athena_disguise":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 0
                elif self.anim_type == "eumaeus_false_tale":
                    self.state = "ENCOUNTER"
                    self.encounter_step = 2
                elif self.anim_type == "eumaeus_leaves":
                    self.trigger_animation("athena_reveals", duration=540)
                elif self.anim_type == "athena_reveals":
                    self.trigger_animation("odysseus_to_palace", duration=480)
                elif self.anim_type == "odysseus_to_palace":
                    self.trigger_animation("suitors_abuse", duration=540)
                elif self.anim_type == "suitors_abuse":
                    self.trigger_animation("penelope_contest", duration=600)
                elif self.anim_type == "penelope_contest":
                    self.trigger_animation("suitors_fail", duration=600)
                elif self.anim_type == "suitors_fail":
                    self.trigger_animation("odysseus_steps_up", duration=480)
                elif self.anim_type == "odysseus_steps_up":
                    self.begin_string_game()
                elif self.anim_type == "odysseus_shoots":
                    self.trigger_animation("antinous_killed", duration=540)
                elif self.anim_type == "antinous_killed":
                    self.begin_battle()
                elif self.anim_type == "odysseus_proves_himself":
                    self.trigger_animation("odysseus_laertes", duration=540)
                elif self.anim_type == "odysseus_laertes":
                    self.encounter_step = 0
                    self.state = "VICTORY"
                else:
                    self.state = "MENU"
                    self.encounter_step = 0
                
        elif self.state == "HUNTING":
            self.crosshair_pos = pygame.mouse.get_pos()
            self.hunting_timer -= 1
            self.update_hunt_extras()
            
            if self.animal:
                self.animal.x += 8 
                if self.animal.x > WIDTH:
                    self.animal = None 
                    
            if not self.animal and self.hunting_timer > 60 and random.randint(1, 100) < 5:
                self.animal = pygame.Rect(-64, random.randint(280, HEIGHT-100), 64, 36)

            if self.hunting_timer <= 0:
                pygame.mouse.set_visible(True)
                if not self.hunted_here:
                    self.message = "The game escaped."
                    self.hunted_here = True
                if self.circe_after_hunt:
                    self.circe_after_hunt = False
                    self.state = "ENCOUNTER"
                    self.encounter_step = 5
                else:
                    self.state = "MENU"

        elif self.state == "STRING_GAME":
            self.mg_tap = max(0, self.mg_tap - 1)
            if self.mg_phase == "play":
                self.mg_value = max(0.0, self.mg_value - 0.25)
            elif self.mg_phase == "done":
                self.mg_timer -= 1
                if self.mg_timer <= 0:
                    self.begin_timing_game()

        elif self.state == "BATTLE":
            self.update_battle()

        elif self.state == "TIMING_GAME":
            if self.mg_phase == "play":
                self.mg_line += self.mg_dir * 0.013
                if self.mg_line >= 1.0:
                    self.mg_line, self.mg_dir = 1.0, -1
                elif self.mg_line <= 0.0:
                    self.mg_line, self.mg_dir = 0.0, 1
            elif self.mg_phase in ("hit", "miss"):
                self.mg_timer -= 1
                if self.mg_timer <= 0:
                    if self.mg_phase == "hit":
                        self.trigger_animation("odysseus_shoots", duration=600)
                    else:
                        self.new_aim_attempt(True)

    # ==================================================================
    #  ANIMATION TOOLKIT - shared drawing helpers for the cutscenes
    # ==================================================================
    def a_begin(self):
        ox, oy = self.shake_offset
        self.screen.set_clip(pygame.Rect(FRAME[0] + ox, FRAME[1] + oy, FRAME[2], FRAME[3]))

    def a_end(self):
        self.screen.set_clip(None)

    def a_rect(self, color, x, y, w, h, width=0):
        ox, oy = self.shake_offset
        pygame.draw.rect(self.screen, color, (int(x + ox), int(y + oy), max(1, int(w)), max(1, int(h))), width)

    def a_circle(self, color, x, y, r, width=0):
        ox, oy = self.shake_offset
        r = max(1, int(r))
        pygame.draw.circle(self.screen, color, (int(x + ox), int(y + oy)), r, min(width, r))

    def a_ellipse(self, color, x, y, w, h, width=0):
        ox, oy = self.shake_offset
        w = max(2, int(w))
        h = max(2, int(h))
        pygame.draw.ellipse(self.screen, color, (int(x + ox), int(y + oy), w, h), min(width, w // 2, h // 2))

    def a_line(self, color, x1, y1, x2, y2, width=1):
        ox, oy = self.shake_offset
        pygame.draw.line(self.screen, color, (int(x1 + ox), int(y1 + oy)), (int(x2 + ox), int(y2 + oy)), max(1, int(width)))

    def a_lines(self, color, pts, width=1):
        ox, oy = self.shake_offset
        pygame.draw.lines(self.screen, color, False, [(int(x + ox), int(y + oy)) for x, y in pts], max(1, int(width)))

    def a_poly(self, color, pts, width=0):
        ox, oy = self.shake_offset
        pygame.draw.polygon(self.screen, color, [(int(x + ox), int(y + oy)) for x, y in pts], width)

    def a_glow(self, x, y, r, color, strength=110):
        """Soft radial light (semi-transparent)."""
        ox, oy = self.shake_offset
        r = max(4, int(r))
        surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        steps = 7
        for i in range(steps):
            rr = max(1, int(r * (1 - i / float(steps))))
            a = max(0, min(255, int(strength * (i + 1) / float(steps))))
            pygame.draw.circle(surf, (color[0], color[1], color[2], a), (r, r), rr)
        self.screen.blit(surf, (int(x - r + ox), int(y - r + oy)))

    def a_fade(self, color, alpha):
        """Tint the whole frame (flashes, darkness)."""
        if alpha <= 0:
            return
        ox, oy = self.shake_offset
        surf = pygame.Surface((FRAME[2], FRAME[3]), pygame.SRCALPHA)
        surf.fill((color[0], color[1], color[2], max(0, min(255, int(alpha)))))
        self.screen.blit(surf, (FRAME[0] + ox, FRAME[1] + oy))

    def a_beam(self, pts, color, alpha):
        """A translucent polygon (sunbeams, light shafts)."""
        ox, oy = self.shake_offset
        surf = pygame.Surface((FRAME[2], FRAME[3]), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (color[0], color[1], color[2], max(0, min(255, int(alpha)))),
                            [(int(x - FRAME[0]), int(y - FRAME[1])) for x, y in pts])
        self.screen.blit(surf, (FRAME[0] + ox, FRAME[1] + oy))

    def a_title(self, text, color, y=100):
        """Scene title with a drop shadow, shrunk if needed so it stays inside the frame."""
        ox, oy = self.shake_offset
        if not hasattr(self, "_atitle_fonts"):
            self._atitle_fonts = {}
        size = 36
        while True:
            font = self._atitle_fonts.get(size)
            if font is None:
                font = self.title_font if size == 36 else pygame.font.SysFont('courier', size, bold=True)
                self._atitle_fonts[size] = font
            if font.size(text)[0] <= 664 or size <= 18:
                break
            size -= 2
        shadow = font.render(text, True, BLACK)
        img = font.render(text, True, color)
        rect = img.get_rect()
        rect.centerx = WIDTH // 2 + ox
        rect.y = y + oy
        self.screen.blit(shadow, (rect.x + 2, rect.y + 2))
        self.screen.blit(img, rect)

    # ---------- scenery ----------
    def a_sky(self, top, bottom, y0=83, y1=517, bands=16):
        h = (y1 + 14 - y0) / float(bands)   # runs a little past the horizon so wave troughs never show black
        for i in range(bands):
            self.a_rect(_mix(top, bottom, i / float(bands - 1)), FRAME[0], y0 + i * h, FRAME[2], h + 2)

    def a_stars(self, t, ymax=330):
        for sx, sy, ph in STAR_FIELD:
            if sy > ymax or (t // 12 + ph) % 5 == 0:
                continue
            c = 255 if ph % 3 else 190
            self.a_rect((c, c, 255 if ph % 2 else c), sx, sy, 2, 2)

    def a_moon(self, x, y, r=26):
        self.a_glow(x, y, r * 3, (200, 210, 255), 70)
        self.a_circle((236, 236, 212), x, y, r)
        self.a_circle((214, 214, 190), x - r * 0.3, y - r * 0.2, r * 0.2)
        self.a_circle((214, 214, 190), x + r * 0.35, y + r * 0.3, r * 0.15)

    def a_sea(self, y, base, crest, ticks, amp=6, deep=None, step=30, bottom=517):
        if deep is None:
            deep = _mix(base, (0, 0, 0), 0.45)
        for x in range(53, 747, step):
            wy = y + int(math.sin(x / 60.0 + ticks) * amp)
            w = min(step, 747 - x)
            seg = (bottom - wy) / 4.0
            for k in range(4):
                self.a_rect(_mix(base, deep, k / 3.0), x, wy + k * seg, w, seg + 1)
            self.a_rect(crest, x, wy, w, 3)

    def a_cloud(self, x, y, s, color):
        for dx, dy, r in ((0, 0, 26), (30, -10, 34), (66, 0, 28), (34, 10, 30), (-18, 8, 20), (88, 10, 20)):
            self.a_circle(color, x + dx * s, y + dy * s, r * s)

    def a_rain(self, t, n=40, color=(150, 175, 210), top=150, bottom=500):
        for i in range(n):
            x = (i * 131 + t * 9) % 694 + 53
            y = (i * 67 + t * 23) % (bottom - top) + top
            self.a_line(color, x, y, x - 5, y + 14, 1)

    def a_flame(self, x, y, w, h, t, seed=0):
        """Flickering fire; (x, y) is the centre of its base."""
        fl = 1.0 + math.sin(t * 0.45 + seed) * 0.15
        for col, sc in (((255, 100, 20), 1.0), ((255, 185, 40), 0.7), ((255, 245, 150), 0.4)):
            ww, hh = w * sc, h * sc * fl
            tip = math.sin(t * 0.3 + seed) * ww * 0.15
            self.a_poly(col, [(x - ww / 2, y), (x - ww / 4, y - hh * 0.55), (x + tip, y - hh), (x + ww / 4, y - hh * 0.5), (x + ww / 2, y)])

    def a_smoke(self, x, y, t, n=5, color=(80, 78, 84)):
        for i in range(n):
            u = ((t * 1.4 + i * 36) % 180) / 180.0
            self.a_glow(x + math.sin(u * 6 + i) * 14 + u * 26, y - u * 120, 8 + u * 20, color, int(110 * (1 - u)))

    def a_palm(self, x, y, h, sway):
        tx, ty = x + sway, y - h
        pts = [(x + (tx - x) * u + math.sin(u * 3) * 4, y - h * u) for u in (0, 0.25, 0.5, 0.75, 1.0)]
        self.a_lines((112, 80, 46), pts, 7)
        for k in range(7):
            ang = -math.pi / 2 + (k - 3) * 0.5
            tipx = tx + math.cos(ang) * 48
            tipy = ty + math.sin(ang) * 22 + 10 + abs(k - 3) * 7
            self.a_line((48, 128, 58), tx, ty, tipx, tipy, 5)
            self.a_line((96, 176, 84), tx, ty - 1, tipx, tipy - 1, 2)

    def a_lotus(self, x, y, s=1.0, t=0):
        sw = math.sin(t * 0.08) * 2
        self.a_ellipse((70, 140, 70), x - 14 * s, y - 3 * s, 28 * s, 9 * s)
        for k, (dx, dy) in enumerate(((-7, -8), (7, -8), (-3, -13), (3, -13), (0, -10))):
            self.a_ellipse((255, 165, 205) if k < 4 else (255, 210, 232), x + dx * s + sw - 4 * s, y + dy * s - 6 * s, 8 * s, 12 * s)
        self.a_circle((255, 220, 90), x + sw, y - 9 * s, 3 * s)

    def a_whirl(self, cx, cy, rx, t, squash=0.32, rings=9):
        """A funnel-shaped whirlpool seen from a low angle."""
        for k in range(rings):
            r = rx * (1 - k / float(rings))
            col = _mix((72, 132, 200), (3, 9, 28), k / float(max(1, rings - 1)))
            self.a_ellipse(col, cx - r, cy - r * squash + k * 3, 2 * r, 2 * r * squash)
        for arm in range(3):
            pts = []
            for j in range(26):
                u = j / 25.0
                ang = arm * 2.094 + u * 9.0 - t * 0.09
                r = rx * (1 - u * 0.92)
                pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r * squash + u * rings * 3 * 0.6))
            self.a_lines((205, 232, 255), pts, 2)

    def a_bolt(self, x0, y0, x1, y1, seed, width=3):
        rnd = random.Random(seed)
        pts = [(x0, y0)]
        n = 9
        for j in range(1, n):
            u = j / float(n)
            pts.append((x0 + (x1 - x0) * u + rnd.randint(-26, 26), y0 + (y1 - y0) * u))
        pts.append((x1, y1))
        self.a_lines((255, 235, 120), pts, width + 5)
        self.a_lines((255, 255, 255), pts, width)
        return pts

    # ---------- characters ----------
    def a_man(self, x, y, tunic=RED, f=1, step=0.0, lean=0, arms="down", s=1.0, skin=(236, 198, 158), helmet=True, hair=(80, 55, 38)):
        """Greek warrior. (x, y) = feet. f = facing (1 right / -1 left). Returns head position."""
        sk = max(2, int(3 * s))
        hip = y - 14 * s
        top = hip - 15 * s
        leg = (205, 165, 125)
        self.a_line(leg, x, hip, x - 4 * s + step, y, sk)
        self.a_line(leg, x, hip, x + 4 * s - step, y, sk)
        self.a_poly(tunic, [(x - 5 * s, hip + 2 * s), (x + 5 * s, hip + 2 * s), (x + 5 * s + lean, top), (x - 5 * s + lean, top)])
        self.a_line(_mix(tunic, (0, 0, 0), 0.45), x - 5 * s, hip, x + 5 * s, hip, max(1, int(2 * s)))
        sx, sy = x + lean * 0.9, top + 3 * s
        hx, hy = x + lean, top - 6 * s
        if arms == "up":
            hands = [(sx - 8 * s, top - 14 * s), (sx + 8 * s, top - 14 * s)]
        elif arms == "fwd":
            hands = [(sx + 11 * f * s, sy + 5 * s), (sx + 9 * f * s, sy + 9 * s)]
        elif arms == "pull":
            hands = [(sx - 11 * f * s, sy + 12 * s), (sx - 8 * f * s, sy + 15 * s)]
        elif arms == "cover":
            hands = [(hx - 6 * s, hy), (hx + 6 * s, hy)]
        elif arms == "none":
            hands = []
        else:
            hands = [(sx - 6 * s, hip - 2 * s), (sx + 6 * s, hip - 2 * s)]
        for hxn, hyn in hands:
            self.a_line(skin, sx, sy, hxn, hyn, max(2, int(2.5 * s)))
        if helmet:
            self.a_circle(skin, hx, hy, 5 * s)
            self.a_poly((205, 155, 60), [(hx - 5.5 * s, hy), (hx - 5 * s, hy - 4 * s), (hx, hy - 7.5 * s), (hx + 5 * s, hy - 4 * s), (hx + 5.5 * s, hy)])
            self.a_line(RED, hx, hy - 7.5 * s, hx - 3 * f * s, hy - 11 * s, max(1, int(2 * s)))
        else:
            self.a_circle(hair, hx, hy - 1.5 * s, 5.2 * s)
            self.a_circle(skin, hx, hy + 0.5 * s, 4.6 * s)
        return hx, hy

    def a_tumble(self, cx, cy, ang, tunic=RED, s=1.0):
        """A flailing figure rotated by `ang` (falls, shipwreck, being thrown)."""
        ca, sa = math.cos(ang), math.sin(ang)

        def rp(px, py):
            return (cx + (px * ca - py * sa) * s, cy + (px * sa + py * ca) * s)
        skin = (236, 198, 158)
        sh, hp = rp(0, -9), rp(0, 5)
        for foot in ((-6, 18), (8, 17)):
            fx, fy = rp(*foot)
            self.a_line((205, 165, 125), hp[0], hp[1], fx, fy, max(2, int(3 * s)))
        for hand in ((-10, -19), (10, -3)):
            hx, hy = rp(*hand)
            self.a_line(skin, sh[0], sh[1], hx, hy, max(2, int(2.5 * s)))
        self.a_line(tunic, sh[0], sh[1], hp[0], hp[1], max(3, int(8 * s)))
        head = rp(0, -16)
        self.a_circle(skin, head[0], head[1], 5 * s)

    def a_pig(self, x, y, t, f=1, s=1.0):
        bob = int(math.sin(t * 0.4 + x) * 1.5)
        body, dark = (240, 162, 174), (204, 120, 136)
        for k, dx in enumerate((-14, -7, 7, 14)):
            sw = int(math.sin(t * 0.5 + k * 1.6) * 2)
            self.a_rect(dark, x + (dx - 2) * s + sw, y - 9 * s, 4 * s, 9 * s)
        self.a_ellipse(body, x - 20 * s, y - 29 * s + bob, 40 * s, 24 * s)
        hx = x + 19 * f * s
        self.a_circle(body, hx, y - 21 * s + bob, 9 * s)
        self.a_ellipse(dark, hx + 8 * f * s - 4 * s, y - 20 * s + bob, 8 * s, 6 * s)
        self.a_poly(dark, [(hx - 2 * f * s, y - 29 * s + bob), (hx - 8 * f * s, y - 36 * s + bob), (hx + 2 * f * s, y - 31 * s + bob)])
        self.a_circle(BLACK, hx + 3 * f * s, y - 23 * s + bob, max(1, 1.5 * s))
        tx = x - 20 * f * s
        self.a_lines(dark, [(tx, y - 22 * s + bob), (tx - 5 * f * s, y - 28 * s), (tx - 2 * f * s, y - 32 * s), (tx - 7 * f * s, y - 34 * s)], 2)

    def a_cow(self, x, y, f=1, s=1.0, down=False):
        hide, patch = (244, 238, 214), (200, 170, 120)
        if down:
            self.a_ellipse(hide, x - 26 * s, y - 20 * s, 52 * s, 22 * s)
            self.a_ellipse(patch, x - 10 * s, y - 18 * s, 18 * s, 12 * s)
            self.a_line((120, 100, 80), x - 20 * s, y + 1 * s, x - 34 * s, y + 8 * s, 4)
            self.a_line((120, 100, 80), x + 18 * s, y + 1 * s, x + 34 * s, y + 6 * s, 4)
            self.a_circle(hide, x + 30 * f * s, y - 10 * s, 8 * s)
            return
        for dx in (-17, -8, 10, 19):
            self.a_rect((120, 100, 80), x + (dx - 2) * s, y - 14 * s, 4 * s, 14 * s)
        self.a_ellipse(hide, x - 26 * s, y - 38 * s, 52 * s, 28 * s)
        self.a_ellipse(patch, x - 8 * s, y - 36 * s, 18 * s, 14 * s)
        hx = x + 27 * f * s
        self.a_ellipse(hide, hx - 9 * s, y - 40 * s, 18 * s, 15 * s)
        self.a_ellipse((220, 170, 160), hx + 3 * f * s - 5 * s, y - 33 * s, 10 * s, 7 * s)
        self.a_line((235, 220, 170), hx - 2 * s, y - 40 * s, hx - 6 * s, y - 47 * s, 2)
        self.a_line((235, 220, 170), hx + 4 * s, y - 40 * s, hx + 8 * s, y - 47 * s, 2)
        self.a_line((200, 190, 170), x - 26 * f * s, y - 32 * s, x - 31 * f * s, y - 18 * s, 2)

    def a_ram(self, x, y, t, i=0):
        st = int(math.sin(t * 0.45 + i) * 3)
        # a crewman clings under the belly
        self.a_rect((205, 165, 128), x - 30, y - 14, 60, 7)
        self.a_circle((236, 198, 158), x + 34, y - 10, 5)
        self.a_line((205, 165, 128), x - 30, y - 11, x - 42, y - 4, 3)
        for dx in (-30, -18, 22, 34):
            self.a_rect((106, 92, 68), x + dx + (st if dx % 2 == 0 else -st), y - 18, 6, 18)
        self.a_ellipse((238, 234, 220), x - 42, y - 62, 84, 48)
        for k in range(6):
            self.a_circle((250, 248, 240), x - 32 + k * 13, y - 60 + (k % 2) * 3, 9)
        self.a_circle((206, 196, 172), x + 42, y - 48, 11)
        self.a_circle((30, 25, 20), x + 46, y - 51, 2)
        self.a_line((150, 118, 70), x + 36, y - 56, x + 28, y - 44, 3)
        self.a_circle((238, 234, 220), x - 44, y - 46, 6)

    def a_ship(self, x, y, t, s=1.0, sail=True, oars=True, bill=0, dark=0.0, broken=False):
        """Greek galley. (x, y) = left end of the deck line. s = scale. dark darkens it for night."""
        def c(col):
            return _mix(col, (4, 4, 14), dark)
        w = max(2, int(3 * s))
        hull = (122, 72, 32)
        if oars:
            for i in range(6):
                px = x + (22 + i * 20) * s
                sw = math.sin(t * 0.13 + i * 0.6) * 9 * s
                self.a_line(c((105, 66, 34)), px, y + 12 * s, px - 14 * s + sw, y + 46 * s, w)
        self.a_poly(c(hull), [(x, y), (x + 150 * s, y), (x + 126 * s, y + 27 * s), (x + 24 * s, y + 27 * s)])
        self.a_poly(c(_mix(hull, (0, 0, 0), 0.4)), [(x + 24 * s, y + 20 * s), (x + 126 * s, y + 20 * s), (x + 126 * s, y + 27 * s), (x + 24 * s, y + 27 * s)])
        self.a_poly(c(hull), [(x + 150 * s, y), (x + 173 * s, y - 15 * s), (x + 151 * s, y + 11 * s)])
        self.a_poly(c(hull), [(x, y), (x - 13 * s, y - 15 * s), (x + 9 * s, y)])
        for i in range(7):
            self.a_circle(c(GOLD if i % 2 else (170, 50, 40)), x + (16 + i * 19) * s, y + 5 * s, 5 * s)
        if sail:
            mx = x + 72 * s
            if broken:
                self.a_poly(c((84, 54, 26)), [(mx, y), (mx + 5 * s, y), (mx + 6 * s, y - 24 * s), (mx + 3 * s, y - 31 * s), (mx + 1 * s, y - 22 * s)])
            else:
                self.a_rect(c((84, 54, 26)), mx, y - 72 * s, 5 * s, 72 * s)
                b = bill * s
                self.a_poly(c((236, 226, 200)), [(mx + 5 * s, y - 68 * s), (mx + 31 * s + b, y - 64 * s), (mx + 58 * s, y - 62 * s),
                                                  (mx + 54 * s, y - 14 * s), (mx + 29 * s + b, y - 18 * s), (mx + 5 * s, y - 20 * s)])
                self.a_rect(c(RED), mx + 5 * s, y - 44 * s, 52 * s, 8 * s)

    def a_raft(self, x, y, s=1.0, man="sit"):
        """Small log raft. (x, y) = centre of the top surface."""
        for k in range(3):
            self.a_rect((130, 82, 40), x - 28 * s, y + k * 5 * s, 56 * s, 5 * s)
            self.a_rect((84, 50, 22), x - 28 * s, y + k * 5 * s + 4 * s, 56 * s, 1)
        self.a_rect((90, 58, 28), x + 12 * s, y - 34 * s, 3 * s, 34 * s)
        skin = (236, 198, 158)
        if man == "sit":
            self.a_rect(RED, x - 11 * s, y - 14 * s, 10 * s, 14 * s)
            self.a_circle(skin, x - 6 * s, y - 18 * s, 5 * s)
            self.a_line(skin, x - 4 * s, y - 10 * s, x + 4 * s, y - 5 * s, max(2, int(2.5 * s)))
        elif man == "lie":
            self.a_rect(RED, x - 10 * s, y - 9 * s, 26 * s, 9 * s)
            self.a_circle(skin, x - 15 * s, y - 5 * s, 5 * s)

    def a_ghost(self, x, y, h, t, alpha, seed=0):
        """Translucent shade. (x, y) = bottom centre of its hem."""
        w = int(h * 0.55)
        sw, sh = w + 16, int(h * 1.3)
        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        cx = sw // 2
        a = max(0, min(255, int(alpha)))
        col = (205, 200, 245, a)
        dk = (20, 10, 40, min(255, int(a * 1.3)))
        r = max(4, int(h * 0.16))
        top = 4
        hem = int(h * 0.95)
        body = [(cx - w // 2 + 4, top + int(h * 0.28)), (cx + w // 2 - 4, top + int(h * 0.28))]
        n = 7
        for k in range(n + 1):
            xk = cx + w // 2 - int(k * w / float(n))
            yk = top + hem + int(math.sin(t * 0.18 + k * 1.3 + seed) * 6) + (6 if k % 2 else 0)
            body.append((xk, yk))
        pygame.draw.polygon(surf, col, body)
        reach = int(math.sin(t * 0.1 + seed) * 6)
        pygame.draw.line(surf, col, (cx - w // 2 + 6, top + int(h * 0.34)), (cx - w // 2 - 6, top + int(h * 0.55) + reach), 5)
        pygame.draw.line(surf, col, (cx + w // 2 - 6, top + int(h * 0.34)), (cx + w // 2 + 6, top + int(h * 0.55) - reach), 5)
        pygame.draw.circle(surf, col, (cx, top + r), r)
        pygame.draw.circle(surf, dk, (cx - r // 2, top + r), max(1, r // 4))
        pygame.draw.circle(surf, dk, (cx + r // 2, top + r), max(1, r // 4))
        pygame.draw.circle(surf, dk, (cx, top + r + r // 2), max(1, r // 4))
        ox, oy = self.shake_offset
        self.screen.blit(surf, (int(x - cx + ox), int(y - top - hem + oy)))

    def a_siren(self, x, y, t, i):
        flap = math.sin(t * 0.25 + i * 2) * 10
        wing, wing2 = (60, 150, 150), (36, 104, 116)
        self.a_poly(wing, [(x - 6, y - 4), (x - 40, y - 24 - flap), (x - 32, y + 10), (x - 6, y + 14)])
        self.a_poly(wing, [(x + 6, y - 4), (x + 40, y - 24 - flap), (x + 32, y + 10), (x + 6, y + 14)])
        self.a_poly(wing2, [(x - 40, y - 24 - flap), (x - 54, y - 12 - flap), (x - 32, y + 2)])
        self.a_poly(wing2, [(x + 40, y - 24 - flap), (x + 54, y - 12 - flap), (x + 32, y + 2)])
        self.a_ellipse((126, 74, 156), x - 10, y, 20, 34)
        self.a_line((230, 190, 90), x - 5, y + 32, x - 8, y + 42, 2)
        self.a_line((230, 190, 90), x + 5, y + 32, x + 8, y + 42, 2)
        self.a_poly((50, 30, 70), [(x - 9, y - 22), (x + 9, y - 22), (x + 12, y + 8), (x - 12, y + 8)])
        self.a_rect((238, 200, 172), x - 5, y - 12, 10, 14)
        self.a_circle((238, 200, 172), x, y - 18, 8)
        self.a_ellipse((130, 30, 56), x - 3, y - 18, 6, 4 + int(abs(math.sin(t * 0.3 + i)) * 4))

    def a_wreck(self, x, y, k, s=1.0):
        """Broken ship. k: 0..1 how long ago it was struck; (x, y) = deck line, left end."""
        sink = k * 26 * s
        hull = (110, 66, 30)
        left = _rot([(x, y), (x + 40 * s, y), (x + 34 * s, y + 15 * s), (x + 12 * s, y + 15 * s)], x + 20 * s, y + 8 * s, -0.5 - k * 0.3)
        right = _rot([(x + 44 * s, y), (x + 82 * s, y), (x + 70 * s, y + 15 * s), (x + 50 * s, y + 15 * s)], x + 60 * s, y + 8 * s, 0.6 + k * 0.4)
        self.a_poly(hull, [(px, py + sink) for px, py in left])
        self.a_poly(hull, [(px, py + sink) for px, py in right])
        self.a_line((90, 60, 30), x + 36 * s, y + sink - 4 * s, x + 54 * s, y + sink - 40 * s, 3)
        self.a_poly((228, 218, 192), [(x + 40 * s, y + sink - 4 * s), (x + 74 * s, y + sink + 2 * s), (x + 62 * s, y + sink + 10 * s)])
        for d in range(4):
            self.a_line((120, 80, 40), x + (d * 22 - 6) * s, y + sink + (4 + d * 2) * s, x + (d * 22 + 16) * s, y + sink + (2 + d) * s, 3)

    # ==================================================================
    #  CUTSCENES
    # ==================================================================
    def anim_cicones_flee(self):
        D = getattr(self, "anim_len", 180)
        t = D - self.anim_timer
        p = t / float(D)
        self.a_begin()
        self.a_sky((70, 20, 25), (232, 128, 56), 83, 345)
        self.a_glow(170, 320, 170, (255, 140, 40), 120)
        # sea on the right
        self.a_rect((44, 70, 120), 330, 332, 417, 70)
        for x in range(330, 747, 30):
            self.a_rect((226, 156, 104), x, 332 + int(math.sin(x / 40.0 + t * 0.1) * 2), 30, 2)
        # beach
        self.a_poly((198, 166, 110), [(53, 345), (340, 345), (420, 396), (747, 396), (747, 517), (53, 517)])
        self.a_rect((174, 144, 94), 53, 462, 694, 55)
        # the burning city of Ismarus
        wall, dk = (114, 94, 76), (98, 80, 64)
        self.a_rect(wall, 53, 250, 260, 95)
        for bx in range(53, 313, 26):
            self.a_rect(wall, bx, 238, 14, 12)
        self.a_rect(dk, 120, 190, 50, 155)
        self.a_rect(dk, 240, 205, 46, 140)
        for bx in (120, 140, 160):
            self.a_rect(dk, bx, 178, 10, 12)
        for bx in (240, 258, 276):
            self.a_rect(dk, bx, 193, 10, 12)
        self.a_rect((40, 25, 20), 136, 215, 10, 22)
        self.a_rect((40, 25, 20), 256, 230, 10, 22)
        self.a_rect((30, 20, 15), 172, 295, 40, 50)
        self.a_circle((30, 20, 15), 192, 295, 20)
        self.a_flame(145, 178, 34, 66, t, 0)
        self.a_flame(263, 193, 30, 56, t, 2)
        self.a_flame(80, 238, 24, 44, t, 4)
        self.a_flame(205, 238, 30, 58, t, 1)
        self.a_smoke(145, 150, t)
        self.a_smoke(263, 165, t + 40)
        # our ship waiting in the shallows
        self.a_ship(585, 352 + math.sin(t * 0.12) * 2, t, 0.8)
        # arrows whistling overhead
        for k in range(4):
            u = ((t * 2.2 + k * 50) % 200) / 200.0
            ax = 150 + u * 560
            ay = 360 - math.sin(u * math.pi) * 130 + k * 8
            slope = -math.cos(u * math.pi) * 0.7
            self.a_line((60, 40, 25), ax, ay, ax - 14, ay - 14 * slope, 2)
            self.a_poly((225, 225, 235), [(ax + 4, ay + slope * 4), (ax - 4, ay - 3), (ax - 4, ay + 3)])
        # runners: our crew in front, the Cicones in pursuit
        actors = []
        for i in range(4):
            actors.append((445 + (i % 2) * 20, 0, i))
        for j in range(5):
            actors.append((440 + (j % 3) * 14, 1, j))
        for y, kind, i in sorted(actors):
            if kind == 0:
                x = 90 + p * 480 + i * 38
                tun = RED if i % 2 == 0 else (235, 235, 235)
                for k in range(3):
                    self.a_circle((216, 190, 142), x - 16 - k * 9, y - 3 - k, 5 - k)
                self.a_man(x, y, tun, 1, math.sin(t * 0.55 + i) * 6, 4, "down", 1.3)
            else:
                x = 20 + p * 410 + i * 34
                self.a_line((120, 90, 50), x - 5, y - 23, x + 36, y - 52, 3)
                self.a_poly((215, 215, 225), [(x + 34, y - 50), (x + 47, y - 58), (x + 37, y - 61)])
                self.a_man(x, y, (96, 60, 126), 1, math.sin(t * 0.5 + i * 2) * 6, 5, "fwd", 1.3)
        self.a_end()
        self.a_title("FLEEING THE CICONES!", RED)

    def anim_lotus_drag(self):
        D = getattr(self, "anim_len", 180)
        t = D - self.anim_timer
        p = t / float(D)
        ticks = t * 0.1
        self.a_begin()
        self.a_sky((90, 165, 230), (232, 244, 252), 83, 340)
        self.a_glow(130, 165, 100, (255, 255, 210), 130)
        self.a_circle((255, 250, 210), 130, 165, 28)
        self.a_poly((120, 175, 125), [(53, 345), (53, 300), (170, 262), (300, 312), (430, 268), (560, 318), (747, 282), (747, 345)])
        self.a_rect((70, 150, 190), 470, 332, 277, 100)
        for x in range(470, 747, 30):
            self.a_rect((205, 232, 250), x, 332 + int(math.sin(x / 40.0 + ticks) * 2), 30, 2)
        self.a_ship(560, 360 + math.sin(ticks) * 2, t, 0.9)
        self.a_poly((216, 192, 130), [(53, 345), (470, 345), (520, 428), (747, 428), (747, 517), (53, 517)])
        self.a_rect((192, 168, 110), 53, 482, 694, 35)
        self.a_palm(95, 405, 150, math.sin(ticks) * 6)
        self.a_palm(300, 385, 120, math.sin(ticks + 1) * 6)
        for i in range(9):
            self.a_lotus(80 + i * 70 + (i * 37) % 30, 395 + (i * 53) % 70, 1.0 + (i % 3) * 0.15, t + i * 7)
        # falling lotus petals
        for i in range(8):
            px = (i * 83 + t * 1.2) % 694 + 53 + math.sin(t * 0.1 + i) * 10
            py = 120 + (t * 1.6 + i * 47) % 300
            self.a_ellipse((255, 175, 215), px, py, 6, 4)
        # the entranced sailor is hauled back to the ship
        mx = 140 + p * 330
        self.a_line((178, 150, 98), 98, 460, mx - 40, 460, 4)
        for k in range(4):
            self.a_circle((224, 202, 152), mx - 46 - k * 11, 454 - k, 6 - k)
        self.a_glow(mx - 10, 447, 70, (255, 170, 225), 70)
        self.a_line((205, 165, 125), mx - 30, 457, mx - 54, 462 + math.sin(t * 0.3) * 2, 3)
        self.a_line((205, 165, 125), mx - 30, 457, mx - 52, 453, 3)
        self.a_rect((212, 82, 72), mx - 32, 450, 32, 12)
        self.a_circle((236, 198, 158), mx + 4, 455, 8)
        self.a_line((60, 40, 30), mx + 1, 454, mx + 7, 454, 1)
        self.a_lotus(mx + 12, 464, 0.7, t)
        for k, off in enumerate((38, 68)):
            self.a_man(mx + off, 464 - k * 3, RED if k == 0 else WHITE, 1, math.sin(t * 0.5 + k) * 5, 5, "pull", 1.25)
        self.a_end()
        self.a_title("DRAGGING MEN BACK TO THE SHIP", CRT_GREEN)

    def anim_cyclops_stab(self):
        D = getattr(self, "anim_len", 180)
        t = D - self.anim_timer
        p = t / float(D)
        hit = p >= 0.5
        self.a_begin()
        self.a_sky((16, 11, 9), (56, 40, 29))
        self.a_poly((32, 23, 17), [(53, 83), (53, 360), (120, 280), (170, 180), (130, 83)])
        self.a_poly((28, 20, 15), [(747, 83), (747, 300), (690, 230), (640, 120), (660, 83)])
        for sx in range(90, 720, 64):
            self.a_poly((38, 27, 20), [(sx, 83), (sx + 24, 83), (sx + 12, 83 + 26 + (sx * 7) % 38)])
        self.a_rect((78, 56, 38), 53, 440, 694, 77)
        self.a_rect((58, 41, 28), 53, 482, 694, 35)
        # campfire
        self.a_glow(135, 436, 160, (255, 140, 40), 100)
        self.a_line((90, 60, 30), 105, 446, 165, 436, 6)
        self.a_line((90, 60, 30), 105, 436, 165, 446, 6)
        self.a_flame(128, 440, 40, 64, t, 0)
        self.a_flame(146, 442, 26, 44, t, 2)
        # Polyphemus, sprawled out drunk
        jx = int(math.sin(t * 1.7) * 5) if (hit and p < 0.75) else 0
        hx, hy = 595 + jx, 400
        self.a_poly((140, 102, 76), [(640, 340), (747, 300), (747, 480), (600, 480)])
        self.a_circle((150, 112, 84), hx, hy, 88)
        self.a_poly((50, 34, 24), [(hx - 70, hy - 52), (hx - 40, hy - 100), (hx - 10, hy - 70), (hx + 20, hy - 104),
                                    (hx + 52, hy - 72), (hx + 84, hy - 90), (hx + 70, hy - 40)])
        self.a_ellipse((112, 80, 56), hx - 62, hy - 56, 110, 26)
        self.a_ellipse((130, 94, 68), hx - 10, hy - 4, 44, 36)
        ex, ey = hx - 23, hy - 8
        if not hit:
            self.a_ellipse((118, 84, 60), ex - 30, ey - 8, 60, 18)
            self.a_line((40, 26, 18), ex - 28, ey + 1, ex + 28, ey + 1, 3)
            self.a_line((70, 40, 28), hx - 36, hy + 50, hx + 24, hy + 54, 4)
            self.a_circle((225, 220, 205), hx - 52 + int(math.sin(t * 0.2) * 3), hy + 36, 4 + int(abs(math.sin(t * 0.1)) * 3), 1)
        else:
            self.a_ellipse((236, 232, 226), ex - 31, ey - 20, 62, 40)
            self.a_circle((200, 20, 20), ex, ey, 14)
            self.a_circle((90, 0, 0), ex, ey, 6)
            for d in range(3):
                self.a_line((190, 15, 15), ex - 14 + d * 14, ey + 18, ex - 14 + d * 14, ey + 30 + (t * 2 + d * 9) % 26, 3)
            self.a_ellipse((40, 12, 12), hx - 40, hy + 36, 70, 40)
            for k in range(4):
                self.a_rect((236, 230, 216), hx - 34 + k * 16, hy + 37, 9, 9)
        # the olive stake, heated in the fire, and the crew driving it home
        u = min(1.0, p / 0.5)
        tip = 250 + u * 300
        self.a_line((150, 112, 64), tip - 240, 392, tip, 392, 8)
        self.a_line((100, 72, 38), tip - 240, 395, tip, 395, 2)
        self.a_poly((40, 25, 15), [(tip - 24, 387), (tip, 392), (tip - 24, 397)])
        self.a_poly((255, 120, 30), [(tip - 10, 388), (tip + 12, 392), (tip - 10, 396)])
        self.a_glow(tip, 392, 44, (255, 150, 40), 140)
        for i in range(4):
            mx = tip - 70 - i * 52
            self.a_man(mx, 440, RED if i == 0 else (226, 226, 226), 1, 0 if hit else math.sin(t * 0.4 + i) * 3, 3, "up", 1.15)
        if hit:
            self.a_fade((255, 60, 20), 140 * max(0.0, 1 - (p - 0.5) * 7))
        self.a_end()
        self.a_title("BLINDING THE CYCLOPS!", RED)

    def anim_cyclops_escape_rams(self):
        D = getattr(self, "anim_len", 180)
        t = D - self.anim_timer
        p = t / float(D)
        self.a_begin()
        self.a_sky((18, 13, 10), (52, 38, 28))
        # the bright mouth of the cave
        self.a_ellipse((140, 202, 250), 380, 92, 420, 450)
        self.a_circle((255, 246, 192), 640, 190, 28)
        self.a_glow(640, 190, 80, (255, 245, 200), 90)
        self.a_ellipse((88, 160, 76), 430, 330, 330, 200)
        self.a_ellipse((66, 130, 60), 520, 350, 300, 200)
        self.a_poly((30, 21, 16), [(53, 83), (390, 83), (350, 140), (330, 250), (355, 330), (320, 517), (53, 517)])
        self.a_poly((30, 21, 16), [(380, 83), (747, 83), (747, 140), (700, 104), (560, 90), (430, 112), (390, 160)])
        for sx in range(60, 330, 60):
            self.a_poly((38, 27, 20), [(sx, 83), (sx + 26, 83), (sx + 13, 83 + 24 + (sx * 5) % 30)])
        self.a_rect((74, 54, 36), 53, 440, 694, 77)
        self.a_ellipse((112, 94, 62), 430, 452, 300, 40)
        # blinded Polyphemus guards the doorway
        skin = (148, 110, 82)
        self.a_poly((136, 100, 74), [(610, 330), (747, 300), (747, 517), (580, 517), (590, 420)])
        self.a_circle(skin, 690, 255, 74)
        self.a_poly((50, 34, 24), [(630, 215), (650, 168), (672, 195), (696, 160), (722, 196), (747, 175), (747, 225)])
        self.a_ellipse((112, 80, 56), 640, 220, 100, 22)
        self.a_ellipse((236, 232, 226), 655, 240, 56, 34)
        self.a_circle((170, 20, 20), 683, 257, 12)
        for d in range(3):
            self.a_line((190, 15, 15), 668 + d * 12, 272, 668 + d * 12, 286 + (t * 2 + d * 8) % 22, 3)
        self.a_ellipse((40, 12, 12), 650, 292, 64, 30)
        self.a_ellipse((130, 94, 68), 676, 262, 36, 30)
        # rams file out, each carrying a man clinging beneath its belly
        for i in range(4):
            rx = p * 1000 - 150 - i * 130
            if -90 < rx < 840:
                self.a_ram(rx, 440, t, i)
        hxp, hyp = 585, 372 + math.sin(t * 0.35) * 7
        self.a_line((142, 106, 78), 655, 330, hxp + 8, hyp - 4, 22)
        self.a_circle(skin, hxp, hyp, 18)
        for k in range(4):
            self.a_line(skin, hxp - 12 + k * 8, hyp + 10, hxp - 14 + k * 8, hyp + 30, 5)
        self.a_end()
        self.a_title("ESCAPING UNDER THE RAMS!", CRT_GREEN)

    def anim_aeolus_winds(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        ticks = t * 0.2
        self.a_begin()
        self.a_sky((34, 44, 70), (100, 116, 142))
        for i in range(5):
            cx = (i * 190 - t * 5) % 900 - 100
            self.a_cloud(cx, 185 + (i * 41) % 90, 1.0 + (i % 2) * 0.4, (70 + i * 6, 82 + i * 6, 106 + i * 6))
        # Aeolia, the floating isle ringed with a bronze wall
        sh = -(1 - p) * 120
        self.a_poly((92, 84, 78), [(53 + sh, 372), (53 + sh, 250), (120 + sh, 218), (190 + sh, 232), (250 + sh, 285), (290 + sh, 372)])
        self.a_rect((178, 130, 72), 70 + sh, 262, 190, 16)
        for k in range(7):
            self.a_line((120, 82, 40), 80 + k * 28 + sh, 262, 80 + k * 28 + sh, 278, 2)
        self.a_rect((208, 192, 162), 122 + sh, 232, 62, 30)
        self.a_poly((150, 80, 60), [(116 + sh, 232), (190 + sh, 232), (153 + sh, 208)])
        self.a_sea(388, (40, 70, 112), (196, 220, 244), ticks, 16, (10, 24, 50), 24)
        S = 1.3
        sx = 330 - p * 60
        sy = 360 + math.sin(ticks * 0.7) * 6
        self.a_ship(sx, sy, t, S, oars=False, bill=-18)
        # the crew, aghast, and the open bag of winds
        self.a_man(sx + 38 * S, sy, (225, 225, 225), 1, 0, 0, "up", 1.1)
        self.a_man(sx + 108 * S, sy, (170, 150, 70), 1, 0, 0, "up", 1.1)
        bx, by = sx + 70 * S, sy
        self.a_ellipse((160, 114, 66), bx - 18, by - 38, 36, 44)
        self.a_ellipse((50, 30, 15), bx - 13, by - 42, 26, 10)
        self.a_line((122, 82, 42), bx - 18, by - 28, bx - 32, by - 10, 2)
        self.a_glow(bx, by - 44, 46, (190, 235, 255), 130)
        for k in range(3):
            pts = []
            for j in range(24):
                u = j / 23.0
                ang = u * 7.0 - ticks * 1.5 + k * 2.1
                r = 6 + u * 70
                pts.append((bx + math.cos(ang) * r * 0.9 - u * 60, by - 44 - u * 130 + math.sin(ang) * r * 0.5))
            self.a_lines((212, 242, 255), pts, 3)
        # howling gale streaks
        for k in range(26):
            y = 150 + (k * 37) % 340
            x0 = 800 - ((k * 131 + t * (13 + (k % 4) * 4)) % 820)
            pts = [(x0 + j * 12, y + math.sin((x0 + j * 12) * 0.04 + ticks + k) * 6) for j in range(8)]
            self.a_lines((235, 248, 255) if k % 2 else (150, 205, 235), pts, 2)
        self.a_end()
        self.a_title("THE WINDS ARE UNLEASHED!", CYAN)

    def anim_laestrygonians_boulders(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        ticks = t * 0.1
        self.a_begin()
        self.a_sky((118, 40, 30), (218, 128, 72))
        self.a_glow(400, 300, 220, (255, 170, 80), 80)
        self.a_sea(392, (40, 62, 94), (214, 192, 172), ticks, 4, (12, 20, 38))
        self.a_poly((88, 74, 64), [(53, 83), (250, 83), (215, 210), (190, 330), (160, 517), (53, 517)])
        self.a_poly((88, 74, 64), [(747, 83), (560, 83), (600, 210), (630, 330), (660, 517), (747, 517)])
        for k in range(6):
            self.a_line((62, 52, 44), 70 + k * 24, 100 + k * 40, 120 + k * 24, 120 + k * 40, 3)
            self.a_line((62, 52, 44), 700 - k * 22, 100 + k * 40, 650 - k * 22, 125 + k * 40, 3)
        xs = [215, 300, 385, 470, 545]
        ys = [396, 404, 396, 404, 396]
        throws = [(0.04, 0, 0), (0.15, 1, 3), (0.26, 0, 1), (0.37, 1, 2), (0.52, 0, 4), (0.64, 1, 4)]
        impact = {}
        for s0, giant, tgt in throws:
            impact[tgt] = min(impact.get(tgt, 9.0), s0 + 0.2) if tgt < 4 else impact.get(tgt, 9.0)
        for i in range(5):
            bob = math.sin(ticks * 1.3 + i) * 2
            x = xs[i]
            if i == 4 and p > 0.5:
                x = xs[4] + (p - 0.5) * 520
            if i in impact and p >= impact[i]:
                k = min(1.0, (p - impact[i]) / 0.3)
                self.a_wreck(x, ys[i] + bob, k, 0.55)
            else:
                self.a_ship(x, ys[i] + bob, t, 0.55, oars=False)
                for q in range(3):
                    self.a_circle((236, 200, 160), x + (24 + q * 18) * 0.55 * 1.2, ys[i] + bob - 6, 3)
        # giants on the clifftops hurling rocks
        for gi, (gx, gdir) in enumerate(((150, 1), (645, -1))):
            holding = False
            for s0, giant, tgt in throws:
                if giant == gi and s0 - 0.08 <= p < s0:
                    holding = True
            self.a_man(gx, 250, (120, 90, 60), gdir, 0, 0, "up" if holding else "down", 2.6, helmet=False)
            if holding:
                self.a_circle((100, 94, 88), gx, 250 - 34 * 2.6 - 16, 15)
        for s0, giant, tgt in throws:
            u = (p - s0) / 0.2
            if 0 <= u < 1:
                gx, gdir = ((150, 1), (645, -1))[giant]
                tx = xs[tgt] + 24 if tgt < 4 else xs[4] + 20 + max(0.0, (s0 - 0.5)) * 520
                bx = gx + (tx - gx) * u
                by = 130 + (394 - 130) * u - math.sin(u * math.pi) * 90
                self.a_circle((92, 86, 80), bx, by, 14)
                self.a_circle((136, 128, 118), bx - 4, by - 4, 5)
        # splashes where boulders land
        for s0, giant, tgt in throws:
            k = (p - s0 - 0.2) / 0.14
            if 0 <= k < 1:
                tx = xs[tgt] + 24 if tgt < 4 else xs[4] + 20 + max(0.0, (s0 - 0.5)) * 520
                r = 10 + k * 46
                self.a_ellipse((226, 240, 250), tx - r, 396 - r * 0.25, 2 * r, r * 0.5, 2)
                for d in range(6):
                    ang = d * 1.05
                    self.a_line((226, 240, 250), tx + math.cos(ang) * r * 0.6, 396 - abs(math.sin(ang)) * r * 0.9, tx + math.cos(ang) * r * 0.8, 396 - abs(math.sin(ang)) * r * 1.3 - 10 * (1 - k), 2)
        self.a_end()
        self.a_title("GIANTS ATTACK WITH BOULDERS!", RED)

    def anim_circe_pigs(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((176, 146, 108), (222, 196, 154), 83, 390)
        # marble hall: columns, tapestry, torches
        for cx in (80, 330, 470, 720):
            self.a_rect((236, 228, 212), cx - 16, 150, 32, 250)
            self.a_rect((206, 196, 176), cx - 16, 150, 8, 250)
            self.a_rect((250, 244, 230), cx - 24, 140, 48, 14)
            self.a_rect((250, 244, 230), cx - 22, 392, 44, 12)
        self.a_rect((92, 38, 110), 360, 170, 80, 150)
        self.a_rect((220, 180, 70), 360, 170, 80, 150, 3)
        self.a_circle((220, 180, 70), 400, 245, 22, 3)
        for tx in (160, 640):
            self.a_rect((70, 50, 30), tx - 3, 250, 6, 40)
            self.a_glow(tx, 240, 70, (255, 160, 60), 90)
            self.a_flame(tx, 252, 14, 26, t, tx)
        self.a_rect((126, 100, 78), 53, 400, 694, 117)
        for row in range(5):
            self.a_rect((104, 80, 60), 53, 404 + row * 24, 694, 2)
        # Circe raises her wand
        self.a_poly((46, 26, 56), [(236, 285), (264, 285), (274, 352), (226, 352)])
        self.a_poly((124, 52, 156), [(208, 446), (292, 446), (268, 350), (232, 350)])
        self.a_rect((142, 62, 172), 236, 305, 28, 50)
        self.a_rect((226, 190, 70), 236, 340, 28, 4)
        self.a_line((240, 206, 170), 262, 318, 310, 285, 5)
        self.a_circle((240, 206, 170), 250, 292, 13)
        self.a_line((226, 190, 70), 238, 284, 262, 284, 3)
        self.a_line((226, 190, 70), 310, 285, 348, 252, 3)
        pulse = 130 + int(math.sin(t * 0.3) * 40)
        self.a_glow(348, 252, 34, (255, 120, 255), pulse)
        for k in range(10):
            ang = t * 0.1 + k * 0.63
            r = 26 + (k % 3) * 12
            sx, sy = 348 + math.cos(ang) * r, 252 + math.sin(ang) * r
            self.a_line((255, 200, 255), sx - 3, sy, sx + 3, sy, 1)
            self.a_line((255, 200, 255), sx, sy - 3, sx, sy + 3, 1)
        # her guests, one after another turned into swine
        for i in range(4):
            x = 440 + i * 62
            ts = 0.28 + i * 0.15
            if p < ts:
                self.a_man(x, 438, (230, 230, 230) if i % 2 else RED, -1, 0, -2, "up", 1.2)
            else:
                k = (p - ts) / 0.1
                if k < 1:
                    self.a_glow(x, 410, 50 + k * 30, (210, 90, 255), int(160 * (1 - k)))
                self.a_pig(x, 438, t + i * 9, -1, 1.2)
        self.a_end()
        self.a_title("CIRCE TURNS MEN INTO SWINE!", PINK)

    def anim_hermes_moly(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((26, 56, 46), (150, 190, 120), 83, 420)
        for tx, tw in ((70, 26), (190, 20), (610, 24), (720, 28)):
            self.a_rect((58, 40, 26), tx, 83, tw, 350)
        for cx, cy, r in ((70, 150, 70), (200, 140, 60), (620, 150, 66), (720, 160, 72), (130, 110, 60), (680, 110, 60), (400, 90, 50)):
            self.a_circle((22, 70, 40), cx, cy, r)
        self.a_beam([(430, 83), (500, 83), (380, 440), (250, 440)], (255, 240, 170), 36 + int(math.sin(t * 0.05) * 10))
        self.a_beam([(520, 83), (560, 83), (560, 440), (470, 440)], (255, 240, 170), 30)
        self.a_poly((64, 128, 60), [(53, 410), (747, 410), (747, 517), (53, 517)])
        self.a_rect((44, 98, 48), 53, 470, 694, 47)
        for g in range(30):
            gx = 60 + (g * 61) % 680
            gy = 420 + (g * 37) % 90
            self.a_line((96, 168, 84), gx, gy, gx + 3, gy - 8, 2)
        for fx in range(80, 740, 110):
            self.a_circle((255, 250, 235), fx, 470 + (fx % 30), 3)
        # fireflies
        for k in range(8):
            fx = 120 + k * 80 + math.sin(t * 0.07 + k) * 20
            fy = 300 + math.cos(t * 0.05 + k * 2) * 40
            self.a_glow(fx, fy, 8, (230, 255, 130), 160)
        # Odysseus waits, Hermes descends from the sky
        ox_ = 290
        self.a_man(ox_, 440, RED, 1, 0, 0, "fwd", 1.8, helmet=False)
        self.a_line((200, 200, 210), ox_ - 10, 412, ox_ - 28, 440, 3)
        u = max(0.0, min(1.0, p / 0.45))
        e = 1 - (1 - u) ** 3
        hx = 520
        hy = 215 + e * 215 + (math.sin(t * 0.1) * 3 if u >= 1 else 0)
        s = 1.7
        flap = math.sin(t * 0.5) * 6
        self.a_poly((70, 110, 220), [(hx - 4 * s, hy - 32 * s), (hx - 26 * s, hy - 8 * s + flap), (hx - 8 * s, hy - 4 * s)])
        self.a_line((235, 200, 90), hx + 18 * s, hy, hx + 18 * s, hy - 62 * s, 3)
        self.a_poly((235, 235, 245), [(hx + 18 * s, hy - 62 * s), (hx + 34 * s, hy - 70 * s), (hx + 22 * s, hy - 56 * s)])
        self.a_poly((235, 235, 245), [(hx + 18 * s, hy - 62 * s), (hx + 2 * s, hy - 70 * s), (hx + 14 * s, hy - 56 * s)])
        self.a_man(hx, hy, (80, 130, 230), -1, 0, 0, "fwd", s, helmet=False)
        self.a_ellipse((236, 202, 90), hx - 15 * s, hy - 40 * s, 30 * s, 8 * s)
        self.a_poly((236, 202, 90), [(hx - 6 * s, hy - 40 * s), (hx, hy - 50 * s), (hx + 6 * s, hy - 40 * s)])
        self.a_poly((255, 255, 255), [(hx - 4 * s, hy - 2 * s), (hx - 16 * s, hy - 10 * s + flap), (hx - 6 * s, hy + 1 * s)])
        self.a_poly((255, 255, 255), [(hx + 4 * s, hy - 2 * s), (hx + 16 * s, hy - 10 * s + flap), (hx + 6 * s, hy + 1 * s)])
        # the moly flower passes from god to hero
        handoff = max(0.0, min(1.0, (p - 0.55) / 0.25))
        fx = (hx - 18 * s) + ((ox_ + 16 * s) - (hx - 18 * s)) * handoff
        fy = (hy - 24 * s) + ((440 - 30 * s) - (hy - 24 * s)) * handoff
        if p < 0.45:
            fx, fy = hx - 18 * s, hy - 18 * s
        self.a_glow(fx, fy - 6, 34, (255, 235, 150), 130 + int(math.sin(t * 0.3) * 30))
        self.a_line((60, 140, 60), fx, fy, fx, fy + 16, 2)
        self.a_line((20, 20, 20), fx, fy + 16, fx - 4, fy + 24, 2)
        self.a_line((20, 20, 20), fx, fy + 16, fx + 4, fy + 24, 2)
        for k in range(5):
            ang = k * 1.256
            self.a_circle((255, 255, 250), fx + math.cos(ang) * 5, fy - 4 + math.sin(ang) * 5, 3)
        self.a_circle((255, 220, 90), fx, fy - 4, 2)
        self.a_end()
        self.a_title("HERMES BRINGS THE HOLY MOLY!", GOLD)

    def anim_circe_feast(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((150, 112, 80), (206, 170, 124), 83, 400)
        for cx in (90, 710):
            self.a_rect((226, 214, 190), cx - 18, 150, 36, 260)
            self.a_rect((244, 234, 212), cx - 26, 140, 52, 14)
        for tx in (170, 630):
            self.a_glow(tx, 250, 80, (255, 160, 60), 100)
            self.a_rect((70, 50, 30), tx - 3, 262, 6, 40)
            self.a_flame(tx, 264, 16, 30, t, tx)
        # an arched window that shows the seasons turning
        cyc = p * 6
        frac = cyc % 1.0
        day = int(cyc) % 2 == 0
        season = min(3, int(p * 4))
        sky = ((150, 205, 250), (110, 190, 255), (240, 190, 130), (205, 220, 240))[season]
        if not day:
            sky = (16, 18, 48)
        self.a_ellipse((110, 70, 40), 344, 142, 112, 66)
        self.a_rect((110, 70, 40), 344, 174, 112, 90)
        self.a_ellipse(sky, 350, 148, 100, 58)
        self.a_rect(sky, 350, 176, 100, 86)
        if day:
            self.a_circle((255, 230, 120), 360 + frac * 80, 250 - math.sin(frac * math.pi) * 58, 11)
        else:
            self.a_circle((230, 230, 205), 360 + frac * 80, 250 - math.sin(frac * math.pi) * 58, 8)
            for sx, sy in ((372, 190), (424, 184), (394, 214)):
                self.a_rect(WHITE, sx, sy, 2, 2)
        leaf = ((90, 190, 90), (40, 150, 60), (220, 130, 40), (230, 235, 245))[season]
        self.a_rect((90, 60, 30), 396, 226, 8, 36)
        self.a_circle(leaf, 400, 218, 20)
        self.a_circle(leaf, 387, 228, 13)
        self.a_circle(leaf, 413, 228, 13)
        self.a_rect((70, 50, 30), 398, 150, 4, 112)
        self.a_rect((70, 50, 30), 350, 218, 100, 4)
        # merry guests behind the long table
        for i in range(6):
            x = 110 + i * 105
            bob = math.sin(t * 0.22 + i * 1.3) * 4
            lift = abs(math.sin(t * 0.2 + i)) * 10
            self.a_rect(RED if i % 2 == 0 else (226, 226, 226), x - 15, 320 + bob, 30, 66)
            self.a_circle((236, 198, 158), x, 308 + bob, 11)
            self.a_circle((80, 55, 38), x, 302 + bob, 11)
            self.a_circle((236, 198, 158), x, 309 + bob, 9)
            self.a_line((236, 198, 158), x + 12, 340 + bob, x + 28, 308 - lift + bob, 5)
            self.a_rect(GOLD, x + 23, 292 + bob - lift, 10, 14)
        # the table: cloth, trim, food, and the hanging drape
        self.a_rect((228, 216, 192), 53, 384, 694, 28)
        self.a_rect((200, 160, 60), 53, 410, 694, 5)
        self.a_rect((238, 230, 210), 53, 415, 694, 58)
        for fx in range(80, 747, 46):
            self.a_rect((214, 202, 176), fx, 417, 3, 54)
        self.a_rect((200, 160, 60), 53, 470, 694, 5)
        self.a_rect((118, 92, 70), 53, 475, 694, 42)
        for fx in range(53, 747, 90):
            self.a_rect((96, 74, 54), fx, 475, 2, 42)
        for k in range(9):
            x = 80 + k * 76
            self.a_ellipse((248, 242, 228), x, 392, 44, 14)
            if k % 3 == 0:
                self.a_ellipse((196, 112, 52), x + 8, 387, 28, 14)
            elif k % 3 == 1:
                self.a_circle((120, 50, 130), x + 14, 393, 5)
                self.a_circle((120, 50, 130), x + 24, 392, 5)
                self.a_circle((200, 40, 50), x + 32, 394, 5)
            else:
                self.a_ellipse((210, 160, 80), x + 6, 388, 30, 10)
            self.a_rect(GOLD, x + 52, 384, 8, 14)
        self.a_end()
        self.a_title("A YEAR OF FEASTING AND REST...", GOLD)

    def anim_man_falls_roof(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((40, 28, 72), (244, 154, 92), 83, 440)
        self.a_glow(110, 300, 140, (255, 190, 100), 80)
        self.a_circle((255, 224, 146), 110, 300, 30)
        self.a_poly((72, 52, 96), [(53, 440), (53, 330), (180, 290), (300, 340), (480, 300), (640, 345), (747, 320), (747, 440)])
        self.a_rect((98, 124, 72), 53, 440, 694, 77)
        self.a_rect((72, 98, 52), 53, 482, 694, 35)
        # Circe's hall with its flat roof
        self.a_rect((228, 208, 172), 53, 250, 300, 190)
        self.a_rect((190, 168, 132), 53, 250, 300, 8)
        for wx in (90, 200, 290):
            self.a_rect((70, 52, 40), wx, 300, 24, 42)
        self.a_rect((90, 60, 40), 150, 380, 44, 60)
        self.a_rect((170, 92, 60), 53, 236, 310, 16)
        self.a_rect((120, 62, 40), 53, 232, 310, 5)
        self.a_ellipse((146, 80, 44), 282, 214, 16, 22)
        # Elpenor, drunk with wine, wanders to the edge
        if p < 0.35:
            x = 230 + p / 0.35 * 112
            self.a_man(x, 236, RED, 1, math.sin(t * 0.3) * 4, math.sin(t * 0.3) * 8, "up", 1.6, helmet=False)
        elif p < 0.45:
            k = (p - 0.35) / 0.1
            self.a_tumble(344 + k * 6, 209 + k * 4, k * 0.6, RED, 1.6)
        elif p < 0.8:
            u = (p - 0.45) / 0.35
            self.a_tumble(352 + u * 56, 209 + u * u * 215, 0.6 + u * 7.0, RED, 1.6)
        else:
            self.a_tumble(410, 424, 1.7, RED, 1.6)
            k = (p - 0.8) / 0.2
            for d in (-1, 0, 1):
                self.a_glow(410 + d * 26 * k, 440, 12 + k * 30, (206, 184, 144), int(120 * (1 - k)))
            if p > 0.88:
                kk = (p - 0.88) / 0.12
                self.a_ghost(410, 410 - kk * 90, 100, t, 130 * (1 - kk * 0.5))
        # his shipmates look on in horror
        for i, x in enumerate((480, 530, 580)):
            self.a_man(x, 452 - (i % 2) * 6, (226, 226, 226) if i % 2 else (176, 150, 70), -1, 0, 0, "up" if p > 0.45 else "down", 1.5)
        self.a_end()
        self.a_title("ELPENOR FALLS FROM THE ROOF!", RED)

    def anim_hades_shades_rising(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((8, 6, 22), (46, 40, 78), 83, 420)
        self.a_glow(600, 210, 90, (120, 110, 190), 60 + int(math.sin(t * 0.06) * 18))
        self.a_circle((176, 170, 210), 600, 210, 30)
        self.a_circle((196, 190, 226), 590, 202, 6)
        for tx in (90, 160, 250, 540, 690):
            h = 120 + (tx * 7) % 70
            self.a_poly((10, 8, 18), [(tx - 6, 420), (tx + 6, 420), (tx + 3, 420 - h), (tx - 3, 420 - h)])
            self.a_poly((10, 8, 18), [(tx, 420 - h * 0.55), (tx + 24, 420 - h * 0.85), (tx + 3, 420 - h * 0.6)])
        self.a_rect((26, 40, 62), 53, 380, 694, 50)
        for k in range(14):
            self.a_rect((86, 110, 160), 60 + (k * 53 + t) % 680, 386 + (k * 11) % 36, 40, 2)
        self.a_rect((30, 26, 46), 53, 428, 694, 40)
        shades = [(110, 0.05, 130), (215, 0.0, 150), (320, 0.12, 125), (480, 0.08, 140), (585, 0.0, 160), (685, 0.15, 125)]
        for i, (sx, delay, h) in enumerate(shades):
            rise = max(0.0, min(1.0, (p - delay) / 0.4))
            if rise <= 0:
                continue
            drift = (400 - sx) * 0.06 * rise
            self.a_ghost(sx + drift, 462 + (1 - rise) * h, h, t, 30 + rise * 130, i)
        self.a_rect((20, 16, 32), 53, 462, 694, 55)
        self.a_ellipse((110, 12, 18), 335, 470, 130, 30)
        self.a_ellipse((160, 24, 30), 350, 474, 100, 18)
        for k in range(10):
            fx = 80 + (k * 71 + t * (1 + k % 3)) % 640
            self.a_glow(fx, 440 - (t * 0.5 + k * 20) % 40, 26, (130, 120, 190), 50)
        # Odysseus stands guard with his sword over the pit
        self.a_man(230, 508, RED, 1, 0, 0, "fwd", 2.0, helmet=False)
        self.a_line((214, 214, 228), 252, 466, 316, 446, 4)
        self.a_end()
        self.a_title("THE SHADES OF THE DEAD RISE...", GHOST_PURPLE)

    def anim_elpenor_grave(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        ticks = t * 0.08
        self.a_begin()
        self.a_sky((70, 60, 120), (252, 170, 110), 83, 300)
        self.a_glow(620, 300, 150, (255, 190, 100), 110)
        self.a_circle((255, 226, 150), 620, 300, 34)
        self.a_sea(300, (70, 90, 150), (250, 200, 160), ticks, 3, (30, 40, 90))
        for k in range(6):
            w = 70 - k * 8 + math.sin(t * 0.2 + k) * 8
            self.a_rect((255, 215, 150), 620 - w / 2, 312 + k * 12, w, 2)
        self.a_poly((86, 112, 70), [(53, 517), (53, 392), (180, 362), (400, 352), (620, 362), (747, 392), (747, 517)])
        self.a_rect((70, 96, 58), 53, 484, 694, 33)
        self.a_poly((100, 126, 80), [(53, 440), (53, 392), (180, 362), (250, 372), (140, 440)])
        # smoke from the funeral pyre
        self.a_ellipse((50, 40, 36), 100, 446, 70, 14)
        self.a_smoke(135, 446, t, 4)
        # the burial mound grows, then the oar is planted and the stone set
        m = min(1.0, p / 0.35)
        self.a_ellipse((126, 92, 52), 280, 440 - 80 * m, 240, 40 + 40 * m)
        self.a_ellipse((148, 108, 62), 296, 442 - 80 * m, 208, 32 + 24 * m)
        if p > 0.35:
            k = min(1.0, (p - 0.35) / 0.25)
            top = 200 - (1 - k) * 120
            self.a_line((130, 88, 44), 400, top, 400, 372, 6)
            self.a_poly((150, 104, 52), [(388, top), (412, top), (406, top + 45), (394, top + 45)])
        if p > 0.6:
            k = min(1.0, (p - 0.6) / 0.2)
            dy = int((1 - k) * 40)
            self.a_rect((46, 46, 56), 288, 319 + dy, 224, 45)
            self.a_rect((92, 92, 106), 290, 315 + dy, 220, 45)
            self.a_rect((124, 124, 138), 290, 315 + dy, 220, 5)
            self.a_rect((200, 200, 212), 290, 315 + dy, 220, 45, 2)
            if k >= 1.0:
                self.draw_text("Here lies Elpenor", self.font, CRT_GREEN, WIDTH // 2 + self.shake_offset[0], 327 + self.shake_offset[1], center=True)
        for sx, sy, sw in ((262, 426, 30), (498, 430, 34), (322, 436, 22), (462, 438, 26)):
            self.a_ellipse((120, 118, 126), sx, sy, sw, sw * 0.6)
        # the mourners, heads bowed
        self.a_man(232, 456, (226, 226, 226), 1, 0, 4, "down", 1.6)
        self.a_man(184, 462, (176, 150, 70), 1, 0, 4, "down", 1.6)
        self.a_man(572, 456, (226, 226, 226), -1, 0, -4, "down", 1.6)
        self.a_man(620, 462, RED, -1, 0, -4, "fwd", 1.6, helmet=False)
        self.a_end()
        self.a_title("ELPENOR'S BURIAL RITES", GOLD)

    def _sirens_scene(self, tied):
        t = 180 - self.anim_timer
        p = t / 180.0
        ticks = t * 0.09
        self.a_begin()
        self.a_sky((92, 52, 122), (246, 152, 142), 83, 360)
        self.a_glow(210, 335, 140, (255, 200, 140), 110)
        self.a_circle((255, 226, 172), 210, 338, 34)
        self.a_sea(360, (62, 92, 152), (232, 204, 224), ticks, 5, (20, 30, 70))
        self.a_poly((72, 66, 84), [(550, 440), (620, 260), (700, 300), (780, 440)])
        self.a_poly((94, 86, 106), [(470, 440), (530, 320), (590, 440)])
        self.a_poly((50, 46, 62), [(620, 260), (650, 330), (700, 300)])
        for bx in range(480, 740, 34):
            self.a_line((236, 232, 220), bx, 428, bx + 8, 424, 2)
        for x in range(470, 747, 18):
            self.a_rect((238, 238, 248), x, 436 + int(math.sin(x / 9.0 + ticks * 2) * 2), 14, 4)
        for i, (sx, sy) in enumerate(((530, 300), (610, 240), (670, 280))):
            self.a_siren(sx, sy, t, i)
        # the ship of Odysseus glides toward the strait
        S = 1.3
        shx = 40 + p * 170
        shy = 402 + math.sin(ticks * 1.3) * 4
        self.a_ship(shx, shy, t, S, bill=6)
        for i in range(5):
            px = shx + (30 + i * 20) * S
            self.a_rect((120, 120, 150), px - 5, shy - 12, 10, 12)
            self.a_circle((236, 198, 158), px, shy - 18, 5)
            self.a_circle(WHITE, px - 5, shy - 18, 1)
            self.a_circle(WHITE, px + 5, shy - 18, 1)
        mx = shx + 84 * S
        lean = (6 + math.sin(t * 0.5) * 4) if tied else 0
        hx, hy = self.a_man(mx, shy, RED, 1, 0, lean, "fwd" if tied else "cover", 1.6, helmet=False)
        self.a_circle(WHITE, hx - 7, hy, 2)
        self.a_circle(WHITE, hx + 7, hy, 2)
        if tied:
            for k in range(3):
                self.a_line((190, 150, 60), mx - 10, shy - 42 + k * 9, mx + 10 + lean, shy - 36 + k * 9, 3)
        # drifting notes of the song
        for i in range(5):
            u = ((t * 1.6 + i * 36) % 180) / 180.0
            nx = 560 - u * (560 - (shx + 110))
            ny = 280 + math.sin(u * 9 + i) * 20 + u * 100
            col = CYAN if i % 2 else PINK
            self.a_ellipse(col, nx - 7, ny - 4, 14, 10)
            self.a_line(col, nx + 6, ny - 1, nx + 6, ny - 26, 3)
            self.a_poly(col, [(nx + 6, ny - 26), (nx + 16, ny - 18), (nx + 6, ny - 16)])
        self.a_end()
        self.a_title("THE SIRENS' ENCHANTING SONG", PINK)
        if tied:
            self.draw_text("BOUND TO MAST", self.small_font, GOLD, int(hx) + self.shake_offset[0], int(shy - 118) + self.shake_offset[1], center=True)

    def anim_sirens_singing(self):
        self._sirens_scene(False)

    def anim_sirens_singing_tied(self):
        self._sirens_scene(True)

    def anim_scylla_attack(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        ticks = t * 0.1
        self.a_begin()
        self.a_sky((72, 42, 62), (172, 92, 82), 83, 380)
        self.a_sea(380, (36, 62, 100), (192, 206, 226), ticks, 5, (10, 20, 40))
        self.a_whirl(655, 440, 120, t, 0.28, 6)
        # Scylla's cliff and cave
        self.a_poly((86, 78, 78), [(53, 83), (420, 83), (360, 190), (320, 280), (290, 380), (53, 380)])
        self.a_poly((110, 100, 98), [(53, 83), (130, 83), (110, 200), (53, 240)])
        self.a_ellipse((40, 30, 40), 110, 238, 200, 96)
        for k in range(5):
            self.a_line((66, 58, 60), 340 - k * 14, 150 + k * 40, 380 - k * 14, 160 + k * 40, 3)
        # the ship caught in the strait
        sy = 392 + math.sin(ticks * 1.2) * 4
        self.a_ship(370, sy, t, 1.3, bill=0)
        reach = (1 - (1 - p / 0.5) ** 2) if p < 0.5 else (1 - (p - 0.5) / 0.5)
        reach = max(0.0, min(1.0, reach))
        for i in range(6):
            mx = 400 + i * 26
            if p < 0.5:
                self.a_man(mx, sy, (226, 226, 226) if i % 2 else RED, 1, 0, 0, "up", 0.95)
        # six hissing heads on long necks
        for i in range(6):
            bx, by = 150 + i * 28, 282
            tx, ty = 400 + i * 26, sy - 40
            hx = bx + (tx - bx) * reach
            hy = by + (ty - by) * reach
            pts = []
            for j in range(13):
                u = j / 12.0
                pts.append((bx + (hx - bx) * u, by + (hy - by) * u - math.sin(u * math.pi) * (55 + 20 * (i % 2))))
            self.a_lines((92, 52, 112), pts, 10)
            self.a_lines((140, 92, 164), pts, 3)
            self.a_circle((92, 52, 112), hx, hy, 12)
            self.a_poly((112, 70, 134), [(hx + 4, hy - 4), (hx + 22, hy + 2), (hx + 4, hy + 6)])
            self.a_circle((255, 232, 60), hx + 2, hy - 4, 3)
            self.a_circle(BLACK, hx + 3, hy - 4, 1)
            self.a_poly((245, 245, 240), [(hx + 8, hy + 5), (hx + 11, hy + 11), (hx + 14, hy + 5)])
            if p >= 0.5:
                self.a_tumble(hx + 14, hy + 16, math.sin(t * 0.6 + i) * 0.7, (226, 226, 226) if i % 2 else RED, 0.5)
        self.a_end()
        self.a_title("SCYLLA ATTACKS FROM THE CLIFFS!", RED)

    def anim_helios_eating_night(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((4, 5, 20), (26, 24, 58), 83, 380)
        self.a_stars(t, 300)
        self.a_moon(660, 215, 22)
        self.a_glow(720, 372, 140, (255, 190, 80), 50 + int(60 * p))
        self.a_poly((18, 42, 30), [(53, 372), (300, 350), (520, 366), (747, 346), (747, 517), (53, 517)])
        self.a_rect((14, 32, 22), 53, 470, 694, 47)
        # the sacred herd, grazing in the dark, some already fallen
        self.a_cow(270, 400, 1, 0.9)
        self.a_cow(330, 392, -1, 0.8)
        self.a_cow(560, 396, -1, 0.9)
        self.a_cow(640, 404, 1, 0.8)
        self.a_cow(600, 440, 1, 0.9, down=True)
        # an olive tree, and Odysseus sleeping in its shade
        self.a_poly((66, 46, 30), [(104, 440), (122, 440), (118, 330), (130, 290), (112, 290), (108, 340)])
        self.a_circle((38, 80, 48), 118, 280, 44)
        self.a_circle((46, 96, 56), 90, 296, 30)
        self.a_circle((46, 96, 56), 148, 296, 30)
        self.a_rect(RED, 146, 432, 48, 15)
        self.a_circle((236, 198, 158), 202, 440, 9)
        self.draw_text("zZZ", self.small_font, CYAN, 206 + self.shake_offset[0], 404 - int((t // 6) % 8) + self.shake_offset[1])
        # the starving crew feast around a roaring fire
        fx, fy = 440, 462
        self.a_glow(fx, fy - 10, 170, (255, 140, 40), 110)
        self.a_line((80, 54, 30), fx - 30, fy, fx + 30, fy - 8, 7)
        self.a_line((80, 54, 30), fx - 30, fy - 8, fx + 30, fy, 7)
        self.a_flame(fx, fy - 4, 46, 76, t, 0)
        self.a_flame(fx + 14, fy - 2, 28, 50, t, 3)
        self.a_line((120, 100, 80), fx - 46, fy - 38, fx + 46, fy - 38, 3)
        self.a_ellipse((160, 76, 44), fx - 16, fy - 52 + int(math.sin(t * 0.2) * 2), 32, 18)
        for i in range(10):
            u = ((t * 1.3 + i * 17) % 90) / 90.0
            self.a_rect((255, 210, 90), fx + math.sin(i * 2 + u * 5) * 20, fy - 40 - u * 120, 2, 2)
        for i, mx in enumerate((340, 392, 490, 546)):
            bob = abs(math.sin(t * 0.3 + i)) * 5
            self.a_man(mx, 478 - bob, ((220, 130, 90), (226, 226, 216))[i % 2], 1 if mx < fx else -1, math.sin(t * 0.3 + i) * 3, 0, "up", 1.5)
            self.a_ellipse((165, 76, 46), mx + 4, 478 - bob - 76, 18, 12)
        self.a_end()
        self.a_title("NIGHTFALL ON THRINACIA", GOLD, 110)
        self.draw_text("While Odysseus sleeps, the starving crew slaughters Helios' sacred cattle!", self.small_font, WHITE,
                       WIDTH // 2 + self.shake_offset[0], 150 + self.shake_offset[1], center=True)

    def anim_lightning_strike(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        ticks = t * 0.15
        strike = 0.42
        hit = p >= strike
        self.a_begin()
        self.a_sky((10, 12, 22), (52, 58, 78), 83, 400)
        for i in range(6):
            cx = 20 + i * 140 + math.sin(t * 0.02 + i) * 14
            self.a_cloud(cx, 130 + (i % 2) * 34, 1.4, (26 + i * 3, 28 + i * 3, 40 + i * 3))
        if t in (22, 23, 43, 44, 59, 60):
            self.a_fade((200, 210, 255), 55)
            self.a_bolt(150, 150, 130, 330, t // 2, 2)
        self.a_sea(400, (14, 28, 54), (160, 182, 212), ticks, 14, (4, 10, 24), 24)
        self.a_rain(t, 70)
        sx = 325
        sy = 382 + math.sin(ticks) * 7
        mastx = sx + 74
        if not hit:
            self.a_ship(sx, sy, t, 1.1, oars=False, bill=6)
            for i in range(3):
                self.a_man(sx + 40 + i * 28, sy, (226, 226, 226) if i % 2 else RED, 1, 0, 0, "up", 0.8)
        else:
            k = (p - strike) / (1 - strike)
            self.a_ship(sx, sy, t, 1.1, oars=False, broken=True)
            self.a_flame(mastx + 3, sy - 30, 34, 60, t, 0)
            self.a_flame(sx + 120, sy, 26, 46, t, 2)
            self.a_flame(sx + 40, sy, 22, 38, t, 4)
            self.a_smoke(mastx, sy - 50, t, 5, (60, 58, 64))
            for i in range(3):
                u = min(1.0, k * 1.6)
                self.a_tumble(sx + 50 + i * 40 + (i - 1) * u * 80, sy - 24 - math.sin(u * math.pi) * 60 + u * 30, u * 6 + i, (226, 226, 226) if i % 2 else RED, 0.8)
        if strike <= p < strike + 0.1:
            self.a_bolt(mastx - 50, 90, mastx + 4, sy - 82 if not hit else sy - 32, t // 2, 5)
            self.a_glow(mastx, sy - 60, 90, (255, 255, 255), 200)
        if strike <= p < strike + 0.08:
            self.a_fade((255, 255, 255), 230 * (1 - (p - strike) / 0.08))
        elif hit and p < strike + 0.2:
            self.a_fade((255, 255, 255), 20)
        self.a_end()
        self.a_title("ZEUS STRIKES THE SHIP!", YELLOW)

    def anim_shipwreck_drowning(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        ticks = t * 0.15
        H = 372
        self.a_begin()
        self.a_sky((6, 8, 18), (40, 46, 64), 83, H)
        for i in range(5):
            self.a_cloud(i * 160 - 20, 130 + (i % 2) * 30, 1.3, (22, 24, 36))
        if t % 47 < 3:
            self.a_fade((200, 210, 255), 40)
            self.a_bolt(620, 140, 600, 360, t // 3, 2)
        self.a_rain(t, 60)
        # the ship snaps in two, the mast topples, and both halves go under
        sink = min(1.0, p / 0.55)
        hull = (110, 66, 30)
        left = _rot([(290, 345), (398, 345), (384, 392), (312, 392)], 344, 370, -0.9 * sink)
        right = _rot([(406, 345), (514, 345), (488, 392), (420, 392)], 460, 370, 1.0 * sink)
        self.a_poly(hull, [(px - sink * 40, py + sink * 90) for px, py in left])
        self.a_poly(hull, [(px + sink * 50, py + sink * 100) for px, py in right])
        mast = _rot([(404, 345), (404, 250)], 404, 345, 0.3 + sink * 1.2)
        self.a_line((90, 60, 30), mast[0][0], mast[0][1] + sink * 40, mast[1][0], mast[1][1] + sink * 40, 6)
        sail = _rot([(408, 262), (470, 272), (456, 326), (408, 326)], 404, 345, 0.3 + sink * 1.2)
        self.a_poly((226, 216, 190), [(px, py + sink * 40) for px, py in sail])
        # sailors thrashing in the water, going under one by one
        xs = [120, 185, 250, 310, 540, 590, 640, 692]
        for i, mx in enumerate(xs):
            k = max(0.0, min(1.0, (p - (0.30 + i * 0.07)) / 0.1))
            wy = 380 + math.sin(ticks + i) * 6 + k * 44
            self.a_rect(RED if i % 2 else (226, 226, 226), mx - 7, wy, 14, 11)
            self.a_circle((236, 198, 158), mx, wy - 7, 7)
            flail = math.sin(t * 0.5 + i) * 8
            self.a_line((236, 198, 158), mx - 6, wy + 1, mx - 17, wy - 20 + flail, 4)
            self.a_line((236, 198, 158), mx + 6, wy + 1, mx + 17, wy - 20 - flail, 4)
        self.a_sea(H + 8, (12, 26, 50), (150, 172, 202), ticks, 10, (3, 8, 20), 24)
        for i, mx in enumerate(xs):
            k = (p - (0.30 + i * 0.07)) / 0.2
            if 0 < k < 1:
                for b in range(3):
                    self.a_circle((170, 200, 230), mx - 8 + b * 8, 396 - ((t * 2 + b * 9) % 34), 4, 1)
        for k in range(6):
            dx = 90 + k * 120 + math.sin(ticks + k) * 10
            dy = 392 + math.sin(ticks * 1.2 + k) * 4
            self.a_line((120, 80, 40), dx, dy, dx + 38, dy - 6 + (k % 3) * 4, 6)
        # only Odysseus survives, clinging to the shattered mast and keel
        mx0, my0 = 410, 386 + math.sin(ticks * 1.1) * 4
        self.a_line((96, 62, 30), mx0 - 90, my0, mx0 + 90, my0 - 5, 11)
        self.a_line((130, 88, 44), mx0 - 76, my0 + 8, mx0 + 50, my0 + 6, 6)
        self.a_rect(RED, mx0 - 8, my0 - 17, 30, 11)
        self.a_circle((236, 198, 158), mx0 - 16, my0 - 14, 8)
        self.a_line((236, 198, 158), mx0 - 4, my0 - 11, mx0 + 26, my0 - 5, 4)
        self.a_end()
        self.a_title("ALL MEN ARE LOST TO THE SEA!", RED)

    def anim_charybdis_suck_raft(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((20, 28, 42), (92, 108, 128), 83, 345)
        for i in range(5):
            self.a_cloud((i * 190 - t * 2) % 900 - 100, 150 + (i * 31) % 70, 1.3, (44 + i * 4, 52 + i * 4, 70 + i * 4))
        self.a_sea(345, (32, 62, 98), (180, 206, 232), t * 0.1, 6, (8, 16, 32))
        cx, cy = 400, 420
        self.a_whirl(cx, cy, 330, t, 0.30, 10)
        self.a_glow(cx, cy + 20, 120, (4, 10, 26), 150)
        # drifting wreckage circles inward
        for k in range(6):
            a = t * 0.07 * (1 + k * 0.1) + k * 1.05
            d = (220 - k * 25) * (1 - p * 0.7)
            px, py = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.30 + p * 18
            self.a_line((130, 86, 44), px - 18, py, px + 18, py + (k % 3) - 1, 6)
        # Odysseus' raft spirals down
        a = 2.0 + t * 0.09 * (1 + p * 1.4)
        d = (1 - p * 0.88) * 250 + 18
        rx, ry = cx + math.cos(a) * d, cy + math.sin(a) * d * 0.30 + p * 20
        self.a_raft(rx, ry - 10, 1.8 - p * 0.7, "sit")
        for k in range(12):
            u = ((t * 2 + k * 11) % 60) / 60.0
            self.a_circle((205, 228, 245), cx + (k - 6) * 26 + math.sin(k) * 10, 380 - u * 70, 2)
        self.a_end()
        self.a_title("CHARYBDIS PULLS THE RAFT DOWN!", CYAN)

    def anim_charybdis_fig_tree(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky((20, 26, 38), (74, 90, 108), 83, 432)
        for i in range(4):
            self.a_cloud(i * 230 - 20, 160 + (i % 2) * 30, 1.3, (38 + i * 4, 46 + i * 4, 62 + i * 4))
        self.a_sea(430, (30, 58, 92), (170, 198, 224), t * 0.1, 5, (6, 14, 30))
        self.a_whirl(400, 455, 300, t, 0.28, 9)
        for k in range(4):
            a = t * 0.06 + k * 1.6
            d = (190 - k * 30) * (1 - p * 0.3)
            self.a_line((130, 86, 44), 400 + math.cos(a) * d - 12, 460 + math.sin(a) * d * 0.28, 400 + math.cos(a) * d + 12, 460 + math.sin(a) * d * 0.28, 4)
        # the cliff and the wild fig tree overhanging the abyss
        self.a_poly((78, 70, 66), [(53, 83), (190, 83), (232, 200), (190, 330), (120, 517), (53, 517)])
        sway = math.sin(t * 0.08)
        pts = [(176, 330), (190, 262), (232, 214), (320, 196), (420, 198), (530, 214)]
        self.a_lines((96, 66, 36), pts, 14)
        self.a_lines((126, 90, 50), pts, 5)
        for k, (lx, ly) in enumerate(((250, 196), (300, 182), (350, 186), (400, 178), (450, 186), (500, 196), (540, 206), (220, 214))):
            self.a_circle((46, 134, 54), lx + sway * 3, ly + math.sin(t * 0.1 + k) * 2, 22)
            self.a_circle((70, 170, 76), lx + sway * 3 - 6, ly - 6, 12)
            if k % 2 == 0:
                self.a_circle((120, 50, 110), lx + 8, ly + 18, 4)
        # Odysseus clinging to the branch, his legs swinging over the whirlpool
        hx = 400 + sway * 12
        sw = math.sin(t * 0.12) * 14
        skin = (236, 198, 158)
        self.a_line(skin, hx - 5, 224, hx - 9, 198, 4)
        self.a_line(skin, hx + 5, 224, hx + 9, 198, 4)
        self.a_rect(RED, hx - 8, 222, 16, 30)
        self.a_circle(skin, hx, 214, 8)
        self.a_line(skin, hx - 4, 252, hx - 4 + sw, 290, 5)
        self.a_line(skin, hx + 4, 252, hx + 4 + sw * 0.7, 288, 5)
        for k in range(14):
            u = ((t * 2 + k * 13) % 60) / 60.0
            self.a_circle((205, 228, 245), 400 + (k - 7) * 28, 430 - u * 90, 2)
        self.a_end()
        self.a_title("HOLDING ON FOR DEAR LIFE!", GREEN)

    def anim_charybdis_spit_raft(self):
        t = 180 - self.anim_timer
        p = t / 180.0
        self.a_begin()
        self.a_sky(_mix((20, 26, 38), (130, 170, 215), p), _mix((74, 90, 108), (250, 210, 160), p), 83, 432)
        self.a_glow(620, 330, 120, (255, 220, 150), int(120 * p))
        self.a_sea(430, _mix((30, 58, 92), (60, 130, 190), p), (190, 215, 235), t * 0.1, 5 + 4 * (1 - p), (6, 14, 30))
        rx_ = int(300 * (1 - p * 0.8))
        if rx_ > 60:
            self.a_whirl(400, 455, rx_, t, 0.28, 8)
        # a geyser erupts as the whirlpool vomits up the wreck
        erupt = min(1.0, p / 0.35) * (1 - max(0.0, (p - 0.5) / 0.3))
        if erupt > 0:
            for k in range(9):
                r = 24 - k * 1.8
                self.a_circle(_mix((190, 220, 245), (255, 255, 255), k / 8.0), 400 + math.sin(t * 0.3 + k) * 6, 440 - k * erupt * 22, r)
            for k in range(14):
                u = ((t * 2.4 + k * 9) % 50) / 50.0
                ang = k * 0.9
                self.a_circle((225, 240, 252), 400 + math.cos(ang) * u * 110, 420 - math.sin(u * math.pi) * 90 * erupt, 3)
        # the raft is thrown up and Odysseus drops from the fig tree onto it
        pe = min(1.0, p / 0.5)
        raftx = 400
        rafty = 470 - pe * 78
        if p > 0.7:
            raftx = 400 + (p - 0.7) / 0.3 * 130
        self.a_poly((78, 70, 66), [(53, 83), (190, 83), (232, 200), (190, 330), (120, 517), (53, 517)])
        pts = [(176, 330), (190, 262), (232, 214), (320, 196), (420, 198), (530, 214)]
        self.a_lines((96, 66, 36), pts, 14)
        self.a_lines((126, 90, 50), pts, 5)
        for k, (lx, ly) in enumerate(((250, 196), (300, 182), (350, 186), (400, 178), (450, 186), (500, 196), (540, 206), (220, 214))):
            self.a_circle((46, 134, 54), lx, ly, 22)
            self.a_circle((70, 170, 76), lx - 6, ly - 6, 12)
        fall = max(0.0, min(1.0, (p - 0.45) / 0.25))
        if fall < 1.0:
            hy = 222 + fall * fall * (rafty - 60 - 222)
            hang = 1 - fall
            self.a_line((236, 198, 158), 395, hy, 392, hy - 24 * hang, 4)
            self.a_line((236, 198, 158), 405, hy, 408, hy - 24 * hang, 4)
            self.a_rect(RED, 392, hy, 16, 28)
            self.a_circle((236, 198, 158), 400, hy - 9, 8)
            self.a_line((236, 198, 158), 396, hy + 28, 394, hy + 52, 5)
            self.a_line((236, 198, 158), 404, hy + 28, 408, hy + 52, 5)
            self.a_raft(raftx, rafty, 1.6, None)
        else:
            self.a_raft(raftx, rafty, 1.6, "sit")
        self.a_end()
        self.a_title("CHARYBDIS SPITS THE RAFT BACK OUT!", GOLD)

    def anim_drifting_ogygia(self):
        t = 540 - self.anim_timer
        p = t / 540.0
        ticks = t * 0.05
        phase = (t % 60) / 60.0
        if phase < 0.65:
            u = phase / 0.65
            light = max(0.25, math.sin(u * math.pi))
            body = (255, 232, 140)
            bx, by = 90 + u * 620, 345 - math.sin(u * math.pi) * 190
            night = False
        else:
            u = (phase - 0.65) / 0.35
            light = 0.1
            body = (236, 236, 214)
            bx, by = 90 + u * 620, 345 - math.sin(u * math.pi) * 170
            night = True
        self.a_begin()
        self.a_sky(_mix((6, 8, 26), (80, 150, 225), light), _mix((22, 22, 56), (230, 220, 200), light), 83, 345)
        if night:
            self.a_stars(t, 330)
        self.a_glow(bx, by, 60, body, 110)
        self.a_circle(body, bx, by, 22 if not night else 18)
        # gulls wheel overhead by day
        if not night:
            for k in range(3):
                gx = (t * 2 + k * 230) % 760 + 40
                gy = 190 + k * 30 + math.sin(t * 0.12 + k) * 8
                self.a_lines(WHITE, [(gx - 8, gy - int(abs(math.sin(t * 0.3 + k)) * 5)), (gx, gy), (gx + 8, gy - int(abs(math.sin(t * 0.3 + k)) * 5))], 2)
        # Ogygia rises over the horizon at last
        if p > 0.8:
            k = min(1.0, (p - 0.8) / 0.15)
            sh = int((1 - k) * 220)
            self.a_poly((46, 96, 62), [(540 + sh, 352), (590 + sh, 300), (650 + sh, 276), (715 + sh, 306), (790 + sh, 352)])
            self.a_poly((72, 128, 80), [(610 + sh, 352), (660 + sh, 314), (730 + sh, 328), (790 + sh, 352)])
            self.a_ellipse((20, 40, 28), 676 + sh, 318, 36, 26)
        self.a_sea(345, _mix((10, 24, 60), (50, 110, 170), light), (190, 215, 240), ticks, 9, (4, 10, 28))
        raftx = 100 + p * 370
        self.a_raft(raftx, 394 + math.sin(ticks * 1.4) * 5, 2.2, "lie")
        self.a_end()
        self.a_title("DRIFTING ALONE ACROSS THE OCEAN...", WHITE, 90)
        seconds_left = max(1, self.anim_timer // 60)
        self.draw_text(f"Day {10 - seconds_left} of 9...", self.font, CRT_GREEN, WIDTH // 2 + self.shake_offset[0], 130 + self.shake_offset[1], center=True)

    # ==================================================================
    #  ITHACA
    # ==================================================================
    def a_odysseus(self, x, y, s=2.0, form="king", arms="down", lean=0, step=0.0):
        """Odysseus as himself (red cloak) or disguised as an old beggar. (x, y) = feet."""
        if form == "king":
            hx, hy = self.a_man(x, y, RED, 1, step, lean, arms, s, helmet=False)
            self.a_line(GOLD, x - 5 * s, y - 14 * s, x + 5 * s, y - 14 * s, max(2, int(2.5 * s)))
            self.a_poly((140, 30, 40), [(x - 5 * s, y - 28 * s), (x - 11 * s, y - 8 * s), (x - 5 * s, y - 12 * s)])
        else:
            hx, hy = self.a_man(x, y, (112, 98, 78), 1, step, 7 * s / 2.0 + lean, arms, s * 0.95, helmet=False, hair=(190, 190, 190))
            self.a_poly((196, 196, 196), [(hx - 4 * s, hy + 2 * s), (hx + 4 * s, hy + 2 * s), (hx + 2 * s, hy + 10 * s), (hx - 2 * s, hy + 10 * s)])
            self.a_line((110, 80, 50), x + 13 * s, y, x + 11 * s, y - 40 * s, max(2, int(2.5 * s)))
            self.a_ellipse((140, 110, 70), x - 15 * s, y - 30 * s, 10 * s, 13 * s)
            self.a_line((96, 80, 60), x - 4 * s, y - 20 * s, x + 4 * s, y - 16 * s, max(1, int(2 * s)))
        return hx, hy

    def a_athena(self, x, y, s=2.0, f=-1, cast=False):
        """The goddess Athena. (x, y) = feet. f = facing."""
        skin = (240, 216, 192)
        self.a_glow(x, y - 40 * s, 70 * s, (205, 228, 255), 110)
        self.a_line((196, 160, 70), x - 16 * f * s, y + 2 * s, x - 16 * f * s, y - 64 * s, max(2, int(2.5 * s)))
        self.a_poly((235, 235, 245), [(x - 16 * f * s, y - 64 * s), (x - 19 * f * s, y - 56 * s), (x - 13 * f * s, y - 56 * s)])
        self.a_poly((238, 242, 252), [(x - 15 * s, y), (x + 15 * s, y), (x + 7 * s, y - 36 * s), (x - 7 * s, y - 36 * s)])
        self.a_rect((90, 130, 210), x - 7 * s, y - 24 * s, 14 * s, 3 * s)
        self.a_poly(GOLD, [(x - 10 * s, y - 38 * s), (x + 10 * s, y - 38 * s), (x + 5 * s, y - 29 * s), (x - 5 * s, y - 29 * s)])
        hand = (x + (20 if cast else 9) * f * s, y - (34 if cast else 24) * s)
        self.a_line(skin, x + 5 * f * s, y - 36 * s, hand[0], hand[1], max(2, int(2.5 * s)))
        self.a_line(skin, x - 5 * f * s, y - 36 * s, x - 15 * f * s, y - 30 * s, max(2, int(2.5 * s)))
        self.a_circle(skin, x, y - 45 * s, 6 * s)
        self.a_poly((70, 44, 34), [(x - 6 * s, y - 46 * s), (x - 8 * f * s - 2 * s, y - 30 * s), (x - 3 * s, y - 38 * s)])
        self.a_poly((205, 160, 60), [(x - 7 * s, y - 46 * s), (x - 6 * s, y - 53 * s), (x, y - 56 * s), (x + 6 * s, y - 53 * s), (x + 7 * s, y - 46 * s)])
        self.a_poly((196, 50, 50), [(x - 1 * s, y - 56 * s), (x - 8 * f * s - 1 * s, y - 64 * s), (x - 11 * f * s, y - 54 * s)])
        self.a_ellipse((150, 120, 84), x - 14 * f * s - 3 * s, y - 44 * s, 7 * s, 10 * s)
        self.a_circle((255, 240, 160), x - 14 * f * s - 1 * s, y - 40 * s, max(1, s))
        return hand

    def a_dog(self, x, y, t, f=1, s=1.0, wag=0.25, head_up=False):
        """Argos, Odysseus' old hound, lying down. (x, y) = ground beneath his belly."""
        coat, dk = (176, 142, 96), (128, 98, 64)
        self.a_line(dk, x - 22 * f * s, y - 9 * s, x - 34 * f * s, y - 9 * s - 10 * s * (0.5 + 0.5 * math.sin(t * wag * 3)), max(2, int(3 * s)))
        self.a_ellipse(coat, x - 24 * s, y - 17 * s, 48 * s, 17 * s)
        self.a_ellipse(dk, x - 8 * s, y - 17 * s, 22 * s, 8 * s)
        hx = x + 25 * f * s
        hy = y - (30 if head_up else 14) * s
        self.a_line(coat, x + 14 * f * s, y - 10 * s, hx, hy, max(3, int(9 * s)))
        self.a_rect(coat, x + 12 * f * s - 4 * s, y - 5 * s, 18 * s, 5 * s)
        self.a_circle(coat, hx, hy, 8 * s)
        self.a_ellipse((214, 198, 170), hx + 4 * f * s - 5 * s, hy - 1 * s, 12 * s, 8 * s)
        self.a_circle((30, 24, 20), hx + 10 * f * s, hy + 1 * s, max(1, 2 * s))
        self.a_circle((30, 24, 20), hx + 2 * f * s, hy - 3 * s, max(1, 1.5 * s))
        self.a_ellipse(dk, hx - 5 * f * s - 3 * s, hy - 4 * s, 7 * s, 13 * s)

    def anim_athena_disguise(self):
        t = 420 - self.anim_timer
        p = t / 420.0
        ticks = t * 0.05
        gy = 472
        S = 2.2
        self.a_begin()
        self.a_sky((70, 70, 120), (252, 208, 166), 83, 310)
        self.a_glow(210, 306, 170, (255, 222, 160), 110)
        self.a_circle((255, 238, 184), 210, 308, 28)
        self.a_sea(306, (88, 118, 172), (255, 228, 192), ticks, 3, (40, 60, 112))
        self.a_poly((78, 90, 116), [(420, 312), (480, 266), (570, 288), (650, 254), (747, 294), (747, 312)])
        self.a_poly((100, 120, 100), [(53, 520), (53, 380), (200, 356), (420, 366), (747, 354), (747, 520)])
        self.a_rect((78, 104, 62), 53, 486, 694, 31)
        # the cave of the nymphs and an old olive tree
        self.a_poly((104, 94, 86), [(60, 420), (96, 340), (180, 322), (250, 346), (280, 420)])
        self.a_ellipse((34, 28, 30), 108, 366, 128, 76)
        self.a_poly((72, 52, 36), [(640, 440), (662, 440), (656, 360), (676, 322), (650, 322), (640, 366)])
        for cx, cy, r in ((650, 310, 44), (610, 330, 30), (692, 332, 30)):
            self.a_circle((124, 150, 108), cx, cy, r)
            self.a_circle((150, 176, 128), cx - 8, cy - 8, r * 0.5)
        for k in range(6):
            self.a_glow((k * 170 + t * 0.6) % 800, 360 + (k % 2) * 20, 90, (255, 242, 232), 45)
        # Athena arrives in a blaze of grey-eyed light
        ax = 530
        if p > 0.06:
            a = min(1.0, (p - 0.06) / 0.14)
            self.a_glow(ax, gy - 80, 40 + a * 80, (225, 238, 255), int(60 + 90 * a))
        hand = None
        if p > 0.14:
            hand = self.a_athena(ax, gy, 2.4, -1, cast=(0.28 <= p < 0.62))
        # Odysseus, still himself... until the goddess strikes
        ox_ = 300
        form = "king" if p < 0.5 else "beggar"
        self.a_odysseus(ox_, gy, S, form, "fwd" if (0.26 <= p < 0.5) else "down")
        if hand is not None and 0.28 <= p < 0.62:
            for k in range(16):
                u = ((t * 3 + k * 13) % 80) / 80.0
                sx = hand[0] + (ox_ + 10 - hand[0]) * u
                sy = hand[1] + (gy - 80 - hand[1]) * u + math.sin(u * 9 + k) * 12
                self.a_glow(sx, sy, 10, (255, 226, 130), 170)
        if 0.46 <= p < 0.7:
            k = min(1.0, (p - 0.46) / 0.24)
            self.a_glow(ox_, gy - 60, 110 * (1.1 - k * 0.4), (255, 230, 150), int(160 * (1 - k)))
            for q in range(12):
                ang = q * 0.52 + t * 0.12
                r = 28 + k * 50
                self.a_glow(ox_ + math.cos(ang) * r, gy - 60 + math.sin(ang) * r * 1.3, 7, (255, 240, 180), int(190 * (1 - k)))
        if 0.46 <= p < 0.54:
            self.a_fade((255, 255, 255), 235 * (1 - abs(p - 0.5) / 0.04))
        self.a_end()
        self.a_title("ATHENA DISGUISES ODYSSEUS!", (190, 215, 255))

    # ==================================================================
    #  EUMAEUS' HUT
    # ==================================================================
    def a_sit(self, x, g, tunic, f=1, s=2.0, lean=0, hand_a=None, hand_b=None, hair=(80, 55, 38), beard=None):
        """A figure seated on a stool. (x, g) = floor under the stool, f = facing.
        hand_a / hand_b are hand offsets from the shoulder, in units of s. Returns head and shoulder positions."""
        skin = (236, 198, 158)
        hip = g - 14 * s
        self.a_line((92, 62, 32), x - 7 * s, hip + 3 * s, x - 8 * s, g, 3)
        self.a_line((92, 62, 32), x + 7 * s, hip + 3 * s, x + 8 * s, g, 3)
        self.a_rect((118, 80, 42), x - 10 * s, hip, 20 * s, 3 * s)
        kx = x + 15 * f * s
        leg = (205, 165, 125)
        self.a_line(leg, x, hip - 1 * s, kx, hip - 1 * s, max(3, int(3.5 * s)))
        self.a_line(leg, kx, hip - 1 * s, kx + 1 * f * s, g - 2, max(3, int(3 * s)))
        self.a_rect((88, 64, 42), kx + (1 * f - 4) * s, g - 4, 8 * s, 4)
        top = hip - 18 * s
        self.a_poly(tunic, [(x - 6 * s, hip + 2 * s), (x + 6 * s, hip + 2 * s), (x + 5.5 * s + lean, top), (x - 5.5 * s + lean, top)])
        self.a_line(_mix(tunic, (0, 0, 0), 0.45), x - 6 * s, hip + 1 * s, x + 6 * s, hip + 1 * s, max(1, int(2 * s)))
        sx, sy = x + lean * 0.9, top + 3 * s
        hx, hy = x + lean, top - 6.5 * s
        for h in (hand_a, hand_b):
            if h is not None:
                self.a_line(skin, sx, sy, sx + h[0] * s, sy + h[1] * s, max(2, int(2.6 * s)))
        self.a_circle(hair, hx, hy - 1.5 * s, 5.4 * s)
        self.a_circle(skin, hx, hy + 0.5 * s, 4.8 * s)
        if beard is not None:
            self.a_poly(beard, [(hx - 4 * s, hy + 2 * s), (hx + 4 * s, hy + 2 * s), (hx + 2 * s, hy + 10 * s), (hx - 2 * s, hy + 10 * s)])
        return hx, hy, (sx, sy)

    def a_swineherd_scene(self, t, top, bottom, sun, lit=0.5, path=True):
        """The farmland outside Eumaeus' hut. `lit` runs from 0 (dusk) to 1 (bright morning)."""
        sx, sy = sun
        self.a_sky(top, bottom, 83, 400)
        self.a_glow(sx, sy, 150, (255, 200, 130), 100)
        self.a_circle((255, 232, 160), sx, sy, 28)
        self.a_poly(_mix((64, 62, 108), (120, 152, 164), lit), [(53, 400), (53, 332), (180, 292), (320, 342), (470, 302), (620, 352), (747, 312), (747, 400)])
        grass = _mix((52, 84, 50), (98, 138, 72), lit)
        self.a_rect(grass, 53, 400, 694, 117)
        self.a_rect(_mix(grass, (0, 0, 0), 0.18), 53, 488, 694, 29)
        if path:
            self.a_poly(_mix((132, 108, 80), (188, 162, 114), lit), [(330, 517), (540, 517), (474, 430), (440, 372), (444, 334), (420, 334), (404, 372), (376, 430)])
        for tx, th in ((560, 150), (700, 130)):
            self.a_rect((70, 50, 34), tx - 6, 400 - th, 12, th)
            self.a_circle(_mix((34, 76, 48), (50, 110, 60), lit), tx, 400 - th - 10, 46)
            self.a_circle(_mix((46, 94, 58), (70, 132, 74), lit), tx - 14, 400 - th - 20, 24)
        self.a_rect((152, 128, 96), 60, 330, 190, 110)
        for k in range(5):
            self.a_rect((130, 106, 78), 66 + k * 38, 336, 28, 18)
        self.a_poly((196, 164, 92), [(42, 332), (155, 262), (268, 332)])
        self.a_poly((170, 138, 72), [(42, 332), (155, 262), (160, 266), (60, 332)])
        self.a_rect((50, 34, 24), 132, 378, 44, 62)
        self.a_rect((70, 50, 34), 212, 350, 26, 24)
        self.a_rect((98, 90, 84), 214, 258, 20, 40)
        self.a_smoke(224, 256, t, 4)
        for k, px in enumerate((590, 640, 700)):
            self.a_pig(px, 436, t + k * 11, 1 if k % 2 else -1, 0.9)
        for fx in range(560, 748, 30):
            self.a_rect((96, 66, 38), fx, 404, 6, 46)
        self.a_rect((120, 84, 48), 560, 414, 187, 4)
        self.a_rect((120, 84, 48), 560, 434, 187, 4)

    def a_tale_panel(self, scene, t, wipe):
        """The picture of the Cretan's story, hanging in the air above the hearth."""
        x0, y0, w, h = 270, 148, 260, 126
        self.a_rect((40, 28, 18), x0 - 6, y0 - 6, w + 12, h + 12)
        self.a_rect((228, 206, 152), x0 - 6, y0 - 6, w + 12, h + 12, 3)
        if scene == 0:       # a hero of Crete
            self.a_rect((140, 200, 245), x0, y0, w, h)
            self.a_circle((255, 236, 150), 492, 176, 14)
            self.a_rect((60, 130, 200), x0, 232, w, 42)
            for k in range(6):
                self.a_rect((200, 230, 250), x0 + (k * 42 + t * 0.6) % 230, 240 + (k % 2) * 12, 22, 2)
            self.a_poly((96, 150, 86), [(272, 236), (304, 204), (352, 186), (402, 206), (430, 236)])
            self.a_rect((214, 190, 130), 272, 232, 158, 5)
            self.a_line((120, 90, 50), 352, 232, 352, 176, 2)
            self.a_poly((215, 215, 225), [(352, 174), (348, 184), (356, 184)])
            self.a_man(340, 232, (196, 62, 56), 1, 0, 0, "down", 1.5)
            self.a_circle((205, 160, 60), 326, 214, 9)
            self.a_circle((150, 100, 40), 326, 214, 4)
            self.a_ship(440, 238 + int(math.sin(t * 0.1) * 2), t, 0.4)
        elif scene == 1:     # the fall of Troy
            self.a_rect((176, 70, 52), x0, y0, w, 50)
            self.a_rect((212, 104, 62), x0, y0 + 50, w, 40)
            self.a_rect((236, 150, 80), x0, y0 + 90, w, 36)
            self.a_rect((62, 46, 34), x0, 252, w, 22)
            self.a_rect((120, 98, 78), 280, 214, 130, 38)
            for bx in range(280, 410, 20):
                self.a_rect((120, 98, 78), bx, 206, 11, 8)
            self.a_rect((104, 84, 64), 290, 190, 24, 62)
            self.a_rect((104, 84, 64), 372, 196, 24, 56)
            self.a_rect((40, 26, 18), 298, 224, 8, 14)
            self.a_flame(302, 190, 18, 34, t, 0)
            self.a_flame(384, 196, 16, 30, t, 2)
            self.a_flame(342, 214, 16, 26, t, 4)
            self.a_rect((150, 104, 56), 432, 226, 52, 20)
            for lx in (436, 448, 468, 478):
                self.a_rect((120, 80, 40), lx, 244, 5, 16)
            self.a_poly((150, 104, 56), [(480, 228), (490, 204), (500, 208), (486, 236)])
            self.a_poly((150, 104, 56), [(490, 204), (512, 208), (508, 216), (492, 214)])
            self.a_line((90, 56, 28), 488, 206, 480, 228, 3)
            self.a_circle(BLACK, 500, 209, 1)
            self.a_man(406, 258, (200, 60, 60), 1, math.sin(t * 0.4) * 2, 0, "up", 0.9)
            self.a_man(420, 262, (226, 226, 226), 1, 0, 0, "up", 0.9)
        else:                # Odysseus alive, sailing home
            self.a_rect((250, 196, 130), x0, y0, w, 50)
            self.a_rect((252, 222, 168), x0, y0 + 50, w, 40)
            self.a_circle((255, 226, 130), 400, 232, 26)
            for k in range(9):
                ang = -math.pi + k * math.pi / 8.0
                self.a_line((255, 226, 140), 400 + math.cos(ang) * 34, 232 + math.sin(ang) * 34, 400 + math.cos(ang) * 74, 232 + math.sin(ang) * 74, 2)
            self.a_rect((70, 130, 200), x0, 238, w, 36)
            bob = int(math.sin(t * 0.1) * 2)
            self.a_ship(330, 238 + bob, t, 0.6, bill=4)
            self.a_glow(378, 214 + bob, 26, (255, 230, 150), 150)
            self.a_man(376, 238 + bob, RED, 1, 0, 0, "up", 0.9, helmet=False)
        if wipe < 0.08:
            self.a_rect((255, 255, 255), x0, y0, int(w * (1 - wipe / 0.08)) + 1, h)

    def anim_eumaeus_false_tale(self):
        t = 540 - self.anim_timer
        p = t / 540.0
        gy = 474
        S = 2.2
        self.a_begin()
        # the swineherd's hut by night
        self.a_sky((70, 50, 36), (124, 94, 66), 83, 440)
        for x in range(53, 747, 46):
            self.a_rect((58, 40, 28), x, 83, 3, 357)
        self.a_rect((44, 30, 20), 53, 146, 694, 16)
        for x in (110, 170, 230):
            self.a_line((70, 50, 30), x, 162, x, 186, 2)
            self.a_ellipse((90, 140, 70), x - 7, 184, 14, 28)
        self.a_poly((150, 110, 80), [(590, 162), (650, 162), (640, 236), (600, 240)])
        self.a_poly((130, 94, 66), [(660, 162), (720, 162), (712, 226), (672, 232)])
        self.a_rect((60, 40, 26), 636, 196, 78, 100)
        self.a_rect((14, 18, 44), 642, 202, 66, 88)
        self.a_circle((230, 230, 205), 676, 238, 12)
        for sx_, sy_ in ((652, 214), (694, 224), (662, 270), (698, 262)):
            self.a_rect(WHITE, sx_, sy_, 2, 2)
        self.a_rect((60, 40, 26), 70, 322, 120, 7)
        for jx, jy, jw, jh in ((82, 296, 22, 28), (112, 302, 18, 22), (142, 292, 24, 34)):
            self.a_ellipse((134, 86, 52), jx, jy, jw, jh)
        self.a_rect((98, 76, 52), 53, 436, 694, 81)
        self.a_rect((80, 60, 42), 53, 436, 694, 5)
        for k in range(46):
            sx_ = 60 + (k * 97) % 680
            sy_ = 446 + (k * 53) % 66
            self.a_line((190, 160, 92), sx_, sy_, sx_ + 7, sy_ - 2, 1)
        # the hearth
        self.a_glow(400, 450, 270, (255, 140, 40), 110)
        self.a_ellipse((90, 86, 84), 338, 456, 124, 34)
        self.a_ellipse((50, 40, 34), 352, 462, 96, 20)
        self.a_line((84, 56, 30), 366, 474, 436, 460, 8)
        self.a_line((84, 56, 30), 366, 460, 436, 474, 8)
        self.a_flame(400, 468, 56, 96, t, 0)
        self.a_flame(418, 470, 34, 60, t, 3)
        for i in range(8):
            u = ((t * 1.3 + i * 17) % 90) / 90.0
            self.a_rect((255, 210, 90), 400 + math.sin(i * 2 + u * 5) * 22, 430 - u * 130, 2, 2)
        # Eumaeus listens, goblet in hand; the "Cretan" talks with his hands
        nod = math.sin(t * 0.12) * 2
        shake = math.sin(t * 0.5) * 3 if p > 0.78 else 0
        hx, hy, sh = self.a_sit(250, gy, (98, 128, 72), 1, S, nod + shake, (12, 13), (13, 6), (150, 150, 150), (172, 172, 172))
        self.a_rect(GOLD, sh[0] + 11 * S, sh[1] + 2 * S, 7, 10)
        g = math.sin(t * 0.13)
        self.a_line((110, 80, 50), 640, gy, 632, gy - 120, 4)
        self.a_ellipse((140, 110, 70), 604, gy - 26, 36, 28)
        hx2, hy2, sh2 = self.a_sit(560, gy, (112, 98, 78), -1, S, -6, (-16, -6 + g * 9), (-12, 5 - g * 7), (190, 190, 190), (196, 196, 196))
        # the picture of his tale, with thought-bubbles rising from the speaker
        scene = 0 if p < 0.34 else (1 if p < 0.67 else 2)
        self.a_tale_panel(scene, t, (p * 3) % 1.0)
        for bx, by, br in ((520, 292, 6), (536, 322, 9), (550, 356, 12)):
            self.a_circle((236, 228, 200), bx, by, br)
            self.a_circle((140, 120, 80), bx, by, br, 2)
        self.a_end()
        self.a_title("A CRETAN'S FALSE TALE", ORANGE)

    def anim_eumaeus_leaves(self):
        t = 540 - self.anim_timer
        p = t / 540.0
        gy = 472
        S = 2.0
        self.a_begin()
        self.a_swineherd_scene(t, (128, 168, 214), (250, 226, 182), (150, 330), 0.9)
        # Telemachus walks up from the shore
        if p < 0.3:
            tx = 800 - (p / 0.3) * 280
        elif p < 0.7:
            tx = 520
        else:
            tx = 520 - min(1.0, (p - 0.7) / 0.25) * 150
        # Eumaeus runs to greet him, then sets off up the road to the city
        if p < 0.28:
            ex, ey, es = 330, gy, S
        elif p < 0.38:
            ex, ey, es = 330 + (p - 0.28) / 0.1 * 140, gy, S
        elif p < 0.62:
            ex, ey, es = 470, gy, S
        else:
            u = min(1.0, (p - 0.62) / 0.33)
            ex, ey, es = 470 - u * 40, gy - u * (gy - 338), S - u * (S - 0.9)
        e_walk = 0.28 <= p < 0.38 or p >= 0.62
        embrace = 0.38 <= p < 0.5
        e_arms = "fwd" if embrace else ("up" if (0.28 <= p < 0.38 or 0.5 <= p < 0.62) else "down")
        if ey < gy:
            self.a_man(ex, ey, (98, 128, 72), 1, math.sin(t * 0.4) * 5 * es / S, 0, "down", es, helmet=False, hair=(150, 150, 150))
        hx, hy = (None, None)
        if ey >= gy:
            hx, hy = self.a_man(ex, ey, (98, 128, 72), 1, math.sin(t * 0.4) * 5 if e_walk else 0, 0, e_arms, es, helmet=False, hair=(150, 150, 150))
            self.a_poly((170, 170, 170), [(hx - 4 * es, hy + 2 * es), (hx + 4 * es, hy + 2 * es), (hx + 2 * es, hy + 8 * es), (hx - 2 * es, hy + 8 * es)])
            self.a_line((110, 80, 50), ex + 20, gy, ex + 18, gy - 80, 4)
        self.a_odysseus(240, gy, S, "beggar", "down")
        t_walk = p < 0.3 or p >= 0.7
        self.a_line((150, 110, 60), tx - 24, gy, tx - 24, gy - 112, 4)
        self.a_poly((220, 220, 230), [(tx - 24, gy - 112), (tx - 28, gy - 100), (tx - 20, gy - 100)])
        self.a_man(tx, gy, (70, 112, 204), -1, math.sin(t * 0.4) * 5 if t_walk else 0, 0, "fwd" if embrace else "down", S, helmet=False)
        self.a_end()
        self.a_title("TELEMACHUS RETURNS!", CRT_GREEN)

    def anim_athena_reveals(self):
        t = 540 - self.anim_timer
        p = t / 540.0
        gy = 472
        S = 2.0
        self.a_begin()
        self.a_swineherd_scene(t, (40, 34, 90), (232, 140, 104), (640, 340), 0.35, path=False)
        ox_ = 290
        king = 0.5 <= p < 0.92
        # Athena, seen only by Odysseus, lays her wand on him
        a = max(0.0, min(1.0, (p - 0.12) / 0.1)) * (1.0 - max(0.0, (p - 0.9) / 0.05))
        hand = None
        if a > 0:
            self.a_glow(150, gy - 80, 40 + a * 80, (225, 238, 255), int(60 + 90 * a))
            if a > 0.4:
                hand = self.a_athena(150, gy, 2.4, 1, cast=(0.26 <= p < 0.5))
        if hand is not None and 0.26 <= p < 0.5:
            for k in range(16):
                u = ((t * 3 + k * 13) % 80) / 80.0
                sx_ = hand[0] + (ox_ - 10 - hand[0]) * u
                sy_ = hand[1] + (gy - 80 - hand[1]) * u + math.sin(u * 9 + k) * 12
                self.a_glow(sx_, sy_, 10, (255, 226, 130), 170)
        if king:
            self.a_glow(ox_, gy - 60, 120, (255, 230, 150), 70)
        arms = "fwd" if 0.78 <= p < 0.9 else "down"
        self.a_odysseus(ox_, gy, 2.2 if king else S, "king" if king else "beggar", arms)
        # Telemachus, who sees only a stranger... and then his father
        if p < 0.5:
            tx = 470
        elif p < 0.62:
            tx = 470 + (p - 0.5) / 0.12 * 30
        elif p < 0.78:
            tx = 500
        elif p < 0.9:
            tx = 500 - (p - 0.78) / 0.12 * 120
        else:
            tx = 380
        walking = 0.78 <= p < 0.9
        t_arms = "fwd" if 0.84 <= p < 0.95 else ("up" if 0.5 <= p < 0.78 else "down")
        t_lean = -7 if 0.5 <= p < 0.66 else (4 if p >= 0.92 else 0)
        self.a_line((150, 110, 60), tx - 24, gy, tx - 24, gy - 112, 4)
        self.a_poly((220, 220, 230), [(tx - 24, gy - 112), (tx - 28, gy - 100), (tx - 20, gy - 100)])
        self.a_man(tx, gy, (70, 112, 204), -1, math.sin(t * 0.4) * 5 if walking else 0, t_lean, t_arms, S, helmet=False)
        # the transformation, and its undoing
        if 0.44 <= p < 0.7:
            k = (p - 0.44) / 0.26
            self.a_beam([(270, 83), (330, 83), (360, gy), (230, gy)], (255, 232, 150), int(90 * (1 - k)))
            for q in range(12):
                ang = q * 0.52 + t * 0.12
                self.a_glow(ox_ + math.cos(ang) * (30 + k * 50), gy - 70 + math.sin(ang) * (40 + k * 60), 7, (255, 240, 180), int(190 * (1 - k)))
        if 0.46 <= p < 0.54:
            self.a_fade((255, 255, 255), 235 * (1 - abs(p - 0.5) / 0.04))
        if 0.90 <= p < 0.96:
            self.a_fade((255, 255, 255), 200 * (1 - abs(p - 0.93) / 0.03))
        self.a_end()
        self.a_title("ATHENA REVEALS THE TRUTH!", (190, 215, 255))

    # ==================================================================
    #  THE PALACE OF ODYSSEUS
    # ==================================================================
    def a_palace(self, x, y, s):
        """The palace on its hill. (x, y) = bottom centre of the front steps."""
        w = 300 * s
        self.a_rect((190, 172, 134), x - w / 2 - 22 * s, y - 16 * s, w + 44 * s, 16 * s)
        self.a_rect((208, 190, 150), x - w / 2 - 10 * s, y - 28 * s, w + 20 * s, 12 * s)
        self.a_rect((228, 208, 166), x - w / 2, y - 122 * s, w, 94 * s)
        for dx in (-1, 1):
            wx = x + dx * (w / 2 + 6 * s)
            self.a_rect((214, 194, 152), wx - 24 * s, y - 150 * s, 48 * s, 122 * s)
            self.a_poly((150, 78, 52), [(wx - 30 * s, y - 150 * s), (wx + 30 * s, y - 150 * s), (wx, y - 176 * s)])
            self.a_rect((70, 50, 34), wx - 5 * s, y - 120 * s, 10 * s, 22 * s)
        self.a_poly((160, 84, 56), [(x - w / 2 - 12 * s, y - 122 * s), (x + w / 2 + 12 * s, y - 122 * s), (x + w / 2 - 22 * s, y - 148 * s), (x - w / 2 + 22 * s, y - 148 * s)])
        self.a_poly((240, 222, 182), [(x - 64 * s, y - 148 * s), (x + 64 * s, y - 148 * s), (x, y - 186 * s)])
        self.a_circle((176, 110, 70), x, y - 158 * s, 10 * s)
        for k in range(7):
            cx = x - w / 2 + 20 * s + k * (w - 40 * s) / 6.0
            self.a_rect((246, 238, 214), cx - 5 * s, y - 120 * s, 10 * s, 92 * s)
            self.a_rect((202, 186, 150), cx - 5 * s, y - 120 * s, 3 * s, 92 * s)
        self.a_rect((66, 44, 28), x - 24 * s, y - 80 * s, 48 * s, 52 * s)
        self.a_circle((66, 44, 28), x, y - 80 * s, 24 * s)
        self.a_line(GOLD, x, y - 104 * s, x, y - 28 * s, max(1, int(2 * s)))

    def a_penelope(self, x, y, s=2.2, f=-1, arm=0.0, gown=(208, 196, 232), veil=True, hair=(60, 40, 32)):
        """Penelope (or one of her maids). (x, y) = feet. arm: 0 = at rest, 1 = raised in address."""
        skin = (240, 214, 188)
        if veil:
            self.a_poly((244, 240, 250), [(x - 7 * s, y - 52 * s), (x + 7 * s, y - 52 * s), (x + 11 * s, y - 24 * s), (x - 11 * s, y - 24 * s)])
        self.a_poly(gown, [(x - 15 * s, y), (x + 15 * s, y), (x + 8 * s, y - 36 * s), (x - 8 * s, y - 36 * s)])
        self.a_rect(GOLD, x - 15 * s, y - 3 * s, 30 * s, 3 * s)
        self.a_rect(GOLD, x - 7 * s, y - 26 * s, 14 * s, 2.5 * s)
        hand = (x + (9 + 9 * arm) * f * s, y - (24 + 28 * arm) * s)
        self.a_line(skin, x + 5 * f * s, y - 35 * s, hand[0], hand[1], max(2, int(2.6 * s)))
        self.a_line(skin, x - 5 * f * s, y - 35 * s, x - 9 * f * s, y - 22 * s, max(2, int(2.6 * s)))
        self.a_circle(hair, x - 2 * f * s, y - 47 * s, 6.4 * s)
        self.a_circle(skin, x, y - 45 * s, 5.6 * s)
        self.a_line(GOLD, x - 5 * s, y - 49 * s, x + 5 * s, y - 49 * s, max(1, int(1.5 * s)))
        return hand

    def a_stool(self, cx, cy, ang):
        """A footstool, tumbling through the air."""
        top = _rot([(-17, -4), (17, -4), (17, 4), (-17, 4)], 0, 0, ang)
        self.a_poly((156, 106, 54), [(cx + px, cy + py) for px, py in top])
        for lx in (-12, 12):
            a, b = _rot([(lx, 4), (lx * 1.1, 17)], 0, 0, ang)
            self.a_line((110, 76, 38), cx + a[0], cy + a[1], cx + b[0], cy + b[1], 3)

    def a_hall(self, t, mood="listen", door=True, suitors=True):
        """The great hall: stone walls, shields, torches, tiled floor, and the suitors feasting at a long table.
        mood: "listen", "laugh" or "cheer"."""
        self.a_sky((88, 66, 48), (152, 120, 86), 83, 400)
        for x in range(53, 747, 58):
            self.a_rect((118, 90, 62), x, 160, 2, 240)
        self.a_rect((58, 38, 24), 53, 146, 694, 18)
        for x in range(53, 747, 116):
            self.a_rect((58, 38, 24), x, 83, 14, 66)
        for sx in range(300, 700, 70):
            self.a_circle((176, 138, 62), sx, 214, 18)
            self.a_circle((126, 92, 38), sx, 214, 8)
            self.a_circle((222, 192, 100), sx, 214, 18, 2)
        for bx in (260, 520):
            self.a_rect((130, 36, 44), bx, 160, 26, 70)
            self.a_poly((130, 36, 44), [(bx, 230), (bx + 13, 244), (bx + 26, 230)])
            self.a_rect(GOLD, bx + 9, 176, 8, 8)
        if door == "barred":
            self.a_rect((120, 100, 76), 53, 166, 104, 254)
            self.a_ellipse((120, 100, 76), 53, 150, 104, 50)
            self.a_ellipse((74, 50, 30), 63, 168, 84, 46)
            self.a_rect((74, 50, 30), 63, 190, 84, 230)
            self.a_rect((64, 64, 72), 58, 312, 96, 10)
            for rx in (68, 100, 140):
                self.a_circle((140, 140, 150), rx, 317, 3)
        elif door:
            self.a_rect((120, 100, 76), 53, 166, 104, 254)
            self.a_ellipse((120, 100, 76), 53, 150, 104, 50)
            self.a_ellipse((252, 232, 176), 63, 168, 84, 46)
            self.a_rect((252, 232, 176), 63, 190, 84, 230)
            self.a_glow(110, 340, 130, (255, 236, 170), 70)
        for cx in (230, 650):
            self.a_rect((224, 208, 172), cx - 16, 150, 32, 250)
            self.a_rect((190, 172, 138), cx - 16, 150, 8, 250)
            self.a_rect((244, 232, 200), cx - 24, 140, 48, 14)
            self.a_glow(cx, 270, 90, (255, 160, 60), 100)
            self.a_rect((70, 50, 30), cx - 3, 262, 6, 36)
            self.a_flame(cx, 266, 16, 30, t, cx)
        self.a_rect((132, 108, 82), 53, 400, 694, 117)
        for k in range(6):
            self.a_rect((112, 90, 66), 53, 404 + k * 22, 694, 2)
        # the suitors
        cols = [(120, 60, 160), (40, 110, 170), (190, 60, 60), (30, 130, 90), (210, 150, 40), (150, 60, 110), (60, 90, 150), (180, 100, 50)]
        amp = {"laugh": 6, "listen": 1.5, "cheer": 4, "shock": 1.0}[mood]
        speed = 0.45 if mood == "laugh" else 0.22
        for i in range(8 if suitors else 0):
            x = 190 + i * 76
            bob = math.sin(t * speed + i * 1.3) * amp
            lift = abs(math.sin(t * 0.2 + i)) * 10
            self.a_rect(cols[i], x - 15, 322 + bob, 30, 66)
            self.a_rect(GOLD, x - 15, 322 + bob, 30, 5)
            self.a_circle((236, 198, 158), x, 308 + bob, 11)
            self.a_circle((60, 42, 30), x, 302 + bob, 11)
            self.a_circle((236, 198, 158), x, 309 + bob, 9)
            if mood == "listen":
                self.a_line((236, 198, 158), x + 12, 340 + bob, x + 24, 346 + bob, 5)
            elif mood == "shock":
                self.a_line((236, 198, 158), x - 12, 340 + bob, x - 9, 316 + bob, 5)
                self.a_line((236, 198, 158), x + 12, 340 + bob, x + 9, 316 + bob, 5)
                self.a_ellipse((120, 28, 40), x - 4, 311 + bob, 8, 10)
            else:
                up = 34 if mood == "cheer" else 20
                self.a_line((236, 198, 158), x + 12, 336 + bob, x + 26, 336 - up + bob - lift, 5)
                self.a_rect(GOLD, x + 21, 336 - up - 14 + bob - lift, 10, 14)
                self.a_ellipse((120, 28, 40), x - 4, 311 + bob, 8, 6 + int(abs(math.sin(t * 0.5 + i)) * 4))
                if mood == "laugh":
                    self.a_line((255, 255, 255), x - 18, 296 + bob, x - 24, 290 + bob, 2)
                    self.a_line((255, 255, 255), x + 18, 296 + bob, x + 24, 290 + bob, 2)
        # the table
        self.a_rect((228, 216, 192), 53, 388, 694, 24)
        self.a_rect((200, 160, 60), 53, 410, 694, 5)
        self.a_rect((120, 36, 52), 53, 415, 694, 55)
        for fx in range(80, 747, 46):
            self.a_rect((98, 26, 42), fx, 417, 3, 51)
        self.a_rect((200, 160, 60), 53, 468, 694, 5)
        for k in range(9):
            x = 80 + k * 76
            self.a_ellipse((248, 242, 228), x, 392, 44, 14)
            if k % 3 == 0:
                self.a_ellipse((196, 112, 52), x + 8, 387, 28, 14)
            elif k % 3 == 1:
                self.a_circle((120, 50, 130), x + 14, 393, 5)
                self.a_circle((200, 40, 50), x + 26, 394, 5)
            else:
                self.a_ellipse((210, 160, 80), x + 6, 388, 30, 10)
            self.a_rect(GOLD, x + 52, 384, 8, 14)

    def anim_odysseus_to_palace(self):
        t = 480 - self.anim_timer
        p = t / 480.0
        ticks = t * 0.05
        yb = 372 + 30 * p
        self.a_begin()
        self.a_sky((108, 160, 214), (250, 218, 168), 83, 340)
        self.a_glow(130, 300, 150, (255, 214, 140), 100)
        self.a_circle((255, 236, 170), 130, 300, 26)
        self.a_sea(332, (88, 130, 188), (232, 226, 202), ticks, 2, (50, 84, 140))
        self.a_poly((104, 132, 122), [(53, 360), (53, 318), (150, 292), (260, 330), (380, 300), (520, 336), (747, 306), (747, 360)])
        for i in range(12):
            self.a_rect(_mix((110, 150, 78), (66, 108, 54), i / 11.0), 53, 360 + i * 14, 694, 16)
        self.a_poly((112, 146, 92), [(290, yb + 30), (390, yb - 14), (690, yb - 14), (747, yb + 40), (747, yb + 80), (290, yb + 80)])
        self.a_palace(540, yb, 0.5 + 0.4 * p)
        self.a_poly(_mix((170, 142, 96), (196, 170, 120), p), [(60, 517), (300, 517), (558, yb), (522, yb)])
        self.a_lines((206, 180, 130), [(300, 517), (558, yb)], 2)
        for tx_, ty_, sc in ((120, 440, 1.3), (250, 410, 1.0), (690, 452, 1.4)):
            self.a_poly((86, 64, 40), [(tx_ - 6 * sc, ty_), (tx_ + 6 * sc, ty_), (tx_ + 3 * sc, ty_ - 44 * sc), (tx_ - 3 * sc, ty_ - 44 * sc)])
            self.a_circle((126, 150, 110), tx_, ty_ - 52 * sc, 28 * sc)
            self.a_circle((152, 176, 130), tx_ - 8 * sc, ty_ - 60 * sc, 15 * sc)
        for k in range(3):
            bx = (t * 2 + k * 260) % 800
            by = 160 + k * 24 + math.sin(t * 0.1 + k) * 8
            self.a_lines((60, 60, 70), [(bx - 7, by - 3), (bx, by), (bx + 7, by - 3)], 2)
        # Telemachus has gone on ahead to the palace gate
        if p < 0.45:
            u = p / 0.45
            self.a_man(300 + u * 225, 470 - u * (470 - (yb + 6)), (70, 112, 204), 1, math.sin(t * 0.4) * 3, 0, "down", 1.1, helmet=False)
        # the beggar walks the road home
        ox_ = 130 + p * 400
        oy_ = 505 - p * (505 - (yb + 46))
        os_ = 2.3 - 1.1 * p
        for k in range(3):
            self.a_circle((200, 176, 128), ox_ - 18 - k * 9, oy_ - 3 - k, max(1, int((5 - k) * os_ / 2.3)))
        self.a_odysseus(ox_, oy_, os_, "beggar", "down", 0, math.sin(t * 0.35) * 5 * os_ / 2.3)
        self.a_end()
        self.a_title("THE ROAD TO THE PALACE", (250, 232, 190))

    def anim_suitors_abuse(self):
        t = 540 - self.anim_timer
        p = t / 540.0
        G = 500
        SO, SA = 2.8, 3.0
        self.a_begin()
        self.a_hall(t, "laugh" if p > 0.28 else "listen", True)
        # the beggar shuffles in from the doorway
        if p < 0.3:
            ox_ = 100 + (p / 0.3) * 150
            walk = math.sin(t * 0.35) * 5
        else:
            ox_ = 250
            walk = 0
        flinch = max(0.0, 1 - (p - 0.6) / 0.1) if p >= 0.6 else 0.0
        duck = 1.0 if 0.74 <= p < 0.82 else 0.0
        lean = -12 * flinch + 10 * duck + (6 if p > 0.88 else 0)
        # Antinous winds up and hurls a footstool
        ax_ = 470
        a_arms = "up" if 0.34 <= p < 0.5 else ("fwd" if 0.5 <= p < 0.6 else "down")
        self.a_odysseus(ox_, G, SO, "beggar", "down", lean, walk)
        self.a_man(ax_, G, (130, 50, 150), -1, 0, 4 if a_arms == "up" else 0, a_arms, SA, helmet=False)
        self.a_line(GOLD, ax_ - 5 * SA, G - 14 * SA, ax_ + 5 * SA, G - 14 * SA, 4)
        if 0.34 <= p < 0.5:
            self.a_stool(ax_, G - 43 * SA - 10, 0.3)
        elif 0.5 <= p < 0.6:
            u = (p - 0.5) / 0.1
            x0, y0 = ax_ - 36, G - 26 * SA + 5
            x1, y1 = ox_ + 18, G - 26 * SO + 6
            self.a_stool(x0 + (x1 - x0) * u, y0 + (y1 - y0) * u - math.sin(u * math.pi) * 50, u * 9)
        elif p >= 0.6:
            k = min(1.0, (p - 0.6) / 0.1)
            if k < 1:
                self.a_glow(ox_ + 18, G - 26 * SO + 6, 40 * (1 - k) + 10, (255, 232, 150), int(180 * (1 - k)))
            bounce = abs(math.sin(k * math.pi * 1.5)) * 20 * (1 - k)
            self.a_stool(ox_ + 44 + k * 18, G - 6 - bounce, 1.7 if k >= 1 else k * 6)
        # more scraps are flung: bread, and an ox's hoof that sails over his ducked head
        for n, (sp, srcx) in enumerate(((0.64, 350), (0.70, 560), (0.78, 420))):
            u = (p - sp) / 0.08
            if 0 <= u < 1:
                bx = srcx + (ox_ + 8 - srcx) * u
                by = 340 + (G - 70 - 340) * u - math.sin(u * math.pi) * 50
                self.a_ellipse((214, 168, 92), bx - 8, by - 5, 16, 10)
                self.a_ellipse((236, 196, 120), bx - 6, by - 4, 8, 4)
            elif u >= 1:
                self.a_ellipse((214, 168, 92), ox_ + 16 + n * 20, min(G - 6, G - 70 + (u - 1) * 160) - 5, 16, 10)
        uh = (p - 0.74) / 0.1
        if 0 <= uh < 1:
            hx_ = 640 + (330 - 640) * uh
            hy_ = 340 + (216 - 340) * uh - math.sin(uh * math.pi) * 30
            self.a_ellipse((120, 84, 52), hx_ - 12, hy_ - 7, 24, 14)
            self.a_rect((226, 214, 190), hx_ - 14, hy_ - 4, 6, 8)
        elif uh >= 1:
            self.a_ellipse((120, 84, 52), 318, min(G - 14, 216 + (uh - 1) * 300), 24, 14)
        # Telemachus, fists clenched, can only watch
        self.a_man(712, G, (70, 112, 204), -1, 0, 6 if p > 0.6 else 0, "down", 2.4, helmet=False)
        self.a_end()
        self.a_title("THE SUITORS MOCK THE BEGGAR", (255, 170, 120))

    def a_contest_panel(self, scene, t, wipe):
        x0, y0, w, h = 270, 148, 260, 126
        self.a_rect((40, 28, 18), x0 - 6, y0 - 6, w + 12, h + 12)
        self.a_rect((228, 206, 152), x0 - 6, y0 - 6, w + 12, h + 12, 3)
        self.a_rect((58, 44, 36), x0, y0, w, h)
        if scene == 0:       # the great bow of Odysseus
            self.a_glow(400, 212, 70, (255, 220, 140), 130)
            pts = [(398 + 30 * math.sin(u / 10.0 * math.pi), 160 + u * 10.4) for u in range(11)]
            self.a_lines((132, 86, 40), pts, 7)
            self.a_line((236, 230, 210), 398, 160, 398, 264, 2)
            self.a_circle(GOLD, 413, 212, 5)
            self.a_poly((132, 86, 40), [(398, 160), (388, 154), (398, 166)])
            self.a_poly((132, 86, 40), [(398, 264), (388, 270), (398, 258)])
            self.a_rect((110, 74, 36), 462, 196, 20, 58)
            for k in range(4):
                self.a_line((214, 184, 124), 466 + k * 4, 196, 464 + k * 5, 180, 2)
                self.a_poly((200, 50, 50), [(464 + k * 5, 180), (460 + k * 5, 172), (468 + k * 5, 174)])
        elif scene == 1:     # twelve axes, lashed together in six pairs
            self.a_rect((86, 66, 48), x0, 258, w, 16)
            for k in range(6):
                x = 296 + k * 36
                for d in (0, 10):
                    self.a_line((120, 86, 50), x + d, 262, x + d, 214, 3)
                    self.a_poly((190, 194, 204), [(x + d, 196), (x + d + 8, 190), (x + d + 8, 214), (x + d, 208)])
                    self.a_ellipse((220, 224, 234), x + d - 4, 192, 8, 20, 2)
                self.a_line((204, 164, 92), x - 2, 240, x + 12, 244, 3)
                self.a_line((204, 164, 92), x - 2, 228, x + 12, 232, 3)
        else:                # the arrow flies true through every ring
            self.a_rect((86, 66, 48), x0, 258, w, 16)
            for k in range(6):
                x = 346 + k * 28
                for d in (0, 8):
                    self.a_line((120, 86, 50), x + d, 262, x + d, 244, 3)
                    self.a_ellipse((220, 224, 234), x + d - 4, 214, 8, 30, 2)
                self.a_line((204, 164, 92), x - 1, 252, x + 10, 255, 3)
            self.a_man(300, 270, (196, 62, 56), 1, 0, 0, "fwd", 1.9, helmet=False)
            self.a_lines((132, 86, 40), [(334 + 10 * math.sin(u / 6.0 * math.pi), 200 + u * 11) for u in range(7)], 4)
            cyc = (t * 3) % 260
            ax = min(520, 334 + cyc)
            self.a_line((214, 184, 124), ax - 38, 229, ax, 229, 4)
            self.a_poly((196, 196, 206), [(ax + 10, 229), (ax, 223), (ax, 235)])
            self.a_glow(ax, 229, 16, (255, 236, 160), 150)
            self.a_circle((196, 52, 52), 526, 229, 9)
        if wipe < 0.08:
            self.a_rect((255, 255, 255), x0, y0, int(w * (1 - wipe / 0.08)) + 1, h)

    def anim_penelope_contest(self):
        t = 600 - self.anim_timer
        p = t / 600.0
        G = 496
        mood = "cheer" if p >= 0.62 else "listen"
        self.a_begin()
        self.a_hall(t, mood, True)
        # the beggar sits quietly by the door, listening to every word
        self.a_line((110, 80, 50), 160, 502, 152, 340, 5)
        self.a_sit(100, 502, (112, 98, 78), 1, 2.6, 5, (13, 12), (14, 11), (190, 190, 190), (196, 196, 196))
        # Penelope's dais
        self.a_rect((172, 152, 120), 410, 496, 300, 12)
        self.a_rect((196, 176, 140), 400, 508, 320, 9)
        px = 790 - (p / 0.15) * 250 if p < 0.15 else 540
        self.a_man(450, G, (70, 112, 204), 1, 0, 0, "down", 2.7, helmet=False)
        arm = 0.0
        if 0.16 <= p < 0.62:
            arm = 1.0 + math.sin(t * 0.12) * 0.12
        elif p >= 0.62:
            arm = 0.3
        self.a_penelope(px + 108, G, 1.9, -1, 0.0, (176, 150, 120), False)
        self.a_penelope(px + 56, G, 1.9, -1, 0.0, (170, 190, 150), False)
        self.a_penelope(px, G, 2.2, -1, arm)
        if 0.18 <= p < 0.9:
            scene = 0 if p < 0.4 else (1 if p < 0.62 else 2)
            start = (0.18, 0.4, 0.62)[scene]
            self.a_contest_panel(scene, t, min(1.0, (p - start) / 0.22))
            for bx, by, br in ((522, 296, 6), (530, 332, 9), (538, 366, 12)):
                self.a_circle((236, 228, 200), bx, by, br)
                self.a_circle((140, 120, 80), bx, by, br, 2)
        self.a_end()
        self.a_title("PENELOPE ANNOUNCES A CONTEST", (230, 210, 255))

    # ==================================================================
    #  THE TEST OF THE BOW
    # ==================================================================
    def a_axes_row(self, x0, x1, y, s=1.0, flash=None):
        """Twelve axes planted in a row and lashed together in six pairs. Their rings sit at y - 52*s.
        If `flash` is an x position, every ring the arrow has already passed through glows gold."""
        ring_y = y - 52 * s
        for k in range(6):
            x = x0 + (x1 - x0) * k / 5.0
            self.a_rect((90, 60, 34), x - 9 * s, y - 2 * s, 18 * s, 4 * s)
            for d in (-5, 5):
                hx = x + d * s
                self.a_line((120, 84, 48), hx, y, hx, ring_y + 8 * s, max(2, int(3 * s)))
                lit = flash is not None and flash > hx
                self.a_ellipse((60, 52, 46), hx - 3.5 * s, ring_y - 9 * s, 7 * s, 18 * s)
                self.a_ellipse((255, 226, 130) if lit else (204, 208, 220), hx - 3.5 * s, ring_y - 9 * s, 7 * s, 18 * s, 2)
                if lit:
                    self.a_glow(hx, ring_y, 14 * s, (255, 226, 130), 130)
            for ry in (y - 14 * s, y - 34 * s):
                self.a_line((204, 164, 92), x - 5 * s, ry, x + 5 * s, ry + 3 * s, max(2, int(2.5 * s)))
                self.a_circle((172, 132, 62), x, ry + 1.5 * s, max(2, 3 * s))

    def a_great_bow(self, cx, cy, L, v, pull=0.0):
        """The great bow of Odysseus, held upright. v: 0 = unstrung (string slack), 1 = fully strung."""
        tip_off = 34 - 54 * v
        pts = []
        for k in range(-8, 9):
            u = k / 8.0
            pts.append((cx + 20 * (1 - u * u) + tip_off * u * u, cy + u * L))
        self.a_lines((126, 82, 38), pts, 9)
        self.a_lines((178, 130, 70), pts, 3)
        top, bot = pts[0], pts[-1]
        self.a_circle(GOLD, cx + 20, cy, 5)
        if v >= 0.98:
            nock = (cx - 8 - pull, cy)
            self.a_lines((240, 234, 214), [top, nock, bot], 2)
        else:
            slack = 1 - v
            loop = (bot[0] + 56 * slack, bot[1] - 36 * slack)
            self.a_line((240, 234, 214), top[0], top[1], loop[0], loop[1], 2)
            self.a_circle((236, 198, 158), loop[0], loop[1], 5)

    def anim_suitors_fail(self):
        t = 600 - self.anim_timer
        p = t / 600.0
        G = 500
        self.a_begin()
        self.a_hall(t, "listen", True)
        self.a_axes_row(400, 700, 498, 1.1)
        self.a_line((110, 80, 50), 160, 502, 152, 340, 5)
        self.a_sit(100, 502, (112, 98, 78), 1, 2.6, 5, (13, 12), (14, 11), (190, 190, 190), (196, 196, 196))
        tunics = [(190, 60, 60), (30, 130, 90), (210, 150, 40), (130, 50, 150)]
        scales = [2.8, 2.8, 2.8, 3.1]
        span = 0.235
        # four suitors try in turn; none can string the bow
        for k in range(4):
            u = (p - (0.03 + k * span)) / span
            if u < 0 or u >= 1.0:
                continue
            S = scales[k]
            hand_y = G - 21 * S
            if u < 0.14:
                x = 560 - (u / 0.14) * 300
                self.a_man(x, G, tunics[k], -1, math.sin(t * 0.4) * 5, 0, "fwd", S, helmet=False)
                self.a_great_bow(x - 30, hand_y, 70, 0.0)
            elif u < 0.62:
                w = (u - 0.14) / 0.48
                shake = math.sin(t * 0.9) * 3 * w
                skin = _mix((236, 198, 158), (232, 112, 100), w)
                self.a_man(260, G, tunics[k], -1, 0, 6 + shake, "fwd", S, skin=skin, helmet=False)
                self.a_great_bow(230 + shake, hand_y, 70, min(0.6, w * 0.7))
                for q in range(3):
                    if (t // 7 + q) % 3 == 0:
                        self.a_circle((170, 210, 255), 250 + q * 10 + shake, G - 36 * S + q * 6, 3)
            elif u < 0.78:
                sub = (u - 0.62) / 0.16
                if sub < 0.4:
                    for ang in range(8):
                        a = ang * 0.785
                        self.a_line((255, 236, 140), 230 + math.cos(a) * 14, hand_y + math.sin(a) * 14, 230 + math.cos(a) * 36, hand_y + math.sin(a) * 36, 3)
                self.a_great_bow(230 + sub * 40, hand_y + sub * 40, 70, 0.0)
                self.a_tumble(260 - sub * 45, G - 17 * S + sub * (17 * S - 12), -sub * 1.55, tunics[k], S / 2.0)
            else:
                sub = (u - 0.78) / 0.22
                self.a_lines((126, 82, 38), [(196 + j * 11, G - 8 - 8 * math.sin(j / 6.0 * math.pi)) for j in range(7)], 7)
                self.a_man(215 + sub * 400, G, tunics[k], 1, math.sin(t * 0.4) * 4, 7, "down", S, helmet=False)
        self.a_end()
        self.a_title("THE SUITORS CANNOT STRING THE BOW", (255, 200, 140))

    def anim_odysseus_steps_up(self):
        t = 480 - self.anim_timer
        p = t / 480.0
        G = 500
        mood = "laugh" if 0.15 <= p < 0.58 else "listen"
        self.a_begin()
        self.a_hall(t, mood, True)
        self.a_axes_row(450, 700, 498, 1.1)
        # the great bow waits on its rack until Eumaeus fetches it
        self.a_rect((80, 54, 30), 380, 458, 8, 42)
        self.a_rect((80, 54, 30), 470, 458, 8, 42)
        if p < 0.52:
            pts = [(380 + k * 12, 452 - 8 * math.sin(k / 8.0 * math.pi)) for k in range(9)]
            self.a_lines((126, 82, 38), pts, 9)
            self.a_lines((178, 130, 70), pts, 3)
        # the beggar rises from his seat by the door and asks to try
        if p < 0.08:
            self.a_line((110, 80, 50), 160, 502, 152, 340, 5)
            self.a_sit(100, 502, (112, 98, 78), 1, 2.6, 5, (13, 12), (14, 11), (190, 190, 190), (196, 196, 196))
            ox_ = 100
        else:
            u = min(1.0, (p - 0.08) / 0.32)
            ox_ = 100 + u * 200
            has_bow = p >= 0.72
            self.a_odysseus(ox_, G, 2.8, "beggar", "fwd" if has_bow else "down", 0, math.sin(t * 0.35) * 5 if u < 1.0 else 0)
            if has_bow:
                self.a_great_bow(ox_ + 28, G - 21 * 2.8, 70, 0.0)
        # Antinous bellows his outrage
        shout = 0.15 <= p < 0.6
        self.a_man(560 - (math.sin(t * 0.3) * 4 if shout else 0), G, (130, 50, 150), -1, 0, -5 if shout else 0, "up" if shout else "down", 3.0, helmet=False)
        # Telemachus steps forward to speak up for the stranger
        if p < 0.2:
            tx = 620
        elif p < 0.34:
            tx = 620 - (p - 0.2) / 0.14 * 260
        else:
            tx = 360
        self.a_man(tx, G, (70, 112, 204), 1, math.sin(t * 0.4) * 5 if 0.2 <= p < 0.34 else 0, 0, "up" if 0.34 <= p < 0.56 else "down", 2.6, helmet=False)
        # Eumaeus carries the bow to his master
        if 0.40 <= p < 0.72:
            if p < 0.56:
                ex = 760 - (p - 0.40) / 0.16 * 320
                carrying = False
            else:
                ex = 440 - (p - 0.56) / 0.16 * 110
                carrying = True
            self.a_man(ex, G, (98, 128, 72), -1, math.sin(t * 0.4) * 5, 0, "fwd" if carrying else "down", 2.6, helmet=False, hair=(150, 150, 150))
            if carrying:
                self.a_great_bow(ex - 28, G - 21 * 2.6, 70, 0.0)
        elif p >= 0.72:
            ex = 330 - min(1.0, (p - 0.72) / 0.2) * 210
            self.a_man(ex, G, (98, 128, 72), -1, math.sin(t * 0.4) * 5 if p < 0.92 else 0, 0, "down", 2.6, helmet=False, hair=(150, 150, 150))
        # the doors are barred, sealing the suitors in
        if p >= 0.7:
            k = min(1.0, (p - 0.7) / 0.22)
            wood = (74, 50, 30)
            self.a_rect(wood, 63, 190, 42 * k + 1, 230)
            self.a_rect(wood, 147 - 42 * k, 190, 42 * k + 1, 230)
            self.a_ellipse(wood, 63 + 42 * (1 - k), 168, 84 * k + 2, 46)
            if k >= 1.0:
                self.a_rect((64, 64, 72), 58, 312, 96, 10)
                for rx in (68, 100, 140):
                    self.a_circle((140, 140, 150), rx, 317, 3)
            self.a_fade((10, 6, 2), int(60 * k))
        self.a_end()
        self.a_title("ODYSSEUS ASKS TO TRY THE BOW", (255, 210, 150))

    def anim_odysseus_shoots(self):
        t = 600 - self.anim_timer
        p = t / 600.0
        G = 500
        mood = "shock" if p >= 0.72 else "listen"
        self.a_begin()
        self.a_hall(t, mood, "barred")
        # the target post at the far end of the hall
        self.a_rect((84, 56, 32), 596, 396, 18, 104)
        self.a_circle((200, 60, 50), 605, 440, 12)
        self.a_circle(WHITE, 605, 440, 7)
        self.a_circle((200, 60, 50), 605, 440, 3)
        released = p >= 0.30
        if p < 0.22:
            pull = (p / 0.22) * 28
        elif p < 0.30:
            pull = 28 + math.sin(t * 1.1) * 1.5
        else:
            pull = 0.0
        u = max(0.0, min(1.0, (p - 0.30) / 0.42))
        ax = 272 + u * 332
        self.a_axes_row(330, 540, 498, 1.1, ax if released else None)
        self.a_man(130, G, (70, 112, 204), 1, 0, 0, "up" if p >= 0.8 else "down", 2.6, helmet=False)
        self.a_odysseus(205, G, 3.0, "beggar", "fwd", 3)
        self.a_great_bow(220, 440, 78, 1.0, pull)
        nock = (220 - 8 - pull, 440)
        self.a_line((236, 198, 158), 205, 422, nock[0], nock[1], 6)
        if not released:
            self.a_line((214, 184, 124), nock[0], nock[1], 272, 440, 3)
            self.a_poly((196, 196, 206), [(282, 440), (272, 435), (272, 445)])
        else:
            wob = math.sin(t * 1.8) * 2 * max(0.0, 1 - (p - 0.72) / 0.12) if p >= 0.72 else 0
            tail = ax - 40
            self.a_line((214, 184, 124), tail, 440 + wob, ax, 440, 4)
            self.a_poly((196, 196, 206), [(ax + 10, 440), (ax, 434), (ax, 446)])
            self.a_line((200, 50, 50), tail, 440 + wob, tail - 9, 434 + wob, 2)
            self.a_line((200, 50, 50), tail, 440 + wob, tail - 9, 446 + wob, 2)
            if p < 0.72:
                self.a_glow(ax, 440, 22, (255, 236, 160), 150)
                for q in range(5):
                    self.a_line((255, 255, 255), ax - 44 - q * 16, 440 + (q - 2) * 3, ax - 52 - q * 16, 440 + (q - 2) * 3, 1)
        if 0.72 <= p < 0.8:
            k = (p - 0.72) / 0.08
            self.a_glow(604, 440, 50 * (1 - k) + 12, (255, 236, 160), int(200 * (1 - k)))
        self.a_end()
        self.a_title("THE ARROW FLIES TRUE!", GOLD)

    # ---------- the two mini games ----------
    def begin_string_game(self):
        self.state = "STRING_GAME"
        self.mg_phase = "intro"
        self.mg_value = 0.0
        self.mg_tap = 0
        self.mg_timer = 0

    def begin_timing_game(self):
        self.state = "TIMING_GAME"
        self.mg_phase = "intro"
        self.mg_attempts = 0
        self.mg_timer = 0
        self.new_aim_attempt(False)

    def new_aim_attempt(self, play=True):
        self.mg_gh = 0.2
        self.mg_gtop = random.uniform(0.08, 0.72)
        self.mg_line = random.uniform(0.0, 1.0)
        self.mg_dir = random.choice([-1, 1])
        self.mg_off = 0.0
        if play:
            self.mg_phase = "play"

    def draw_frame_box(self):
        ox, oy = self.shake_offset
        pygame.draw.rect(self.screen, WHITE, (50 + ox, 80 + oy, WIDTH - 100, HEIGHT - 160), 3)

    def draw_minigame_card(self, title, body, tk):
        ox, oy = self.shake_offset
        self.a_fade((0, 0, 0), 150)
        self.a_rect((24, 18, 12), 130, 118, 540, 360)
        self.a_rect(GOLD, 130, 118, 540, 360, 3)
        self.a_title(title, GOLD, 132)
        self.draw_text(body, self.font, WHITE, WIDTH // 2 + ox, 190 + oy, center=True, max_width=490)
        if (tk // 25) % 2 == 0:
            self.draw_text("Press SPACE to begin", self.font, CRT_GREEN, WIDTH // 2 + ox, 440 + oy, center=True)

    def draw_string_game(self):
        tk = pygame.time.get_ticks() // 16
        ox, oy = self.shake_offset
        G = 500
        v = self.mg_value / 100.0
        self.draw_frame_box()
        self.a_begin()
        self.a_hall(tk, "listen", "barred")
        playing = self.mg_phase in ("play", "done")
        strain = math.sin(tk * 0.8) * (1 + 3 * v) if self.mg_phase == "play" else 0
        lean = 6 + self.mg_tap * 0.8 + strain * 0.4
        self.a_odysseus(215, G, 3.2, "beggar", "fwd", lean)
        self.a_great_bow(244 + strain * 0.5, 430, 80, v)
        if self.mg_tap > 0:
            self.a_glow(264, 430, 44, (255, 230, 150), 24 * self.mg_tap)
        if self.mg_phase == "play":
            for q in range(4):
                if (tk // 6 + q) % 3 == 0:
                    self.a_circle((170, 210, 255), 200 + q * 9, 392 + q * 5 + (tk % 12), 3)
        if self.mg_phase == "done":
            self.a_fade((255, 230, 150), 60 + int(math.sin(tk * 0.2) * 30))
        self.a_end()
        if self.mg_phase == "intro":
            self.draw_minigame_card(
                "STRING THE BOW",
                "No suitor could bend the great bow. Only its master can.| |Tap the SPACEBAR as fast as you can to bend the bow and slip the string over its tip.| |Keep tapping! If you stop, the bow slowly straightens again.",
                tk)
            return
        self.a_title("STRING THE BOW", GOLD, 100)
        if self.mg_phase == "play" and (tk // 12) % 2 == 0:
            self.a_title("TAP SPACE!", WHITE, 140)
        elif self.mg_phase == "done":
            self.a_title("THE BOW IS STRUNG!", GOLD, 140)
        bx, by, bw, bh = 200, 546, 400, 26
        self.draw_text("BOW TENSION", self.small_font, WHITE, WIDTH // 2 + ox, 524 + oy, center=True)
        pygame.draw.rect(self.screen, (30, 30, 36), (bx + ox, by + oy, bw, bh))
        pygame.draw.rect(self.screen, _mix((220, 70, 40), (90, 230, 90), v), (bx + ox, by + oy, max(1, int(bw * v)), bh))
        pygame.draw.rect(self.screen, WHITE, (bx - 3 + ox, by - 3 + oy, bw + 6, bh + 6), 3)

    def draw_timing_game(self):
        tk = pygame.time.get_ticks() // 16
        ox, oy = self.shake_offset
        G = 500
        phase = self.mg_phase
        self.draw_frame_box()
        self.a_begin()
        self.a_hall(tk, "listen", "barred")
        self.a_rect((84, 56, 32), 596, 396, 18, 104)
        self.a_circle((200, 60, 50), 605, 440, 12)
        self.a_circle(WHITE, 605, 440, 7)
        self.a_circle((200, 60, 50), 605, 440, 3)
        flying = phase in ("hit", "miss")
        u = min(1.0, (80 - self.mg_timer) / 40.0) if flying else 0.0
        ax = 270 + u * 334
        ay = 440 + (max(-300.0, min(60.0, self.mg_off * 330.0)) * u * u if phase == "miss" else 0)
        self.a_axes_row(330, 540, 498, 1.1, ax if phase == "hit" else None)
        self.a_odysseus(205, G, 3.0, "beggar", "fwd", 3)
        pull = 0.0 if flying else 28
        self.a_great_bow(220, 440, 78, 1.0, pull)
        nock = (220 - 8 - pull, 440)
        self.a_line((236, 198, 158), 205, 422, nock[0], nock[1], 6)
        if not flying:
            self.a_line((214, 184, 124), nock[0], nock[1], 272, 440, 3)
            self.a_poly((196, 196, 206), [(282, 440), (272, 435), (272, 445)])
        else:
            ang = math.atan2(ay - 440, max(1.0, ax - 270))
            tx, ty = ax - math.cos(ang) * 40, ay - math.sin(ang) * 40
            self.a_line((214, 184, 124), tx, ty, ax, ay, 4)
            self.a_poly((196, 196, 206), [(ax + math.cos(ang) * 10, ay + math.sin(ang) * 10), (ax - math.sin(ang) * 6, ay + math.cos(ang) * 6), (ax + math.sin(ang) * 6, ay - math.cos(ang) * 6)])
            self.a_line((200, 50, 50), tx, ty, tx - 9, ty - 6, 2)
            self.a_line((200, 50, 50), tx, ty, tx - 9, ty + 6, 2)
            if u < 1.0:
                self.a_glow(ax, ay, 20, (255, 236, 160), 130)
        # the aiming meter
        mx, my, mw, mh = 650, 130, 46, 330
        self.a_rect((20, 18, 16), mx - 8, my - 8, mw + 16, mh + 16)
        self.a_rect((26, 26, 36), mx, my, mw, mh)
        for k in range(1, 10):
            self.a_line((70, 70, 84), mx, my + mh * k / 10.0, mx + 10, my + mh * k / 10.0, 2)
        gtop = my + self.mg_gtop * mh
        self.a_rect((60, 210, 90), mx, gtop, mw, self.mg_gh * mh)
        self.a_rect((200, 255, 210), mx, gtop, mw, self.mg_gh * mh, 3)
        ly = my + self.mg_line * mh
        self.a_rect((0, 0, 0), mx - 12, ly - 4, mw + 24, 8)
        self.a_rect((255, 255, 255), mx - 12, ly - 2, mw + 24, 5)
        self.a_poly((255, 70, 60), [(mx - 14, ly - 8), (mx - 2, ly), (mx - 14, ly + 8)])
        self.a_poly((255, 70, 60), [(mx + mw + 14, ly - 8), (mx + mw + 2, ly), (mx + mw + 14, ly + 8)])
        self.a_rect((20, 18, 16), mx - 8, my - 8, mw + 16, mh + 16, 3)
        if phase == "hit":
            self.a_fade((255, 230, 150), 40)
        self.a_end()
        if phase == "intro":
            self.draw_minigame_card(
                "TAKE YOUR AIM",
                "A line slides up and down the meter. Press SPACE when the line is inside the green box to loose your arrow.| |You may try as many times as you like.",
                tk)
            return
        self.a_title("TAKE YOUR AIM", GOLD, 100)
        if phase == "play":
            self.draw_text("Press SPACE when the line is in the green box!", self.font, BLACK, WIDTH // 2 - 60 + ox + 2, 148 + oy, center=True)
            self.draw_text("Press SPACE when the line is in the green box!", self.font, WHITE, WIDTH // 2 - 60 + ox, 146 + oy, center=True)
        elif phase == "miss":
            self.a_title("MISSED!", RED, 140)
            self.draw_text("Your arrow flies wide. Try again!", self.font, WHITE, WIDTH // 2 - 60 + ox, 190 + oy, center=True)
        elif phase == "hit":
            self.a_title("A PERFECT SHOT!", GOLD, 140)
        self.draw_text("Attempt " + str(max(1, self.mg_attempts)), self.small_font, WHITE, 90 + ox, 492 + oy)

    # ==================================================================
    #  THE DEATH OF ANTINOUS
    # ==================================================================
    def anim_antinous_killed(self):
        t = 540 - self.anim_timer
        p = t / 540.0
        G = 500
        mood = "shock" if p >= 0.56 else "listen"
        self.a_begin()
        self.a_hall(t, mood, "barred")
        self.a_axes_row(330, 540, 498, 1.1, 9999)
        # Odysseus casts off his rags
        king = p >= 0.27
        pull = 0.0
        if 0.34 <= p < 0.5:
            pull = (p - 0.34) / 0.12 * 28
        elif 0.5 <= p < 0.56:
            pull = 0.0
        if 0.27 <= p:
            for q in range(7):
                self.a_line((196, 150, 70), 168 + q * 11, G - 4 - (q % 3) * 3, 188 + q * 11, G - 10 - (q % 3) * 3, 2)
        if 0.27 <= p < 0.42:
            k = (p - 0.27) / 0.15
            for q in range(5):
                rx = 190 + q * 12 + math.sin(q * 2.0) * 10 * k
                ry = 420 + k * 70 + q * 4
                self.a_poly((124, 110, 88), [(rx, ry), (rx + 14, ry + 6), (rx + 4, ry + 16)])
        elif p >= 0.42:
            for q in range(5):
                self.a_poly((124, 110, 88), [(176 + q * 12, 492), (190 + q * 12, 497), (180 + q * 12, 506)])
        self.a_man(130, G, (70, 112, 204), 1, 0, 0, "up" if p >= 0.8 else "down", 2.6, helmet=False)
        if p >= 0.6:
            self.a_line((220, 220, 232), 150, 440, 178, 410, 4)
        arms = "fwd" if p >= 0.3 else "down"
        self.a_odysseus(205, G, 3.0, "king" if king else "beggar", arms, 3 if p >= 0.3 else 0)
        self.a_great_bow(220, 440, 78, 1.0, pull)
        if 0.3 <= p < 0.5:
            nock = (212 - pull, 440)
            self.a_line((236, 198, 158), 205, 422, nock[0], nock[1], 6)
            self.a_line((214, 184, 124), nock[0], nock[1], 272, 440, 3)
            self.a_poly((196, 196, 206), [(282, 440), (272, 435), (272, 445)])
        # Antinous raises his golden cup... and the arrow finds him
        ax_ = 480
        if p < 0.56:
            cheer = math.sin(t * 0.3) * 3
            self.a_man(ax_, G, (130, 50, 150), -1, 0, cheer, "up", 3.1, helmet=False)
            self.a_line(GOLD, ax_ - 5 * 3.1, G - 14 * 3.1, ax_ + 5 * 3.1, G - 14 * 3.1, 4)
            cx_, cy_ = ax_ - 8 * 3.1, G - 43 * 3.1 - 8
            self.a_rect(GOLD, cx_ - 7, cy_ - 8, 14, 16)
            self.a_rect((150, 20, 44), cx_ - 6, cy_ - 8, 12, 5)
        else:
            u2 = min(1.0, (p - 0.56) / 0.2)
            self.a_tumble(ax_ + u2 * 80, G - 17 * 3.1 + u2 * (17 * 3.1 - 12), u2 * 1.5, (130, 50, 150), 3.1)
            uc = min(1.0, (p - 0.56) / 0.14)
            cx_ = 466 - uc * 70
            cy_ = 340 + uc * 146 - math.sin(uc * math.pi) * 60
            if uc < 1.0:
                self.a_rect(GOLD, cx_ - 7, cy_ - 8, 14, 16)
                for q in range(8):
                    a = q * 0.8 + uc * 5
                    self.a_circle((150, 20, 44), cx_ + math.cos(a) * 16 * uc, cy_ + math.sin(a) * 12 * uc, 3)
            else:
                self.a_ellipse((120, 20, 36), 380, 480, 60, 16)
                self.a_rect(GOLD, 398, 484, 16, 8)
        # the arrow itself
        if 0.5 <= p < 0.56:
            u = (p - 0.5) / 0.06
            ax = 272 + u * 196
            ay = 440 - u * 40
            self.a_line((214, 184, 124), ax - 40, ay + 8, ax, ay, 4)
            self.a_poly((196, 196, 206), [(ax + 10, ay - 2), (ax, ay - 7), (ax, ay + 5)])
            self.a_glow(ax, ay, 22, (255, 236, 160), 150)
        if 0.56 <= p < 0.62:
            self.a_glow(468, 400, 60, (255, 236, 160), int(200 * (1 - (p - 0.56) / 0.06)))
        if 0.24 <= p < 0.30:
            self.a_fade((255, 255, 255), 235 * (1 - abs(p - 0.27) / 0.03))
        if p >= 0.8:
            self.a_fade((130, 0, 10), int(70 * min(1.0, (p - 0.8) / 0.15)))
        self.a_end()
        self.a_title("THE FIRST ARROW FINDS ANTINOUS", (255, 190, 150))

    # ==================================================================
    #  THE SLAUGHTER OF THE SUITORS - top-down battle (after Book 22)
    # ==================================================================
    def begin_battle(self):
        pygame.mouse.set_visible(False)
        self.state = "BATTLE"
        self.bt = {
            "phase": "intro", "wave": -1, "kills": 0, "wave_kills0": 0,
            "hp": BT_MAXHP, "maxhp": BT_MAXHP, "px": 400.0, "py": 455.0, "inv": 0, "flash": 0,
            "roll": 0, "rcd": 0, "rdx": 0.0, "rdy": 0.0, "cd": 0, "draw": 0, "aim": 0.0,
            "aegis": 0.0, "aegis_fx": 0,
            "shield": False, "shield_fly": 0, "helmet": False, "helmet_ready": False, "wp": None, "swing": 0, "swing_cd": 0, "heal_kills": 0,
            "tele_used": False, "eum_used": False, "tele_used0": False, "eum_used0": False,
            "allies": [], "sp": [], "athena_left": 0,
            "enemies": [], "arrows": [], "eproj": [], "corpses": [], "fx": [],
            "queue": [], "spawn_t": 0, "timer": 0, "banner_t": 0, "banner": ("", ""), "clear_t": 0, "note": "", "note_t": 0,
        }

    def bt_start_wave(self, n, retry=False):
        b = self.bt
        w = BT_WAVES[n]
        b["wave"] = n
        if retry:
            b["tele_used"], b["eum_used"] = b["tele_used0"], b["eum_used0"]
        else:
            b["wave_kills0"] = b["kills"]
            b["tele_used0"], b["eum_used0"] = b["tele_used"], b["eum_used"]
        q = []
        for kind, cnt in w["spawn"]:
            q += [kind] * cnt
        random.shuffle(q)
        named = list(w.get("named", []))
        if named:
            step = len(q) / float(len(named) + 1)
            for i, nm in enumerate(named):          # the book's order is kept
                q.insert(min(len(q), int(step * (i + 1)) + i), nm)
        b["queue"] = list(w.get("first", [])) + q + list(w.get("last", []))
        b["enemies"], b["eproj"], b["arrows"], b["sp"], b["allies"] = [], [], [], [], []
        b["athena_left"] = w.get("athena", 0)
        b["helmet_ready"] = b["helmet"]
        b["spawn_t"] = 80
        b["phase"] = "play"
        b["banner"] = (w["title"], w["sub"])
        b["banner_t"] = 230
        if w.get("aegis"):
            b["aegis_fx"] = 30
            self.shake_timer = 14

    def bt_begin_sword_wave(self):
        b = self.bt
        b["hp"] = b["maxhp"]
        b["inv"] = 60
        self.bt_start_wave(3)

    def bt_sparks(self, x, y, col=(255, 236, 160), n=6, sp=3.0):
        b = self.bt
        for _ in range(n):
            a = random.random() * 6.28
            b["fx"].append({"x": x, "y": y, "vx": math.cos(a) * sp, "vy": math.sin(a) * sp, "ttl": 16, "col": col, "sz": 3})

    def bt_spawn(self, kind):
        b = self.bt
        far = [s for s in BT_SPAWNS if math.hypot(s[0] - b["px"], s[1] - b["py"]) > 230] or BT_SPAWNS
        x, y = random.choice(far)
        if kind in BT_NAMED:
            base, name, hp = BT_NAMED[kind]
        else:
            base, name, hp = kind, "", {"sword": 1, "armed": 2, "panic": 1}[kind]
        sp = {"sword": 1.45, "armed": 1.3, "panic": 2.0, "leodes": 0.0}[base]
        if kind == "amphinomus":
            sp = 2.1
        r = 14 if kind == "agelaus" else 12
        special = {"eurymachus": (60, 90, 200), "amphinomus": (200, 90, 60), "leodes": (150, 150, 176), "agelaus": (212, 164, 44)}
        col = special.get(kind) or random.choice(BT_SUITOR_COLS)
        wave = BT_WAVES[b["wave"]]
        named = kind in BT_NAMED
        b["enemies"].append({"k": kind, "base": base, "name": name, "x": float(x), "y": float(y), "r": r, "hp": hp, "mhp": hp, "sp": sp,
                             "cd": random.randint(60, 150), "tele": 0, "flash": 0, "kx": 0.0, "ky": 0.0, "stun": 0, "blk": 0,
                             "face": 0.0, "col": col, "ph": random.random() * 6.28, "state": 0, "st": 0, "dx": 0.0, "dy": 0.0,
                             "table": bool(wave.get("tables")) and base == "sword" and not named,
                             "shield": base == "armed"})
        self.bt_sparks(x, y, (255, 236, 170), 8, 2.2)

    def bt_shield_blocks(self, ang_to_source, half_arc):
        b = self.bt
        if not b["shield"] or b["roll"] > 0:
            return False
        diff = abs((ang_to_source - b["aim"] + math.pi) % (2 * math.pi) - math.pi)
        return diff <= half_arc

    def bt_damage(self, e, dmg, ang, by_player=True, ignore_guard=False):
        b = self.bt
        if not ignore_guard and (e["table"] or e["shield"]):
            if abs(((ang - e["face"]) % (2 * math.pi)) - math.pi) < 1.15:      # struck from the front
                if e["table"]:
                    e["table"] = False
                    self.bt_sparks(e["x"] + math.cos(e["face"]) * 14, e["y"] + math.sin(e["face"]) * 14, (176, 126, 74), 10, 3.0)
                else:
                    e["shield"] = False
                    self.bt_sparks(e["x"] + math.cos(e["face"]) * 14, e["y"] + math.sin(e["face"]) * 14, (255, 236, 160), 8, 3.0)
                e["flash"] = 4
                e["kx"] += math.cos(ang) * 2.0
                e["ky"] += math.sin(ang) * 2.0
                return
        e["hp"] -= dmg
        e["flash"] = 6
        e["kx"] += math.cos(ang) * 3.5
        e["ky"] += math.sin(ang) * 3.5
        for _ in range(4):
            a = ang + random.uniform(-0.8, 0.8)
            b["fx"].append({"x": e["x"], "y": e["y"], "vx": math.cos(a) * 3, "vy": math.sin(a) * 3, "ttl": 12, "col": (255, 255, 255), "sz": 2})
        if e["hp"] <= 0 and e in b["enemies"]:
            b["enemies"].remove(e)
            b["kills"] += 1
            if by_player:
                b["aegis"] = min(100.0, b["aegis"] + 7)
            if e["name"]:
                b["note"], b["note_t"] = e["name"] + " HAS FALLEN!", 150
            b["corpses"].append({"x": e["x"], "y": e["y"], "a": ang, "col": e["col"], "r": e["r"], "ttl": 420})
            b["corpses"] = b["corpses"][-30:]
            for _ in range(8):
                a = random.random() * 6.28
                sp = random.uniform(1.0, 4.0)
                b["fx"].append({"x": e["x"], "y": e["y"], "vx": math.cos(a) * sp, "vy": math.sin(a) * sp, "ttl": 24,
                                "col": random.choice([e["col"], (255, 220, 120), (255, 255, 255)]), "sz": 3})

    def bt_swing(self):
        b = self.bt
        wp = b["wp"]
        a = b["aim"]
        b["swing"] = 10
        b["swing_cd"] = wp["cd"]
        hits = []
        for e in b["enemies"]:
            dx, dy = e["x"] - b["px"], e["y"] - b["py"]
            d = math.hypot(dx, dy)
            if d <= wp["reach"] + e["r"]:
                diff = abs((math.atan2(dy, dx) - a + math.pi) % (2 * math.pi) - math.pi)
                if diff <= wp["arc"] / 2.0 + (e["r"] / max(d, 1.0)) * 0.6:
                    hits.append((d, e))
        hits.sort(key=lambda h: h[0])
        if wp["pierce"]:
            hits = hits[:wp["pierce"]]
        for d, e in hits:
            e["kx"] += math.cos(a) * wp["knock"]
            e["ky"] += math.sin(a) * wp["knock"]
            self.bt_damage(e, wp["dmg"], a)
        keep = []
        for pr in b["eproj"]:
            dx, dy = pr["x"] - b["px"], pr["y"] - b["py"]
            d = math.hypot(dx, dy)
            diff = abs((math.atan2(dy, dx) - a + math.pi) % (2 * math.pi) - math.pi)
            if d <= wp["reach"] + 22 and diff <= max(wp["arc"], 1.2) / 2.0:
                self.bt_sparks(pr["x"], pr["y"], (255, 255, 255), 5, 3.0)
            else:
                keep.append(pr)
        b["eproj"] = keep

    def bt_summon(self, who):
        b = self.bt
        if who == "tele":
            b["tele_used"] = True
            b["allies"].append({"k": "tele", "x": 100.0, "y": 450.0, "ttl": 1200, "cd": 20, "mc": 0, "face": 0.0})
            b["note"], b["note_t"] = "TELEMACHUS JOINS THE FIGHT!", 150
            self.bt_sparks(100, 450, (140, 190, 255), 14, 3.0)
        else:
            b["eum_used"] = True
            b["allies"].append({"k": "eum", "x": 100.0, "y": 380.0, "ttl": 1500, "cd": 20, "mc": 0, "face": 0.0})
            b["note"], b["note_t"] = "EUMAEUS JOINS THE FIGHT AND BINDS YOUR WOUNDS!", 170
            b["hp"] = min(b["maxhp"], b["hp"] + 2)
            self.bt_sparks(100, 380, (150, 220, 140), 14, 3.0)
            self.bt_sparks(b["px"], b["py"], (255, 140, 170), 10, 2.5)

    def battle_keydown(self, key):
        b = self.bt
        ph = b["phase"]
        if ph == "intro":
            if key == pygame.K_SPACE:
                self.bt_start_wave(0)
        elif ph == "dead":
            if key == pygame.K_SPACE:
                b["hp"] = b["maxhp"]
                b["kills"] = b["wave_kills0"]
                self.bt_start_wave(b["wave"], True)
                b["inv"] = 90
        elif ph == "arrows_out":
            if key == pygame.K_SPACE:
                b["phase"] = "armory"
                b["timer"] = 0
        elif ph == "armory":
            idx = {pygame.K_1: 0, pygame.K_KP1: 0, pygame.K_2: 1, pygame.K_KP2: 1}.get(key)
            if idx is not None:
                b["wp"] = BT_SWORDS[idx]
                b["phase"] = "armed"
                b["timer"] = 0
        elif ph == "armed":
            if key == pygame.K_SPACE:
                self.bt_begin_sword_wave()
        elif ph in ("play", "clear"):
            if key == pygame.K_SPACE and b["rcd"] <= 0 and b["roll"] <= 0:
                keys = pygame.key.get_pressed()
                mvx = (1 if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) else 0) - (1 if (keys[pygame.K_a] or keys[pygame.K_LEFT]) else 0)
                mvy = (1 if (keys[pygame.K_s] or keys[pygame.K_DOWN]) else 0) - (1 if (keys[pygame.K_w] or keys[pygame.K_UP]) else 0)
                if mvx == 0 and mvy == 0:
                    mvx, mvy = math.cos(b["aim"]), math.sin(b["aim"])
                n = math.hypot(mvx, mvy) or 1.0
                b["rdx"], b["rdy"] = mvx / n, mvy / n
                b["roll"] = 14
                b["rcd"] = 70
            elif key == pygame.K_q and b["aegis"] >= 100:
                b["aegis"] = 0.0
                b["aegis_fx"] = 26
                self.shake_timer = 12
                for e in list(b["enemies"]):
                    dx, dy = e["x"] - b["px"], e["y"] - b["py"]
                    d = math.hypot(dx, dy) or 1.0
                    if d < 200:
                        e["kx"] += dx / d * 14
                        e["ky"] += dy / d * 14
                        e["stun"] = 80
                        self.bt_damage(e, 1, math.atan2(dy, dx), True, True)
                b["eproj"] = [pr for pr in b["eproj"] if math.hypot(pr["x"] - b["px"], pr["y"] - b["py"]) > 200]
            elif key == pygame.K_t and ph == "play" and not b["tele_used"]:
                self.bt_summon("tele")
            elif key == pygame.K_e and ph == "play" and not b["eum_used"]:
                self.bt_summon("eum")

    def update_battle(self):
        b = self.bt
        b["timer"] += 1
        for f in b["fx"]:
            f["x"] += f["vx"]
            f["y"] += f["vy"]
            f["vx"] *= 0.92
            f["vy"] *= 0.92
            f["ttl"] -= 1
        b["fx"] = [f for f in b["fx"] if f["ttl"] > 0]
        for c in b["corpses"]:
            c["ttl"] -= 1
        b["corpses"] = [c for c in b["corpses"] if c["ttl"] > 0]
        for k in ("aegis_fx", "banner_t", "note_t"):
            if b[k] > 0:
                b[k] -= 1
        phase = b["phase"]
        if phase == "won":
            if b["timer"] > 220:
                pygame.mouse.set_visible(True)
                self.trigger_animation("odysseus_proves_himself", duration=720)
            return
        if phase == "armed":
            if b["timer"] > 260:
                self.bt_begin_sword_wave()
            return
        if phase not in ("play", "clear"):
            return
        keys = pygame.key.get_pressed()
        mx, my = pygame.mouse.get_pos()
        # ---- the shield Odysseus snatches from the wall ----
        if b["shield_fly"] > 0:
            b["shield_fly"] -= 1
            if b["shield_fly"] == 0:
                b["shield"] = True
                b["helmet"] = True
                b["helmet_ready"] = True
                self.bt_sparks(b["px"], b["py"], (255, 226, 130), 14, 3.0)
        # ---- Odysseus ----
        b["aim"] = math.atan2(my - b["py"], mx - b["px"])
        if b["roll"] > 0:
            b["roll"] -= 1
            vx, vy = b["rdx"] * 7.5, b["rdy"] * 7.5
            if b["timer"] % 3 == 0:
                b["fx"].append({"x": b["px"], "y": b["py"], "vx": 0, "vy": 0, "ttl": 12, "col": (210, 190, 150), "sz": 5})
        else:
            mvx = (1 if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) else 0) - (1 if (keys[pygame.K_a] or keys[pygame.K_LEFT]) else 0)
            mvy = (1 if (keys[pygame.K_s] or keys[pygame.K_DOWN]) else 0) - (1 if (keys[pygame.K_w] or keys[pygame.K_UP]) else 0)
            n = math.hypot(mvx, mvy)
            vx, vy = (mvx / n * 3.0, mvy / n * 3.0) if n else (0.0, 0.0)
        b["px"], b["py"] = self.bt_resolve(b["px"] + vx, b["py"] + vy, 12)
        for k in ("inv", "rcd", "cd", "draw", "flash", "swing", "swing_cd"):
            if b[k] > 0:
                b[k] -= 1
        if pygame.mouse.get_pressed()[0] and b["roll"] <= 0:
            if b["wp"] is None:
                if b["cd"] <= 0:
                    a = b["aim"]
                    b["arrows"].append({"x": b["px"] + math.cos(a) * 20, "y": b["py"] + math.sin(a) * 20, "vx": math.cos(a) * 13, "vy": math.sin(a) * 13, "a": a})
                    b["cd"] = 20
                    b["draw"] = 10
            elif b["swing_cd"] <= 0:
                self.bt_swing()
        # ---- the suitors ----
        for e in list(b["enemies"]):
            dx, dy = b["px"] - e["x"], b["py"] - e["y"]
            d = math.hypot(dx, dy) or 1.0
            ux, uy = dx / d, dy / d
            e["face"] = math.atan2(dy, dx)
            if e["flash"] > 0:
                e["flash"] -= 1
            if e["blk"] > 0:
                e["blk"] -= 1
            mvx = mvy = 0.0
            k = e["base"]
            if e["stun"] > 0:
                e["stun"] -= 1
            elif k == "sword":
                mvx, mvy = ux * e["sp"], uy * e["sp"]
            elif k == "armed":
                if e["state"] == 0:
                    # shield up, he closes to throwing range and hurls the one spear Melanthius gave him
                    if d > 300:
                        mvx, mvy = ux * e["sp"], uy * e["sp"]
                    else:
                        sgn = 1 if math.sin(e["ph"] + b["timer"] * 0.01) > 0 else -1
                        mvx, mvy = -uy * e["sp"] * 0.7 * sgn, ux * e["sp"] * 0.7 * sgn
                    e["cd"] -= 1
                    if e["cd"] == 26:
                        e["tele"] = 26
                    if e["tele"] > 0:
                        e["tele"] -= 1
                    if e["cd"] <= 0:
                        turn = False
                        if b["athena_left"] > 0:
                            b["athena_left"] -= 1
                            turn = True
                        b["eproj"].append({"k": "spear", "x": e["x"], "y": e["y"], "vx": ux * 8.5, "vy": uy * 8.5, "r": 6, "rot": 0.0, "life": 160, "turn": turn})
                        e["state"] = 1
                else:
                    mvx, mvy = ux * e["sp"] * 1.1, uy * e["sp"] * 1.1     # spear gone, he draws his sword
            elif k == "panic":
                ang = math.atan2(-dy, -dx) + math.sin(e["ph"] + b["timer"] * 0.05) * 0.9
                mvx, mvy = math.cos(ang) * e["sp"], math.sin(ang) * e["sp"]
                e["face"] = math.atan2(-dy, -dx)
            e["x"] += mvx + e["kx"]
            e["y"] += mvy + e["ky"]
            e["kx"] *= 0.8
            e["ky"] *= 0.8
            for o in b["enemies"]:
                if o is e:
                    continue
                ddx, ddy = e["x"] - o["x"], e["y"] - o["y"]
                dd = math.hypot(ddx, ddy)
                if 0 < dd < e["r"] + o["r"]:
                    push = (e["r"] + o["r"] - dd) * 0.5
                    e["x"] += ddx / dd * push
                    e["y"] += ddy / dd * push
            e["x"], e["y"] = self.bt_resolve(e["x"], e["y"], e["r"])
            if k not in ("panic", "leodes") and d < e["r"] + 11 and e["blk"] <= 0:
                if self.bt_shield_blocks(math.atan2(-dy, -dx), 0.8):
                    e["blk"], e["stun"] = 28, 22
                    e["kx"] -= ux * 9
                    e["ky"] -= uy * 9
                    self.bt_sparks(b["px"] + math.cos(b["aim"]) * 16, b["py"] + math.sin(b["aim"]) * 16, (255, 236, 160), 7, 3.0)
                    self.shake_timer = 4
                elif self.bt_hurt(2 if (k == "boss" and e["state"] == 2) else 1):
                    b["px"], b["py"] = self.bt_resolve(b["px"] + ux * 12, b["py"] + uy * 12, 12)
        # ---- Telemachus and Eumaeus ----
        for al in list(b["allies"]):
            al["ttl"] -= 1
            if al["mc"] > 0:
                al["mc"] -= 1
            tgt, td = None, 9999.0
            for e in b["enemies"]:
                dd = math.hypot(e["x"] - al["x"], e["y"] - al["y"])
                if dd < td:
                    tgt, td = e, dd
            mvx = mvy = 0.0
            if al["k"] == "tele":
                if tgt is not None:
                    ang = math.atan2(tgt["y"] - al["y"], tgt["x"] - al["x"])
                    al["face"] = ang
                    if td > 170:
                        mvx, mvy = math.cos(ang) * 3.2, math.sin(ang) * 3.2
                    elif td < 100:
                        mvx, mvy = -math.cos(ang) * 2.4, -math.sin(ang) * 2.4
                    al["cd"] -= 1
                    if al["cd"] <= 0 and td < 380:
                        b["sp"].append({"x": al["x"], "y": al["y"], "vx": math.cos(ang) * 9, "vy": math.sin(ang) * 9, "a": ang})
                        al["cd"] = 42
                    if td < 34 and al["mc"] <= 0:
                        self.bt_damage(tgt, 1, ang, False)
                        al["mc"] = 24
                else:
                    ang = math.atan2(b["py"] - al["y"], b["px"] - al["x"])
                    if math.hypot(b["px"] - al["x"], b["py"] - al["y"]) > 90:
                        mvx, mvy = math.cos(ang) * 2.6, math.sin(ang) * 2.6
            else:
                near = tgt is not None and math.hypot(tgt["x"] - b["px"], tgt["y"] - b["py"]) < 300
                if near:
                    ang = math.atan2(tgt["y"] - al["y"], tgt["x"] - al["x"])
                    al["face"] = ang
                    if td > 30:
                        mvx, mvy = math.cos(ang) * 2.7, math.sin(ang) * 2.7
                    if td < 44 and al["mc"] <= 0:
                        self.bt_damage(tgt, 2, ang, False)
                        al["mc"] = 22
                else:
                    ang = math.atan2(b["py"] - al["y"], b["px"] - al["x"])
                    al["face"] = ang
                    if math.hypot(b["px"] - al["x"], b["py"] - al["y"]) > 70:
                        mvx, mvy = math.cos(ang) * 2.7, math.sin(ang) * 2.7
                keep = []
                for pr in b["eproj"]:
                    if math.hypot(pr["x"] - al["x"], pr["y"] - al["y"]) < 34:
                        self.bt_sparks(pr["x"], pr["y"], (255, 236, 160), 5, 2.5)
                    else:
                        keep.append(pr)
                b["eproj"] = keep
            al["x"], al["y"] = self.bt_resolve(al["x"] + mvx, al["y"] + mvy, 12)
            if al["ttl"] <= 0:
                self.bt_sparks(al["x"], al["y"], (255, 255, 255), 14, 3.0)
                b["allies"].remove(al)
        for sp in b["sp"]:
            for _ in range(3):
                sp["x"] += sp["vx"] / 3.0
                sp["y"] += sp["vy"] / 3.0
                dead = not (BT_L - 4 < sp["x"] < BT_R + 4 and BT_T - 4 < sp["y"] < BT_B + 4)
                for cx, cy, cr in BT_CIRCLES:
                    if math.hypot(sp["x"] - cx, sp["y"] - cy) < cr:
                        dead = True
                if not dead:
                    for e in b["enemies"]:
                        if math.hypot(sp["x"] - e["x"], sp["y"] - e["y"]) < e["r"] + 4:
                            self.bt_damage(e, 2, sp["a"], False)
                            dead = True
                            break
                if dead:
                    sp["dead"] = True
                    break
        b["sp"] = [sp for sp in b["sp"] if not sp.get("dead")]
        # ---- missiles ----
        for pr in b["eproj"]:
            if pr.get("turn") and not pr.get("turned") and math.hypot(pr["x"] - b["px"], pr["y"] - b["py"]) < 130:
                pr["turned"] = True
                rot = 0.75 if random.random() < 0.5 else -0.75
                c, s_ = math.cos(rot), math.sin(rot)
                pr["vx"], pr["vy"] = pr["vx"] * c - pr["vy"] * s_, pr["vx"] * s_ + pr["vy"] * c
                self.bt_sparks(pr["x"], pr["y"], (255, 226, 130), 10, 3.5)
                b["note"], b["note_t"] = "ATHENA TURNS THE SPEARS ASIDE!", 100
            pr["x"] += pr["vx"]
            pr["y"] += pr["vy"]
            pr["rot"] += 0.35
            pr["life"] -= 1
            hit_wall = not (BT_L < pr["x"] < BT_R and BT_T < pr["y"] < BT_B)
            for cx, cy, cr in BT_CIRCLES:
                if math.hypot(pr["x"] - cx, pr["y"] - cy) < cr + pr["r"] * 0.5:
                    hit_wall = True
            if hit_wall or pr["life"] <= 0:
                pr["life"] = 0
            elif not pr.get("turn") and math.hypot(pr["x"] - b["px"], pr["y"] - b["py"]) < pr["r"] + 10:
                if self.bt_shield_blocks(math.atan2(pr["y"] - b["py"], pr["x"] - b["px"]), 1.2):
                    self.bt_sparks(pr["x"], pr["y"], (255, 236, 160), 8, 3.0)
                    self.shake_timer = 4
                    pr["life"] = 0
                elif self.bt_hurt(1):
                    pr["life"] = 0
        b["eproj"] = [pr for pr in b["eproj"] if pr["life"] > 0]
        for a in b["arrows"]:
            for _ in range(3):
                a["x"] += a["vx"] / 3.0
                a["y"] += a["vy"] / 3.0
                dead = not (BT_L - 4 < a["x"] < BT_R + 4 and BT_T - 4 < a["y"] < BT_B + 4)
                for cx, cy, cr in BT_CIRCLES:
                    if math.hypot(a["x"] - cx, a["y"] - cy) < cr:
                        dead = True
                if not dead:
                    for e in b["enemies"]:
                        if math.hypot(a["x"] - e["x"], a["y"] - e["y"]) < e["r"] + 3:
                            self.bt_damage(e, 1, a["a"])
                            dead = True
                            break
                if dead:
                    a["dead"] = True
                    break
        b["arrows"] = [a for a in b["arrows"] if not a.get("dead")]
        # ---- spawning and wave flow ----
        if b["queue"]:
            b["spawn_t"] -= 1
            if b["spawn_t"] <= 0 and len(b["enemies"]) < 10:
                if b["queue"][0] == "leodes" and b["enemies"]:
                    pass                                  # Leodes is the last suitor to fall, so he waits for the rest
                else:
                    self.bt_spawn(b["queue"].pop(0))
                    b["spawn_t"] = 38
        if phase == "play" and not b["queue"] and not b["enemies"]:
            w = b["wave"]
            b["eproj"], b["arrows"], b["sp"] = [], [], []
            if w >= len(BT_WAVES) - 1:
                b["phase"] = "won"
                b["timer"] = 0
            elif w == 2:
                b["phase"] = "arrows_out"
                b["timer"] = 0
                b["allies"] = []
            else:
                b["phase"] = "clear"
                b["clear_t"] = 170
                b["hp"] = min(b["maxhp"], b["hp"] + 2)
                if w == 1:
                    b["shield_fly"] = 50
        elif phase == "clear":
            b["clear_t"] -= 1
            if b["clear_t"] <= 0:
                self.bt_start_wave(b["wave"] + 1)

    # ---------- drawing the battle ----------
    def bt_draw_shield(self, cx, cy, r):
        self.a_circle((70, 52, 30), cx + 1, cy + 2, r)
        self.a_circle((186, 140, 60), cx, cy, r)
        self.a_circle((236, 196, 100), cx, cy, r, 2)
        self.a_circle((150, 108, 44), cx, cy, r * 0.62, 1)
        self.a_circle((242, 216, 140), cx, cy, r * 0.32)
        for k in range(8):
            a = k * 0.785
            self.a_circle((222, 180, 90), cx + math.cos(a) * r * 0.82, cy + math.sin(a) * r * 0.82, max(1, r * 0.08))

    def bt_draw_sword(self, x, y, a):
        b = self.bt
        wp = b["wp"]
        sw = b["swing"]
        prog = 1 - sw / 10.0 if sw > 0 else 0.0
        hand = (x + math.cos(a + 0.95) * 14, y + math.sin(a + 0.95) * 14)
        if wp["key"] == 0:       # one of his two spears, thrust; the other slung across his back
            ca, sa = math.cos(a), math.sin(a)
            ext = math.sin(prog * math.pi) * 28 if sw > 0 else 0.0
            hand = (hand[0] + ca * ext, hand[1] + sa * ext)
            tip = (hand[0] + ca * 48, hand[1] + sa * 48)
            base = (hand[0] - ca * 14, hand[1] - sa * 14)
            self.a_line((150, 110, 60), x - ca * 8 - sa * 10, y - sa * 8 + ca * 10, x - ca * 26 + sa * 16, y - sa * 26 - ca * 16, 3)
            self.a_line((150, 110, 60), base[0], base[1], tip[0], tip[1], 3)
            self.a_poly((226, 232, 242), [(tip[0] + ca * 16, tip[1] + sa * 16), (tip[0] - sa * 5, tip[1] + ca * 5), (tip[0] - ca * 4, tip[1] - sa * 4), (tip[0] + sa * 5, tip[1] - ca * 5)])
            if sw > 0:
                self.a_line((255, 255, 255), x + ca * 16, y + sa * 16, x + ca * (wp["reach"] + 6), y + sa * (wp["reach"] + 6), 3)
            return
        ang = (a + wp["arc"] / 2.0 - prog * wp["arc"]) if sw > 0 else a + 0.55
        ca, sa = math.cos(ang), math.sin(ang)
        tip = (hand[0] + ca * 36, hand[1] + sa * 36)
        self.a_line((222, 180, 98), hand[0], hand[1], tip[0], tip[1], 4)
        self.a_line((250, 224, 160), hand[0], hand[1], tip[0], tip[1], 1)
        self.a_line((150, 108, 44), hand[0] - sa * 6, hand[1] + ca * 6, hand[0] + sa * 6, hand[1] - ca * 6, 3)
        self.a_circle((184, 138, 60), hand[0] - ca * 3, hand[1] - sa * 3, 3)
        if sw > 0:
            pts = []
            for j in range(9):
                aj = a - wp["arc"] / 2.0 + wp["arc"] * j / 8.0
                pts.append((x + math.cos(aj) * (wp["reach"] - 4), y + math.sin(aj) * (wp["reach"] - 4)))
            self.a_lines((255, 240, 190) if sw > 5 else (255, 255, 255), pts, 4)
            self.a_lines((255, 255, 255), pts, 1)

    def bt_draw_enemy(self, e):
        x, y, r, f = e["x"], e["y"], e["r"], e["face"]
        k = e["base"]
        col = (255, 255, 255) if e["flash"] > 0 else e["col"]
        skin = (236, 198, 158)
        cf, sf = math.cos(f), math.sin(f)
        self.a_ellipse((50, 40, 32), x - r, y + r * 0.35, 2 * r, r * 1.1)
        if e["tele"] > 0:
            self.a_line((255, 70, 60) if (e["tele"] // 3) % 2 == 0 else (255, 200, 80), x, y, x + cf * 260, y + sf * 260, 2)
        hand_r = (x + math.cos(f + 0.85) * (r + 2), y + math.sin(f + 0.85) * (r + 2))
        hand_l = (x + math.cos(f - 0.85) * (r + 2), y + math.sin(f - 0.85) * (r + 2))
        if k == "armed" and e["state"] == 0:
            self.a_line((150, 110, 60), x - cf * 12, y - sf * 12, x + cf * 36, y + sf * 36, 3)
            self.a_poly((222, 228, 238), [(x + cf * 46, y + sf * 46), (x + cf * 32 - sf * 4, y + sf * 32 + cf * 4), (x + cf * 32 + sf * 4, y + sf * 32 - cf * 4)])
        self.a_circle(col, x, y, r)
        self.a_circle(_mix(col, (0, 0, 0), 0.35), x, y, r, 2)
        if k in ("panic", "leodes"):
            for sgn in (-1, 1):
                self.a_line(skin, x + sgn * r * 0.5, y - r * 0.3, x + sgn * r * 0.9, y - r * 1.2, 3)
                self.a_circle(skin, x + sgn * r * 0.9, y - r * 1.2, 4)
            if k == "panic" and (e["ph"] * 10 + self.bt["timer"]) % 20 < 10:
                self.a_circle((170, 210, 255), x + r + 3, y - r, 2)
        else:
            for hx, hy in (hand_r, hand_l):
                self.a_circle(skin, hx, hy, 4)
        if k == "sword" or (k == "armed" and e["state"] == 1):
            self.a_line((220, 224, 236), hand_r[0], hand_r[1], hand_r[0] + math.cos(f + 0.3) * 24, hand_r[1] + math.sin(f + 0.3) * 24, 2)
            self.a_line((150, 108, 44), hand_r[0] - math.sin(f + 0.3) * 4, hand_r[1] + math.cos(f + 0.3) * 4, hand_r[0] + math.sin(f + 0.3) * 4, hand_r[1] - math.cos(f + 0.3) * 4, 2)
        if e["table"]:
            tx, ty = x + cf * 20, y + sf * 20
            self.a_poly((156, 108, 62), [(tx - sf * 16 - cf * 4, ty + cf * 16 - sf * 4), (tx + sf * 16 - cf * 4, ty - cf * 16 - sf * 4),
                                         (tx + sf * 16 + cf * 4, ty - cf * 16 + sf * 4), (tx - sf * 16 + cf * 4, ty + cf * 16 + sf * 4)])
            self.a_line((92, 60, 30), tx - sf * 16, ty + cf * 16, tx + sf * 16, ty - cf * 16, 2)
        if e["shield"]:
            sx, sy = x + cf * 17, y + sf * 17
            self.a_circle((180, 134, 58), sx, sy, 12)
            self.a_circle((236, 196, 100), sx, sy, 12, 2)
            self.a_circle((240, 214, 140), sx, sy, 4)
        self.a_circle((70, 50, 36), x - cf * 2, y - sf * 2, r * 0.56)
        self.a_circle(skin, x + cf * 2, y + sf * 2, r * 0.46)
        if k == "armed":
            self.a_circle((205, 160, 60), x - cf * 1, y - sf * 1, r * 0.55)
            self.a_line((60, 30, 30), x - cf * 4, y - sf * 4, x - cf * 15, y - sf * 15, 4)
        if e["mhp"] > 1:
            w = 24
            self.a_rect((40, 20, 20), x - w / 2, y - r - 12, w, 4)
            self.a_rect((220, 60, 50), x - w / 2, y - r - 12, w * e["hp"] / float(e["mhp"]), 4)
        if e["name"]:
            ox, oy = self.shake_offset
            self.draw_text(e["name"], self.small_font, WHITE, int(x) + ox, int(y - r - 28) + oy, center=True)

    def bt_draw_ally(self, al):
        x, y, f = al["x"], al["y"], al["face"]
        cf, sf = math.cos(f), math.sin(f)
        tele = al["k"] == "tele"
        col = (70, 112, 204) if tele else (98, 128, 72)
        skin = (236, 198, 158)
        self.a_ellipse((50, 40, 32), x - 12, y + 5, 24, 12)
        self.a_glow(x, y, 26, (255, 236, 160), 50)
        self.a_line((150, 110, 60), x - cf * 12, y - sf * 12, x + cf * 36, y + sf * 36, 3)
        self.a_poly((214, 218, 228), [(x + cf * 44, y + sf * 44), (x + cf * 32 - sf * 4, y + sf * 32 + cf * 4), (x + cf * 32 + sf * 4, y + sf * 32 - cf * 4)])
        self.a_circle(col, x, y, 12)
        self.a_circle(GOLD, x, y, 12, 2)
        hl = (x + math.cos(f - 0.9) * 14, y + math.sin(f - 0.9) * 14)
        self.bt_draw_shield(hl[0], hl[1], 10)
        self.a_circle(skin, x + math.cos(f + 0.9) * 14, y + math.sin(f + 0.9) * 14, 4)
        self.a_circle((70, 50, 36) if tele else (170, 170, 170), x - cf * 2, y - sf * 2, 7.5)
        self.a_circle(skin, x + cf * 2, y + sf * 2, 6)
        self.a_circle((205, 160, 60), x - cf * 1, y - sf * 1, 7.5)
        self.a_line((196, 50, 50) if tele else (60, 30, 30), x - cf * 4, y - sf * 4, x - cf * 13, y - sf * 13, 3)
        ox, oy = self.shake_offset
        self.draw_text("TELEMACHUS" if tele else "EUMAEUS", self.small_font, (190, 220, 255) if tele else (190, 235, 170), int(x) + ox, int(y - 34) + oy, center=True)

    def bt_draw_player(self, tk):
        b = self.bt
        x, y, a = b["px"], b["py"], b["aim"]
        ca, sa = math.cos(a), math.sin(a)
        if b["inv"] > 0 and (b["inv"] // 3) % 2 == 0:
            return
        self.a_ellipse((50, 40, 32), x - 12, y + 6, 24, 12)
        if b["roll"] > 0:
            for k in range(3):
                self.a_circle((190, 40, 50), x - b["rdx"] * k * 8, y - b["rdy"] * k * 8, 9 - k * 2)
            self.a_circle((214, 64, 56), x, y, 10)
            self.a_circle(GOLD, x, y, 10, 2)
            return
        self.a_circle((150, 28, 40), x - ca * 3, y - sa * 3, 15)
        self.a_circle((214, 64, 56), x, y, 12)
        self.a_circle(GOLD, x, y, 12, 2)
        px_, py_ = -sa, ca
        if b["wp"] is None:
            C = (x + ca * 24, y + sa * 24)
            pts = []
            for k in range(-6, 7):
                u = k / 6.0
                pts.append((C[0] + px_ * u * 20 - ca * u * u * 8, C[1] + py_ * u * 20 - sa * u * u * 8))
            pull = 0 if b["draw"] > 0 else 9
            nock = (C[0] - ca * (6 + pull), C[1] - sa * (6 + pull))
            self.a_line((236, 198, 158), x + px_ * 9, y + py_ * 9, C[0], C[1], 4)
            self.a_line((236, 198, 158), x - px_ * 9, y - py_ * 9, nock[0], nock[1], 4)
            self.a_lines((126, 82, 38), pts, 5)
            self.a_lines((240, 234, 214), [pts[0], nock, pts[-1]], 2)
            if b["draw"] <= 0:
                self.a_line((214, 184, 124), nock[0], nock[1], C[0] + ca * 22, C[1] + sa * 22, 3)
                self.a_poly((196, 196, 206), [(C[0] + ca * 30, C[1] + sa * 30), (C[0] + ca * 21 - sa * 4, C[1] + sa * 21 + ca * 4), (C[0] + ca * 21 + sa * 4, C[1] + sa * 21 - ca * 4)])
        else:
            self.bt_draw_sword(x, y, a)
        if b["shield"]:
            self.bt_draw_shield(x + math.cos(a - 1.05) * 17, y + math.sin(a - 1.05) * 17, 12)
        self.a_circle((80, 55, 38), x - ca * 2, y - sa * 2, 8)
        self.a_circle((236, 198, 158), x + ca * 2, y + sa * 2, 6.5)
        if b["helmet"]:
            self.a_circle((205, 160, 60), x - ca * 1, y - sa * 1, 8)
            self.a_circle((236, 196, 100), x - ca * 1, y - sa * 1, 8, 2)
            self.a_line((196, 50, 50), x - ca * 4, y - sa * 4, x - ca * 16, y - sa * 16, 4)

    def draw_battle_card(self, tk):
        ox, oy = self.shake_offset
        self.a_fade((0, 0, 0), 170)
        self.a_rect((24, 18, 12), 110, 92, 580, 416)
        self.a_rect(GOLD, 110, 92, 580, 416, 3)
        self.a_title("SLAY THE SUITORS", GOLD, 100)
        self.draw_text("The doors are barred. Not one suitor may escape!", self.font, WHITE, WIDTH // 2 + ox, 142 + oy, center=True)
        rows = [("W A S D / ARROWS", "Move Odysseus"), ("MOUSE", "Aim"), ("LEFT CLICK", "Attack (hold to repeat)"),
                ("SPACE", "Dodge roll (invincible)"), ("Q", "Athena's Aegis blast"),
                ("T", "Summon Telemachus (once)"), ("E", "Summon Eumaeus (once)")]
        for i, (k, v) in enumerate(rows):
            yy = 176 + i * 28
            self.draw_text(k, self.font, GOLD, 140 + ox, yy + oy)
            self.draw_text(v, self.font, WHITE, 352 + ox, yy + oy)
        self.draw_text("Slay suitors to charge the Aegis, then press Q to hurl them back and shatter their missiles.", self.small_font, CRT_GREEN, WIDTH // 2 + ox, 380 + oy, center=True, max_width=530)
        self.draw_text("Suitors hide behind tables and shields: strike from the side, or hit twice. Telemachus and Eumaeus can each be called ONCE in the whole battle.", self.small_font, WHITE, WIDTH // 2 + ox, 420 + oy, center=True, max_width=530)
        if (tk // 25) % 2 == 0:
            self.draw_text("Press SPACE to begin", self.font, CRT_GREEN, WIDTH // 2 + ox, 474 + oy, center=True)

    def draw_battle(self):
        b = self.bt
        tk = pygame.time.get_ticks() // 16
        ox, oy = self.shake_offset
        if b["phase"] in ("arrows_out", "armory", "armed"):
            self.draw_armory(tk)
            return
        if self._bt_bg is None:
            self.build_battle_bg()
        self.screen.blit(self._bt_bg, (ox, oy))
        self.a_begin()
        if b["shield_fly"] > 0 or b["shield"]:
            self.a_circle((58, 48, 42), 400, 106, 15)
            self.a_circle((90, 70, 40), 400, 106, 3)
        # Athena, in the form of a swallow, watches from the rafters
        if b["wave"] >= 2:
            wx = 400 + math.sin(tk * 0.03) * 6
            wy = 100 + (math.sin(tk * 0.4) * 3 if b["note_t"] > 0 else 0)
            self.a_poly((30, 40, 80), [(wx - 7, wy), (wx, wy - 4), (wx + 7, wy), (wx + 12, wy + 5), (wx + 4, wy + 3), (wx, wy + 8), (wx - 4, wy + 3), (wx - 12, wy + 5)])
            self.a_circle((200, 80, 60), wx, wy - 2, 2)
            if b["note_t"] > 0 or b["aegis_fx"] > 0:
                self.a_glow(wx, wy, 26, (255, 226, 130), 90)
        for fx_, fy_ in ((170, 120), (400, 120), (630, 120)):
            self.a_glow(fx_, fy_ + 20, 90, (255, 150, 50), 70)
            self.a_flame(fx_, 114, 12, 22, tk, fx_)
        self.a_glow(400, 318, 120, (255, 140, 40), 90)
        self.a_flame(400, 326, 30, 50, tk, 0)
        self.a_flame(410, 326, 18, 34, tk, 3)
        for c in b["corpses"]:
            self.a_ellipse(_mix(c["col"], (30, 20, 20), 0.35), c["x"] - c["r"], c["y"] - c["r"] * 0.6, c["r"] * 2, c["r"] * 1.2)
            self.a_circle((200, 168, 134), c["x"] + math.cos(c["a"]) * c["r"], c["y"] + math.sin(c["a"]) * c["r"] * 0.6, c["r"] * 0.45)
        for e in sorted(b["enemies"], key=lambda q: q["y"]):
            self.bt_draw_enemy(e)
        for al in b["allies"]:
            self.bt_draw_ally(al)
        self.bt_draw_player(tk)
        if b["shield_fly"] > 0:
            u = 1 - b["shield_fly"] / 50.0
            sx_ = 400 + (b["px"] - 400) * u
            sy_ = 106 + (b["py"] - 106) * u - math.sin(u * math.pi) * 40
            self.a_glow(sx_, sy_, 30, (255, 226, 130), 100)
            self.bt_draw_shield(sx_, sy_, 13)
        for pr in b["eproj"]:
            if pr["k"] == "spear":
                ang = math.atan2(pr["vy"], pr["vx"])
                ca, sa = math.cos(ang), math.sin(ang)
                self.a_line((150, 110, 60), pr["x"] - ca * 22, pr["y"] - sa * 22, pr["x"] + ca * 12, pr["y"] + sa * 12, 3)
                self.a_poly((210, 214, 224), [(pr["x"] + ca * 20, pr["y"] + sa * 20), (pr["x"] + ca * 10 - sa * 4, pr["y"] + sa * 10 + ca * 4), (pr["x"] + ca * 10 + sa * 4, pr["y"] + sa * 10 - ca * 4)])
                if pr.get("turn"):
                    self.a_glow(pr["x"], pr["y"], 16, (255, 226, 130), 90)
            else:
                col = GOLD if pr["k"] == "cup" else (170, 120, 70)
                self.a_circle(col, pr["x"], pr["y"], pr["r"])
                self.a_circle((255, 240, 180), pr["x"] + math.cos(pr["rot"]) * 3, pr["y"] + math.sin(pr["rot"]) * 3, 2)
        for a in b["arrows"]:
            ca, sa = math.cos(a["a"]), math.sin(a["a"])
            self.a_line((214, 184, 124), a["x"] - ca * 22, a["y"] - sa * 22, a["x"], a["y"], 3)
            self.a_poly((200, 204, 214), [(a["x"] + ca * 8, a["y"] + sa * 8), (a["x"] - sa * 4, a["y"] + ca * 4), (a["x"] + sa * 4, a["y"] - ca * 4)])
            self.a_line((200, 50, 50), a["x"] - ca * 22, a["y"] - sa * 22, a["x"] - ca * 28 - sa * 3, a["y"] - sa * 28 + ca * 3, 2)
        for sp in b["sp"]:
            ca, sa = math.cos(sp["a"]), math.sin(sp["a"])
            self.a_line((150, 110, 60), sp["x"] - ca * 24, sp["y"] - sa * 24, sp["x"] + ca * 10, sp["y"] + sa * 10, 3)
            self.a_poly((230, 234, 244), [(sp["x"] + ca * 20, sp["y"] + sa * 20), (sp["x"] + ca * 8 - sa * 4, sp["y"] + sa * 8 + ca * 4), (sp["x"] + ca * 8 + sa * 4, sp["y"] + sa * 8 - ca * 4)])
        for f in b["fx"]:
            self.a_circle(f["col"], f["x"], f["y"], max(1, f["sz"] * f["ttl"] / 20.0))
        if b["aegis_fx"] > 0:
            k = 1 - b["aegis_fx"] / 30.0
            cx_, cy_ = (b["px"], b["py"]) if b["wave"] != 4 or b["banner_t"] < 150 else (400, 100)
            self.a_circle((255, 226, 130), cx_, cy_, 20 + 180 * k, 6)
            self.a_circle((255, 250, 210), cx_, cy_, 14 + 150 * k, 2)
            self.a_glow(cx_, cy_, 60 + 140 * k, (255, 226, 130), int(110 * (1 - k)))
        self.screen.blit(self._bt_vig, (FRAME[0] + ox, FRAME[1] + oy))
        if b["flash"] > 0:
            self.a_fade((200, 0, 0), b["flash"] * 9)
        self.a_end()
        # ---- HUD ----
        for i in range(b["maxhp"]):
            self.bt_heart(84 + i * 24, 108, 9, i < b["hp"])
        if b["shield"]:
            self.bt_draw_shield(268, 108, 9)
        if b["helmet"]:
            hc = (205, 160, 60) if b["helmet_ready"] else (110, 100, 80)
            self.a_circle(hc, 298, 110, 8)
            self.a_rect(hc, 290, 110, 16, 5)
            self.a_line((196, 50, 50) if b["helmet_ready"] else (90, 60, 50), 298, 102, 298, 94, 3)
        if b["wp"] is None:
            self.a_lines((126, 82, 38), [(332 + 6 * math.sin(u / 4.0 * math.pi), 98 + u * 5) for u in range(5)], 3)
            self.a_line((240, 234, 214), 332, 98, 332, 118, 1)
        elif b["wp"]["key"] == 0:
            self.a_line((150, 110, 60), 324, 118, 340, 96, 3)
            self.a_poly((226, 232, 242), [(343, 91), (336, 97), (344, 101)])
        else:
            self.a_line((222, 180, 98), 326, 118, 340, 98, 4)
            self.a_line((150, 108, 44), 324, 108, 334, 114, 3)
        left = 107 - b["kills"]
        self.draw_text("SUITORS REMAINING: " + str(left), self.font, BLACK, WIDTH // 2 + ox + 2, 98 + oy, center=True)
        self.draw_text("SUITORS REMAINING: " + str(left), self.font, WHITE, WIDTH // 2 + ox, 96 + oy, center=True)
        full = b["aegis"] >= 100
        gx, gy, gw = 596, 100, 130
        self.a_rect((20, 16, 12), gx - 2, gy - 2, gw + 4, 16)
        self.a_rect((255, 214, 90) if (full and (tk // 8) % 2 == 0) else (200, 160, 50), gx, gy, gw * b["aegis"] / 100.0, 12)
        self.a_rect(WHITE, gx - 2, gy - 2, gw + 4, 16, 2)
        self.draw_text("Q: AEGIS" + (" READY!" if full else ""), self.small_font, GOLD if full else WHITE, gx + ox, gy + 17 + oy)
        self.a_rect((70, 70, 80), 84, 124, 60, 4)
        self.a_rect((150, 220, 255), 84, 124, 60 * (1 - b["rcd"] / 70.0), 4)
        verb = "shoot" if b["wp"] is None else "swing"
        self.draw_text("WASD move   CLICK " + verb + "   SPACE roll   Q Aegis", self.small_font, WHITE, WIDTH // 2 + ox, 530 + oy, center=True)
        tcol = (120, 120, 130) if b["tele_used"] else (150, 200, 255)
        ecol = (120, 120, 130) if b["eum_used"] else (170, 235, 150)
        self.draw_text("T Telemachus: " + ("USED" if b["tele_used"] else "READY"), self.small_font, tcol, WIDTH // 2 - 130 + ox, 550 + oy, center=True)
        self.draw_text("E Eumaeus: " + ("USED" if b["eum_used"] else "READY"), self.small_font, ecol, WIDTH // 2 + 130 + ox, 550 + oy, center=True)
        phase = b["phase"]
        if phase in ("play", "clear") and b["banner_t"] > 0 and b["wave"] >= 0:
            title, sub = b["banner"]
            self.a_title(title, GOLD, 146)
            self.draw_text(sub, self.small_font, BLACK, WIDTH // 2 + ox + 1, 190 + oy, center=True, max_width=620)
            self.draw_text(sub, self.small_font, WHITE, WIDTH // 2 + ox, 189 + oy, center=True, max_width=620)
        if b["note_t"] > 0 and phase in ("play", "clear"):
            self.draw_text(b["note"], self.font, BLACK, WIDTH // 2 + ox + 2, 462 + oy, center=True)
            self.draw_text(b["note"], self.font, GOLD, WIDTH // 2 + ox, 460 + oy, center=True)
        if phase == "clear":
            self.a_title("WAVE CLEARED!", GOLD, 146)
            msg = "Odysseus snatches a shield from the wall!" if b["wave"] == 1 else "Athena restores some of your strength."
            self.draw_text(msg, self.font, BLACK, WIDTH // 2 + ox + 2, 194 + oy, center=True)
            self.draw_text(msg, self.font, WHITE, WIDTH // 2 + ox, 192 + oy, center=True)
        if phase == "intro":
            self.draw_battle_card(tk)
        elif phase == "dead":
            self.a_fade((120, 0, 0), 120)
            self.a_title("ODYSSEUS HAS FALLEN!", RED, 190)
            self.draw_text("Athena restores your strength.|Press SPACE to fight this wave again.", self.font, WHITE, WIDTH // 2 + ox, 250 + oy, center=True)
        elif phase == "won":
            self.a_fade((255, 230, 150), min(120, b["timer"]))
            self.a_title("ALL 107 SUITORS HAVE FALLEN!", GOLD, 200)
            self.draw_text("The hall of Odysseus is his own again.", self.font, WHITE, WIDTH // 2 + ox, 250 + oy, center=True)
            self.draw_text("Phemius the bard and Medon the herald are spared.", self.small_font, (220, 210, 180), WIDTH // 2 + ox, 284 + oy, center=True)
        cx, cy = pygame.mouse.get_pos()
        for col, wd, rr in ((BLACK, 4, 13), (RED, 2, 13), (BLACK, 3, 4), (RED, 1, 4)):
            pygame.draw.circle(self.screen, col, (cx + ox, cy + oy), rr, wd)


    def bt_resolve(self, x, y, r):
        x = min(max(x, BT_L + r), BT_R - r)
        y = min(max(y, BT_T + r), BT_B - r)
        for cx, cy, cr in BT_CIRCLES:
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            m = r + cr
            if d < m:
                if d == 0:
                    dx, dy, d = 1.0, 0.0, 1.0
                x, y = cx + dx / d * m, cy + dy / d * m
        for rx, ry, rw, rh in BT_TABLES:
            nx, ny = min(max(x, rx), rx + rw), min(max(y, ry), ry + rh)
            dx, dy = x - nx, y - ny
            d = math.hypot(dx, dy)
            if d < r:
                if d == 0:
                    y = ry - r
                else:
                    x, y = nx + dx / d * r, ny + dy / d * r
        return x, y


    def bt_hurt(self, dmg):
        b = self.bt
        if b["inv"] > 0 or b["roll"] > 0 or b["phase"] != "play":
            return False
        if b["helmet"] and b["helmet_ready"]:
            b["helmet_ready"] = False
            b["inv"] = 30
            self.bt_sparks(b["px"], b["py"], (255, 236, 160), 12, 3.5)
            b["note"], b["note_t"] = "YOUR HELMET TURNS THE BLOW ASIDE!", 100
            self.shake_timer = 6
            return False
        b["hp"] -= dmg
        b["inv"] = 50
        b["flash"] = 8
        self.shake_timer = 8
        for _ in range(8):
            a = random.random() * 6.28
            b["fx"].append({"x": b["px"], "y": b["py"], "vx": math.cos(a) * 3, "vy": math.sin(a) * 3, "ttl": 16, "col": (230, 60, 60), "sz": 3})
        if b["hp"] <= 0:
            b["hp"] = 0
            b["phase"] = "dead"
            b["timer"] = 0
        return True

    def build_battle_bg(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        saved = (self.screen, self.shake_offset)
        self.screen, self.shake_offset = bg, (0, 0)
        self.a_rect((44, 36, 32), 53, 83, 694, 434)
        # stone walls with blocks
        for bx in range(53, 747, 46):
            self.a_rect((58, 48, 42), bx, 86, 44, 18)
            self.a_rect((52, 43, 37), bx + 20, 106, 44, 18)
        # the tiled floor
        for ty in range(BT_T, BT_B, 44):
            for tx in range(BT_L, BT_R, 44):
                shade = (122, 98, 74) if ((tx - BT_L) // 44 + (ty - BT_T) // 44) % 2 == 0 else (108, 86, 64)
                self.a_rect(shade, tx, ty, min(44, BT_R - tx), min(44, BT_B - ty))
        for ty in range(BT_T, BT_B, 44):
            self.a_rect((82, 64, 46), BT_L, ty, BT_R - BT_L, 2)
        for tx in range(BT_L, BT_R, 44):
            self.a_rect((82, 64, 46), tx, BT_T, 2, BT_B - BT_T)
        # the great rug
        self.a_rect((120, 30, 38), 238, 252, 324, 132)
        self.a_rect((220, 180, 70), 238, 252, 324, 132, 4)
        self.a_rect((220, 180, 70), 252, 266, 296, 104, 2)
        for k in range(7):
            self.a_poly((200, 150, 60), [(262 + k * 42, 318), (283 + k * 42, 296), (304 + k * 42, 318), (283 + k * 42, 340)], 2)
        # banners, shields and torch brackets on the walls
        for bx in (130, 330, 470, 670):
            self.a_rect((130, 36, 44), bx, 88, 24, 34)
            self.a_poly((130, 36, 44), [(bx, 122), (bx + 12, 132), (bx + 24, 122)])
            self.a_rect(GOLD, bx + 8, 98, 8, 8)
        for sx in (230, 400, 570):
            self.a_circle((176, 138, 62), sx, 106, 13)
            self.a_circle((222, 192, 100), sx, 106, 13, 2)
        for tx in (170, 400, 630):
            self.a_rect((70, 50, 30), tx - 3, 112, 6, 14)
        # the barred door on the left wall
        self.a_rect((120, 100, 76), 53, 276, 20, 84)
        self.a_rect((74, 50, 30), 55, 280, 15, 76)
        self.a_rect((64, 64, 72), 53, 308, 20, 8)
        # overturned feast tables
        for rx, ry, rw, rh in BT_TABLES:
            self.a_rect((70, 48, 28), rx - 3, ry - 3, rw + 6, rh + 6)
            self.a_rect((226, 214, 190), rx, ry, rw, rh)
            self.a_rect((200, 160, 60), rx, ry, rw, rh, 3)
            for k in range(4):
                self.a_circle((248, 242, 228), rx + 14 + k * 17, ry + 14, 6)
                self.a_circle(GOLD, rx + 14 + k * 17, ry + 34, 4)
        # columns
        for cx, cy, cr in BT_CIRCLES[:4]:
            self.a_circle((70, 58, 48), cx + 4, cy + 6, cr)
            self.a_circle((226, 210, 174), cx, cy, cr)
            self.a_circle((196, 178, 142), cx, cy, cr, 3)
            self.a_circle((248, 238, 208), cx - 4, cy - 4, 6)
        # the hearth
        self.a_circle((76, 72, 70), 400, 318, 30)
        self.a_circle((110, 104, 100), 400, 318, 28, 4)
        self.a_circle((36, 26, 22), 400, 318, 20)
        for k in range(8):
            a = k * 0.785
            self.a_circle((140, 134, 128), 400 + math.cos(a) * 24, 318 + math.sin(a) * 24, 4)
        pygame.draw.rect(self.screen, WHITE, (50, 80, WIDTH - 100, HEIGHT - 160), 3)
        self.screen, self.shake_offset = saved
        vig = pygame.Surface((FRAME[2], FRAME[3]), pygame.SRCALPHA)
        vig.fill((0, 0, 0, 175))
        steps = 14
        for i in range(steps):
            alpha = int(175 * (1 - i / float(steps - 1)) ** 2)
            pygame.draw.ellipse(vig, (0, 0, 0, alpha), (i * 24, i * 15, FRAME[2] - i * 48, FRAME[3] - i * 30))
        self._bt_bg, self._bt_vig = bg, vig

    def bt_heart(self, x, y, sz, filled):
        col = (230, 50, 70) if filled else (70, 40, 46)
        self.a_circle(col, x - sz * 0.5, y - sz * 0.3, sz * 0.55)
        self.a_circle(col, x + sz * 0.5, y - sz * 0.3, sz * 0.55)
        self.a_poly(col, [(x - sz * 1.0, y - sz * 0.1), (x + sz * 1.0, y - sz * 0.1), (x, y + sz * 1.0)])
        if filled:
            self.a_circle((255, 160, 170), x - sz * 0.6, y - sz * 0.45, max(1, sz * 0.18))


    # ---------- the armory: three swords of the age of heroes ----------
    def a_sword_art(self, kind, cx, cy, s=1.0, dim=1.0):
        """A sword, point up. kind 0: silver-studded sword with ivory sheath; 1: Mycenaean thrusting sword; 2: leaf-bladed bronze sword."""
        def c(col):
            return _mix(col, (10, 8, 6), 1 - dim)
        bronze, dk, silver, ivory = c((218, 176, 94)), c((160, 120, 56)), c((226, 230, 240)), c((240, 230, 200))
        grip = c((110, 76, 40))
        lw = max(1, int(2 * s))
        if kind == 3:
            self.a_poly(bronze, [(cx, cy - 92 * s), (cx + 8 * s, cy - 58 * s), (cx + 9 * s, cy + 6 * s), (cx - 9 * s, cy + 6 * s), (cx - 8 * s, cy - 58 * s)])
            self.a_line(dk, cx, cy - 88 * s, cx, cy + 4 * s, lw)
            self.a_line(c((250, 224, 160)), cx - 8 * s, cy - 56 * s, cx - 9 * s, cy + 4 * s, 1)
            self.a_rect(dk, cx - 16 * s, cy + 6 * s, 32 * s, 6 * s)
            self.a_rect(grip, cx - 5 * s, cy + 12 * s, 10 * s, 36 * s)
            self.a_circle(bronze, cx, cy + 52 * s, 8 * s)
        elif kind == 4:
            for sg in (-1, 1):
                hx, hy = cx + sg * 26 * s, cy - 96 * s
                bx_, by_ = cx - sg * 8 * s, cy + 62 * s
                n = math.hypot(bx_ - hx, by_ - hy)
                ux, uy = (bx_ - hx) / n, (by_ - hy) / n
                px_, py_ = -uy, ux
                self.a_line(grip, hx, hy, bx_, by_, max(2, int(4 * s)))
                tip = (hx - ux * 30 * s, hy - uy * 30 * s)
                self.a_poly(bronze, [tip, (hx + px_ * 8 * s, hy + py_ * 8 * s), (hx + ux * 8 * s, hy + uy * 8 * s), (hx - px_ * 8 * s, hy - py_ * 8 * s)])
                self.a_line(dk, hx - ux * 26 * s, hy - uy * 26 * s, hx + ux * 6 * s, hy + uy * 6 * s, 1)
        elif kind == 0:
            sx = cx + 38 * s
            self.a_poly(ivory, [(sx - 9 * s, cy - 72 * s), (sx + 9 * s, cy - 72 * s), (sx + 7 * s, cy + 30 * s), (sx, cy + 42 * s), (sx - 7 * s, cy + 30 * s)])
            self.a_line(c((190, 150, 70)), sx - 9 * s, cy - 40 * s, sx + 9 * s, cy - 40 * s, lw)
            self.a_rect(c((200, 160, 70)), sx - 10 * s, cy - 76 * s, 20 * s, 8 * s)
            self.a_circle(c((200, 160, 70)), sx, cy + 38 * s, 5 * s)
            self.a_poly(bronze, [(cx, cy - 86 * s), (cx + 9 * s, cy - 52 * s), (cx + 10 * s, cy + 8 * s), (cx - 10 * s, cy + 8 * s), (cx - 9 * s, cy - 52 * s)])
            self.a_line(dk, cx, cy - 82 * s, cx, cy + 6 * s, lw)
            self.a_rect(dk, cx - 17 * s, cy + 8 * s, 34 * s, 6 * s)
            self.a_rect(grip, cx - 5 * s, cy + 14 * s, 10 * s, 38 * s)
            for k in range(4):
                self.a_circle(silver, cx, cy + 21 * s + k * 9 * s, 3 * s)
            self.a_circle(silver, cx, cy + 56 * s, 8 * s)
        elif kind == 1:
            self.a_poly(bronze, [(cx, cy - 112 * s), (cx + 5 * s, cy - 62 * s), (cx + 6 * s, cy + 4 * s), (cx - 6 * s, cy + 4 * s), (cx - 5 * s, cy - 62 * s)])
            self.a_line(dk, cx, cy - 108 * s, cx, cy + 2 * s, lw)
            for sg in (-1, 1):
                self.a_poly(dk, [(cx + sg * 6 * s, cy + 4 * s), (cx + sg * 19 * s, cy - 5 * s), (cx + sg * 15 * s, cy + 15 * s), (cx + sg * 6 * s, cy + 15 * s)])
                self.a_circle(bronze, cx + sg * 13 * s, cy + 5 * s, max(1, 2 * s))
            self.a_rect(grip, cx - 4 * s, cy + 15 * s, 8 * s, 34 * s)
            self.a_circle(bronze, cx, cy + 20 * s, 3 * s)
            self.a_circle(bronze, cx, cy + 34 * s, 3 * s)
            self.a_circle(dk, cx, cy + 54 * s, 8 * s)
            self.a_circle(bronze, cx, cy + 54 * s, 8 * s, 2)
        else:
            pts = [(cx, cy - 78 * s), (cx + 10 * s, cy - 58 * s), (cx + 19 * s, cy - 26 * s), (cx + 17 * s, cy - 2 * s), (cx + 10 * s, cy + 8 * s),
                   (cx - 10 * s, cy + 8 * s), (cx - 17 * s, cy - 2 * s), (cx - 19 * s, cy - 26 * s), (cx - 10 * s, cy - 58 * s)]
            self.a_poly(bronze, pts)
            self.a_poly(c((246, 218, 150)), pts, 2)
            self.a_line(dk, cx, cy - 74 * s, cx, cy + 6 * s, lw)
            self.a_rect(dk, cx - 15 * s, cy + 8 * s, 30 * s, 7 * s)
            for k in range(3):
                self.a_circle(bronze, cx - 9 * s + k * 9 * s, cy + 11.5 * s, max(1, 2 * s))
            self.a_rect(grip, cx - 5 * s, cy + 15 * s, 10 * s, 30 * s)
            self.a_rect(dk, cx - 11 * s, cy + 45 * s, 22 * s, 7 * s)

    def draw_armory(self, tk):
        b = self.bt
        ph = b["phase"]
        ox, oy = self.shake_offset
        self.draw_frame_box()
        self.a_begin()
        self.a_rect((40, 32, 28), 53, 83, 694, 434)
        for by in range(83, 517, 36):
            off = 23 if ((by - 83) // 36) % 2 else 0
            for bx in range(53, 770, 46):
                self.a_rect((50, 41, 35), bx + off - 23, by, 44, 34)
        self.a_rect((70, 54, 40), 53, 474, 694, 43)
        for tx in (120, 680):
            self.a_glow(tx, 250, 130, (255, 150, 50), 80)
            self.a_rect((70, 50, 30), tx - 3, 262, 6, 40)
            self.a_flame(tx, 264, 16, 30, tk, tx)
        if ph == "arrows_out":
            self.a_rect((112, 76, 42), 150, 300, 56, 160)
            self.a_rect((86, 56, 30), 150, 300, 56, 160, 3)
            self.a_ellipse((18, 12, 8), 150, 292, 56, 18)
            self.a_line((60, 40, 24), 150, 340, 206, 340, 4)
            self.a_line((60, 40, 24), 150, 420, 206, 420, 4)
            self.a_line((60, 40, 24), 178, 300, 270, 250, 3)
            for k in range(5):
                x = 250 + k * 38
                y = 470 + (k % 2) * 8
                self.a_line((214, 184, 124), x, y, x + 26, y - 8 + (k % 3) * 4, 3)
                self.a_line((200, 50, 50), x, y, x - 6, y - 5, 2)
                self.a_line((200, 50, 50), x, y, x - 6, y + 4, 2)
            self.a_rect((86, 60, 32), 470, 244, 230, 10)
            for i, ak in enumerate((4, 3, 4)):
                self.a_sword_art(ak, 520 + i * 70, 340, 0.62, 0.55)
        self.a_end()
        if ph == "arrows_out":
            msg = "You have ran out of arrows. Grab a spear from the storeroom or a sword from the hall."
            self.draw_text(msg, self.title_font, BLACK, WIDTH // 2 + ox + 2, 132 + oy, center=True, max_width=640)
            self.draw_text(msg, self.title_font, WHITE, WIDTH // 2 + ox, 130 + oy, center=True, max_width=640)
            if (tk // 25) % 2 == 0:
                self.draw_text("Press SPACE to continue", self.font, CRT_GREEN, WIDTH // 2 + ox, 484 + oy, center=True)
        elif ph == "armory":
            self.a_title("THE STOREROOM AND THE HALL", GOLD, 88)
            for i, sw in enumerate(BT_SWORDS):
                x0, y0, w, h = 90 + i * 330, 134, 290, 366
                pulse = 190 + int(math.sin(tk * 0.1 + i) * 40)
                self.a_rect((26, 20, 14), x0, y0, w, h)
                self.a_rect((pulse, int(pulse * 0.8), 60), x0, y0, w, h, 3)
                self.a_circle(GOLD, x0 + 24, y0 + 24, 15)
                self.draw_text(str(i + 1), self.font, BLACK, x0 + 18 + ox, y0 + 15 + oy)
                self.a_sword_art(sw["art"], x0 + w // 2 - 10, y0 + 112, 0.9)
                self.draw_text(sw["name"], self.font, WHITE, x0 + w // 2 + ox, y0 + 186 + oy, center=True, max_width=270)
                self.draw_text(sw["boost"], self.small_font, CRT_GREEN, x0 + w // 2 + ox, y0 + 240 + oy, center=True, max_width=266)
                self.draw_text(sw["lore"], self.small_font, (214, 200, 170), x0 + w // 2 + ox, y0 + 284 + oy, center=True, max_width=266)
            if (tk // 25) % 2 == 0:
                self.draw_text("Press 1 or 2 to take your weapon", self.font, CRT_GREEN, WIDTH // 2 + ox, 538 + oy, center=True)
        else:
            sw = b["wp"]
            self.a_begin()
            self.a_glow(400, 270, 150, (255, 226, 150), 70)
            self.a_sword_art(sw["art"], 400, 280, 1.5)
            self.a_end()
            self.a_title("ARMED AND READY!", GOLD, 96)
            self.draw_text(sw["name"], self.font, GOLD, WIDTH // 2 + ox, 372 + oy, center=True)
            self.draw_text(sw["lore"], self.small_font, WHITE, WIDTH // 2 + ox, 404 + oy, center=True, max_width=560)
            self.draw_text(sw["boost"], self.small_font, CRT_GREEN, WIDTH // 2 + ox, 454 + oy, center=True, max_width=560)
            if (tk // 25) % 2 == 0:
                self.draw_text("Left click to attack. Press SPACE to fight on!", self.font, WHITE, WIDTH // 2 + ox, 486 + oy, center=True)

    def draw_sailing_sky(self):
        ox, oy = self.shake_offset
        kind = SAIL_KINDS.get(self.location_index, "sunny")
        w = SAIL_SKIES[kind]
        tk = pygame.time.get_ticks() // 16
        u = 1.0 - max(0, self.hunting_timer) / 240.0
        hz = 350
        self.sail_wave_col = _mix(BLUE, (8, 22, 52), w["tint"])
        self.sail_foam_col = _mix(WHITE, (150, 160, 184), w["tint"] * 0.7)
        for i in range(16):
            self.a_rect(_mix(w["top"], w["bot"], i / 15.0), 0, i * 23, WIDTH, 25)
        if w.get("stars"):
            for sx, sy, ph in STAR_FIELD:
                if (tk // 12 + ph) % 5 != 0:
                    self.a_rect((255, 255, 235), sx * 1.05, sy, 2, 2)
            self.a_moon(610, 120, 24)
        if w["sun"] is not None:
            sx, sy = w["sun"]
            sx = sx + (u - 0.5) * 70
            self.a_glow(sx, sy, 150, w["sun_col"], 110)
            self.a_circle(w["sun_col"], sx, sy, 30)
        if w.get("bolt") and (tk // 4) % 64 < 2:
            seed = tk // 4
            self.a_bolt(180 + (seed * 97) % 440, 60, 220 + (seed * 53) % 360, hz + 20, seed, 3)
        for i in range(w["n"]):
            cx = (i * 190 + tk * (0.35 + (i % 3) * 0.12)) % 1000 - 140
            cy = 90 + (i * 47) % 190
            sc = 1.0 + (i % 3) * 0.4
            shade = _mix(w["cloud"], (0, 0, 0), 0.16)
            self.a_cloud(cx + 4, cy + 7, sc, shade)
            self.a_cloud(cx, cy, sc, w["cloud"])
        if w.get("fog"):
            for i in range(7):
                self.a_glow((i * 150 + tk * 0.4) % 900 - 50, 300 + (i % 3) * 30, 210, (214, 218, 224), 80)
        if kind in ("sunny", "noon", "dawn"):
            for k in range(3):
                gx = (tk * (1.4 + k * 0.3) + k * 260) % 900 - 50
                gy = 170 + k * 34 + math.sin(tk * 0.05 + k) * 8
                fl = abs(math.sin(tk * 0.25 + k)) * 4
                self.a_lines(WHITE, [(gx - 9, gy - fl), (gx, gy), (gx + 9, gy - fl)], 2)
        far_top = _mix(w["bot"], (60, 120, 200), 0.55)
        far_bot = _mix((40, 100, 190), (10, 24, 50), w["tint"])
        for i in range(7):
            self.a_rect(_mix(far_top, far_bot, i / 6.0), 0, hz + i * 15, WIDTH, 17)
        if w["sun"] is not None:
            sx = w["sun"][0] + (u - 0.5) * 70
            for k in range(8):
                gx = sx + math.sin(tk * 0.1 + k) * 10 + (k - 4) * 6
                self.a_rect(w["sun_col"], gx - (14 - k), hz + 6 + k * 11, 28 - 2 * k, 2)
        if w.get("rain"):
            for i in range(90):
                x = (i * 131 + tk * 9) % WIDTH
                y = (i * 67 + tk * 23) % 440
                self.a_line((150, 175, 210), x, y, x - 5, y + 14, 1)
        if w.get("bolt") and (tk // 4) % 64 < 2:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 255, 255, 80))
            self.screen.blit(flash, (0, 0))
        self.draw_text("SAILING ON THE OPEN SEA...", self.title_font, BLACK, WIDTH // 2 + ox + 2, 82 + oy, center=True)


    # ==================================================================
    #  ODYSSEUS PROVES WHO HE IS (Books 21, 23 and 24)
    # ==================================================================
    def a_proof_panel(self, scene, t, wipe):
        x0, y0, w, h = 270, 148, 260, 126
        self.a_rect((40, 28, 18), x0 - 6, y0 - 6, w + 12, h + 12)
        self.a_rect((228, 206, 152), x0 - 6, y0 - 6, w + 12, h + 12, 3)
        if scene == 0:       # the boar hunt on Mount Parnassus, long ago
            self.a_rect((40, 74, 52), x0, y0, w, h)
            for tx in (286, 336, 392, 446, 500):
                self.a_rect((50, 36, 24), tx, y0, 8, 100)
                self.a_circle((30, 84, 50), tx + 4, y0 + 18, 22)
            self.a_rect((70, 110, 60), x0, 238, w, 36)
            self.a_boar(318 + int(math.sin(t * 0.3) * 3), 232, 72, 34, t)
            self.a_line((150, 110, 60), 456, 236, 390, 237, 3)
            self.a_poly((214, 218, 228), [(388, 237), (398, 232), (398, 242)])
            self.a_man(470, 262, (196, 62, 56), -1, 0, -3, "fwd", 1.3, helmet=False)
            self.a_man(506, 266, (60, 90, 150), -1, 0, 0, "up", 0.9)
        elif scene == 1:     # the scar, close up
            self.a_rect((90, 60, 40), x0, y0, w, h)
            self.a_glow(400, 212, 90, (255, 220, 160), 90)
            self.a_ellipse((228, 186, 148), 296, 178, 208, 64)
            self.a_ellipse((206, 160, 124), 296, 224, 208, 24)
            pts = [(330, 208), (350, 198), (366, 214), (384, 196), (400, 212), (418, 198), (436, 214), (460, 200)]
            self.a_lines((252, 238, 232), pts, 5)
            self.a_lines((196, 126, 116), [(x, y + 3) for x, y in pts], 2)
            self.a_glow(396, 206, 50, (255, 240, 200), int(70 + math.sin(t * 0.15) * 30))
        else:                # the marriage bed, built around a living olive tree
            self.a_rect((52, 44, 36), x0, y0, w, h)
            self.a_rect((92, 72, 54), x0, 252, w, 22)
            self.a_poly((112, 82, 48), [(386, 158), (414, 158), (420, 262), (380, 262)])
            for k in range(3):
                self.a_line((84, 58, 32), 392 + k * 8, 166, 390 + k * 9, 258, 2)
            for cx_, cy_, r_ in ((372, 168, 22), (408, 164, 24), (442, 176, 18), (350, 182, 16)):
                self.a_circle((92, 128, 90), cx_, cy_, r_)
            self.a_rect((124, 84, 42), 326, 238, 148, 10)
            for px_ in (332, 460):
                self.a_rect((124, 84, 42), px_, 246, 8, 20)
            for k in range(7):
                self.a_line((130, 40, 140), 332 + k * 20, 240, 340 + k * 20, 247, 2)
            for k in range(6):
                self.a_circle(GOLD if k % 2 else (224, 228, 238), 338 + k * 24, 243, 2)
        if wipe < 0.08:
            self.a_rect((255, 255, 255), x0, y0, int(w * (1 - wipe / 0.08)) + 1, h)

    def anim_odysseus_proves_himself(self):
        t = 720 - self.anim_timer
        p = t / 720.0
        G = 500
        self.a_begin()
        self.a_hall(t, "listen", True, False)
        # Penelope's chair, on the dais
        self.a_rect((172, 152, 120), 560, 496, 190, 12)
        self.a_rect((196, 176, 140), 550, 508, 210, 9)
        self.a_rect((110, 76, 40), 690, 384, 12, 112)
        self.a_rect((130, 90, 48), 672, 384, 50, 10)
        weeping = 0.30 <= p < 0.50
        # the watchers
        self.a_man(130, G, (70, 112, 204), 1, 0, 0, "up" if p >= 0.92 else "down", 2.6, helmet=False)
        eh = self.a_man(340, G, (98, 128, 72), 1, 0, 4 if weeping else 0, "up" if weeping else "down", 2.6, helmet=False, hair=(150, 150, 150))
        ph_ = self.a_man(410, G, (140, 96, 54), 1, 0, 4 if weeping else 0, "up" if weeping else "down", 2.6, helmet=False)
        ex = 480 + (36 * min(1.0, (p - 0.5) / 0.1) if 0.5 <= p < 0.62 else (36 if 0.62 <= p < 0.7 else 0))
        self.a_penelope(ex, G, 1.8, -1, 0.8 if weeping else 0.0, (150, 140, 156), False, (196, 196, 196))
        if weeping:
            for who in (eh, ph_, (ex, G - 81)):
                for k in range(2):
                    self.a_circle((170, 210, 255), who[0] + 5, who[1] + 6 + ((t * 2 + k * 8) % 16), 2)
        # Penelope tests him, then runs to him
        px = 620 - min(1.0, max(0.0, (p - 0.78) / 0.13)) * 330 if p >= 0.78 else 620
        gp = G - 4 if px > 560 else G
        arm = 1.0 if 0.5 <= p < 0.64 else (0.9 if p >= 0.9 else 0.0)
        self.a_penelope(px, gp, 2.1, -1, arm)
        # Odysseus, restored by Athena
        ox_ = 230
        self.a_glow(ox_, 410, 110, (255, 226, 150), 45 + int(math.sin(t * 0.08) * 12))
        angry = 0.55 <= p < 0.76
        arms = "up" if angry else ("fwd" if p >= 0.88 else "down")
        self.a_odysseus(ox_, G, 3.0, "king", arms, 5 if angry else 0)
        if 0.12 <= p < 0.46:
            self.a_lines((252, 238, 232), [(236, 466), (242, 471), (237, 477), (244, 482)], 3)
            self.a_glow(240, 474, 22, (255, 240, 200), int(110 + math.sin(t * 0.2) * 40))
        # his proofs appear in the air above the hearth
        scene, start = None, 0.0
        if 0.10 <= p < 0.28:
            scene, start = 0, 0.10
        elif 0.28 <= p < 0.46:
            scene, start = 1, 0.28
        elif 0.52 <= p < 0.80:
            scene, start = 2, 0.52
        if scene is not None:
            self.a_proof_panel(scene, t, min(1.0, (p - start) / 0.18))
            for bx, by, br in ((284, 296, 6), (268, 326, 9), (254, 356, 12)):
                self.a_circle((236, 228, 200), bx, by, br)
                self.a_circle((140, 120, 80), bx, by, br, 2)
        if p >= 0.9:
            for q in range(10):
                a = q * 0.63 + t * 0.05
                self.a_glow(262 + math.cos(a) * 60, 410 + math.sin(a) * 50, 8, (255, 230, 150), 170)
        self.a_end()
        self.a_title("ODYSSEUS PROVES HIMSELF", (255, 226, 150))

    def a_fruit_tree(self, x, y, s, kind):
        leaf = {"pear": (70, 140, 70), "apple": (60, 130, 66), "fig": (50, 120, 70)}[kind]
        self.a_rect((86, 60, 36), x - 4 * s, y - 40 * s, 8 * s, 40 * s)
        for dx, dy, r in ((0, -52, 26), (-18, -42, 20), (18, -42, 20), (0, -68, 18)):
            self.a_circle(leaf, x + dx * s, y + dy * s, r * s)
        fruit = {"pear": (196, 206, 84), "apple": (210, 50, 46), "fig": (110, 50, 110)}[kind]
        for k in range(9):
            self.a_circle(fruit, x + ((k * 37) % 44 - 22) * s, y - (34 + (k * 23) % 36) * s, max(1, 3 * s))

    def a_orchard_panel(self, scene, t, wipe):
        x0, y0, w, h = 270, 148, 260, 126
        if scene == 0:
            self.a_proof_panel(1, t, wipe)
            return
        self.a_rect((40, 28, 18), x0 - 6, y0 - 6, w + 12, h + 12)
        self.a_rect((228, 206, 152), x0 - 6, y0 - 6, w + 12, h + 12, 3)
        self.a_rect((150, 204, 238), x0, y0, w, h)
        self.a_rect((96, 150, 72), x0, 252, w, 22)
        if scene == 4:       # fifty rows of vines
            self.a_rect((170, 214, 130), x0, y0, w, h)
            for k in range(50):
                x = 282 + k * 4.7
                self.a_line((60, 120, 52), x, 168, x, 258, 2)
                self.a_circle((120, 56, 130), x, 204 + (k % 3) * 14, 2)
            return
        leaf = {1: (70, 140, 70), 2: (60, 130, 66), 3: (50, 120, 70)}[scene]
        fruit = {1: (196, 206, 84), 2: (210, 50, 46), 3: (112, 52, 112)}[scene]
        self.a_rect((110, 80, 46), 392, 200, 16, 56)
        for cx_, cy_, r_ in ((400, 190, 46), (360, 206, 32), (440, 206, 32), (400, 164, 28)):
            self.a_circle(leaf, cx_, cy_, r_)
        if scene == 1:       # thirteen pear trees' worth of pears
            layout = [(5, 186), (4, 208), (4, 230)]
            for cols, yy in layout:
                for c in range(cols):
                    xx = 400 + (c - (cols - 1) / 2.0) * 28
                    self.a_ellipse(fruit, xx - 5, yy - 6, 10, 14)
                    self.a_line((90, 60, 30), xx, yy - 6, xx + 2, yy - 10, 2)
        elif scene == 2:     # ten apple trees' worth of apples
            for r in range(2):
                for c in range(5):
                    self.a_circle(fruit, 400 + (c - 2) * 30, 196 + r * 26, 8)
                    self.a_circle((255, 150, 140), 397 + (c - 2) * 30, 193 + r * 26, 2)
        else:                # forty fig trees' worth of figs
            for r in range(5):
                for c in range(8):
                    self.a_circle(fruit, 306 + c * 26, 180 + r * 18, 6)

    def anim_odysseus_laertes(self):
        t = 540 - self.anim_timer
        p = t / 540.0
        G = 500
        self.a_begin()
        self.a_sky((96, 160, 230), (216, 238, 252), 83, 330)
        self.a_glow(620, 140, 120, (255, 250, 214), 110)
        self.a_circle((255, 250, 214), 620, 140, 28)
        self.a_poly((112, 156, 128), [(53, 340), (53, 290), (180, 252), (320, 304), (470, 262), (640, 312), (747, 270), (747, 340)])
        for i in range(10):
            self.a_rect(_mix((120, 170, 86), (70, 120, 60), i / 9.0), 53, 330 + i * 19, 694, 21)
        for r in range(9):
            self.a_line((56, 112, 50), 70 + r * 24, 372, 82 + r * 24, 352, 4)
            self.a_circle((120, 56, 130), 76 + r * 24, 364, 3)
        for tx_, ty_, sc, kind in ((250, 400, 1.2, "pear"), (340, 384, 0.9, "pear"), (430, 396, 1.1, "apple"), (520, 380, 0.9, "apple"), (620, 394, 1.2, "fig"), (710, 380, 0.9, "fig")):
            self.a_fruit_tree(tx_, ty_, sc, kind)
        self.a_rect((120, 90, 56), 53, 508, 694, 9)
        # old Laertes, digging at the foot of a young tree
        digging = p < 0.30
        dropped = p >= 0.30
        shock = math.sin(t * 0.6) * 3 if 0.30 <= p < 0.5 else 0
        if p >= 0.86:
            lx = 520 - min(1.0, (p - 0.86) / 0.1) * 24
        else:
            lx = 560
        lean = (8 + math.sin(t * 0.2) * 4) if digging else (-5 + shock if p < 0.86 else 0)
        lh = self.a_man(lx, G, (122, 102, 72), -1, 0, lean, "down" if digging else ("up" if p < 0.86 else "fwd"), 2.4, helmet=False, hair=(206, 206, 206))
        self.a_poly((214, 214, 214), [(lh[0] - 4 * 2.4, lh[1] + 2 * 2.4), (lh[0] + 4 * 2.4, lh[1] + 2 * 2.4), (lh[0] + 2 * 2.4, lh[1] + 11 * 2.4), (lh[0] - 2 * 2.4, lh[1] + 11 * 2.4)])
        if digging:
            sw = math.sin(t * 0.2) * 10
            self.a_line((110, 80, 50), lx - 16, G - 62, lx - 36 + sw, G - 4, 4)
            self.a_poly((190, 192, 202), [(lx - 46 + sw, G - 6), (lx - 28 + sw, G - 4), (lx - 36 + sw, G + 4)])
        elif p < 0.5:
            self.a_line((110, 80, 50), 505, G - 4, 470, G - 16, 4)
        # Odysseus comes through the orchard
        if p < 0.26:
            ox_ = 120 + (p / 0.26) * 300
            walk = math.sin(t * 0.35) * 5
        elif p < 0.86:
            ox_, walk = 420, 0
        else:
            ox_, walk = 420 + min(1.0, (p - 0.86) / 0.1) * 40, 0
        self.a_odysseus(ox_, G, 3.0, "king", "fwd" if p >= 0.86 else "down", 0, walk)
        if 0.34 <= p < 0.46:
            self.a_lines((252, 238, 232), [(ox_ + 6, 466), (ox_ + 12, 471), (ox_ + 7, 477), (ox_ + 14, 482)], 3)
            self.a_glow(ox_ + 10, 474, 22, (255, 240, 200), 150)
        # the proofs: the scar, then the trees his father gave him
        scene, start = None, 0.0
        for sc_i, (a_, b_) in enumerate(((0.34, 0.46), (0.46, 0.58), (0.58, 0.68), (0.68, 0.78), (0.78, 0.88))):
            if a_ <= p < b_:
                scene, start = sc_i, a_
        if scene is not None:
            self.a_orchard_panel(scene, t, min(1.0, (p - start) / 0.12))
            for bx, by, br in ((470, 292, 6), (480, 322, 9), (490, 356, 12)):
                self.a_circle((236, 228, 200), bx, by, br)
                self.a_circle((140, 120, 80), bx, by, br, 2)
        if p >= 0.9:
            for q in range(10):
                a = q * 0.63 + t * 0.05
                self.a_glow(470 + math.cos(a) * 60, 410 + math.sin(a) * 50, 8, (255, 230, 150), 170)
        self.a_end()
        self.a_title("THE ORCHARD OF LAERTES", (255, 226, 150))

    # ==================================================================
    #  ITHACA AT LAST - the beach at dawn
    # ==================================================================
    def draw_victory_beach(self):
        ox, oy = self.shake_offset
        tk = pygame.time.get_ticks() // 16
        for i in range(20):
            pygame.draw.rect(self.screen, _mix((64, 132, 224), (255, 224, 176), i / 19.0), (ox, oy + i * 19, WIDTH, 21))
        sx, sy = 560, 262
        for k in range(14):
            a = k * 0.449 + tk * 0.004
            self.a_line((255, 236, 180), sx + math.cos(a) * 52, sy + math.sin(a) * 52, sx + math.cos(a) * 130, sy + math.sin(a) * 130, 2)
        self.a_glow(sx, sy, 200, (255, 214, 140), 110 + int(math.sin(tk * 0.03) * 20))
        self.a_circle((255, 244, 210), sx, sy, 38)
        for i in range(5):
            cx = (i * 210 + tk * (0.25 + (i % 3) * 0.1)) % 1000 - 140
            self.a_cloud(cx + 4, 120 + (i * 41) % 110 + 6, 1.1 + (i % 2) * 0.4, (240, 196, 168))
            self.a_cloud(cx, 120 + (i * 41) % 110, 1.1 + (i % 2) * 0.4, (255, 236, 220))
        self.a_poly((92, 124, 124), [(0, 340), (0, 296), (110, 246), (220, 290), (340, 230), (470, 296), (600, 262), (720, 300), (800, 270), (800, 340)])
        self.a_poly((112, 146, 130), [(0, 352), (0, 322), (160, 292), (300, 330), (470, 300), (640, 334), (800, 306), (800, 352)])
        self.a_palace(660, 330, 0.3)
        for i in range(8):
            pygame.draw.rect(self.screen, _mix((70, 150, 220), (40, 100, 180), i / 7.0), (ox, oy + 340 + i * 17, WIDTH, 19))
        for k in range(10):
            gx = sx + math.sin(tk * 0.07 + k) * 12 + (k - 5) * 5
            self.a_rect((255, 240, 190), gx - (12 - k), 350 + k * 11, 24 - 2 * k, 2)
        for x in range(0, WIDTH, 30):
            wy = 430 + int(math.sin(x / 70.0 + tk * 0.05) * 6)
            pygame.draw.rect(self.screen, (58, 148, 232), (x + ox, wy + oy, 30, 60))
            pygame.draw.rect(self.screen, WHITE, (x + ox, wy + oy, 30, 4))
        self.a_poly((238, 216, 162), [(0, 600), (0, 478), (200, 462), (460, 480), (800, 456), (800, 600)])
        foam = int(math.sin(tk * 0.05) * 8)
        self.a_poly((255, 255, 255), [(0, 478 + foam), (200, 462 + foam), (460, 480 + foam), (800, 456 + foam), (800, 462 + foam), (460, 486 + foam), (200, 468 + foam), (0, 484 + foam)])
        self.a_poly((212, 188, 132), [(0, 600), (0, 548), (260, 540), (520, 552), (800, 536), (800, 600)])
        for tx_, ty_, sc in ((70, 520, 1.5), (740, 508, 1.3)):
            self.a_poly((86, 64, 40), [(tx_ - 6 * sc, ty_), (tx_ + 6 * sc, ty_), (tx_ + 3 * sc, ty_ - 52 * sc), (tx_ - 3 * sc, ty_ - 52 * sc)])
            self.a_circle((112, 140, 98), tx_, ty_ - 62 * sc, 32 * sc)
            self.a_circle((140, 168, 118), tx_ - 8 * sc, ty_ - 70 * sc, 16 * sc)
        # Odysseus and Penelope, hand in hand at last, with Telemachus beside them
        sway = math.sin(tk * 0.04) * 2
        self.a_man(470, 540, (70, 112, 204), -1, 0, 0, "down", 2.8, helmet=False)
        self.a_penelope(378, 540, 2.1, 1, 0.0)
        self.a_odysseus(330 + sway, 540, 3.1, "king", "fwd", 0)
        for k in range(3):
            gx = (tk * (1.2 + k * 0.3) + k * 300) % 900 - 50
            gy = 150 + k * 38 + math.sin(tk * 0.05 + k) * 10
            fl = abs(math.sin(tk * 0.25 + k)) * 5
            self.a_lines(WHITE, [(gx - 11, gy - fl), (gx, gy), (gx + 11, gy - fl)], 2)
        for q in range(14):
            u = ((tk * 0.6 + q * 31) % 220) / 220.0
            self.a_glow((q * 61) % 780 + 10 + math.sin(u * 6 + q) * 14, 520 - u * 300, 7, (255, 232, 150), int(160 * (1 - u)))
        if not hasattr(self, "big_font"):
            self.big_font = pygame.font.SysFont('courier', 60, bold=True)
        text = "ITHACA AT LAST!"
        y = 70 + int(math.sin(tk * 0.05) * 4)
        for dx, dy in ((4, 4), (-2, 0), (2, 0), (0, -2), (0, 2)):
            sh = self.big_font.render(text, True, (60, 36, 10))
            r = sh.get_rect()
            r.centerx = WIDTH // 2 + ox + dx
            r.y = y + oy + dy
            self.screen.blit(sh, r)
        img = self.big_font.render(text, True, GOLD)
        r = img.get_rect()
        r.centerx = WIDTH // 2 + ox
        r.y = y + oy
        self.screen.blit(img, r)
        self.draw_text("After twenty years, Odysseus is home.", self.font, BLACK, WIDTH // 2 + ox + 2, 152 + oy, center=True)
        self.draw_text("After twenty years, Odysseus is home.", self.font, WHITE, WIDTH // 2 + ox, 150 + oy, center=True)
        if (tk // 28) % 2 == 0:
            self.draw_text("Press SPACE to play again", self.font, BLACK, WIDTH // 2 + ox + 2, 566 + oy, center=True)
            self.draw_text("Press SPACE to play again", self.font, WHITE, WIDTH // 2 + ox, 564 + oy, center=True)

    # ==================================================================
    #  THE MAP
    # ==================================================================
    def map_node(self, i):
        loc = self.locations[i]
        if loc["id"] == "circe_return":
            loc = self.locations[[l["id"] for l in self.locations].index("circe")]
        return loc["x"], loc["y"]

    def build_map_bg(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        saved = (self.screen, self.shake_offset)
        self.screen, self.shake_offset = bg, (0, 0)
        rnd = random.Random(21)
        self.a_rect((226, 204, 154), 0, 0, WIDTH, HEIGHT)
        for k in range(520):
            c = rnd.choice([(214, 190, 138), (234, 214, 168), (206, 180, 128)])
            self.a_rect(c, rnd.randint(20, 780), rnd.randint(20, 580), rnd.randint(1, 4), rnd.randint(1, 2))
        # waves drawn in ink on the open sea
        for k in range(120):
            x, y = rnd.randint(40, 760), rnd.randint(100, 570)
            self.a_lines((150, 160, 150), [(x + j * 4, y + math.sin(j) * 1.5) for j in range(6)], 1)

        def blob(cx, cy, r, seed, n=14, sq=0.8):
            rr = random.Random(seed)
            return [(cx + math.cos(i * 6.283 / n) * r * (0.72 + 0.5 * rr.random()), cy + math.sin(i * 6.283 / n) * r * sq * (0.72 + 0.5 * rr.random())) for i in range(n)]

        def land(pts, ripples=((1.16, (200, 208, 192)), (1.08, (210, 214, 190)))):
            cx = sum(p_[0] for p_ in pts) / len(pts)
            cy = sum(p_[1] for p_ in pts) / len(pts)
            for k, col in ripples:
                self.a_poly(col, [(cx + (x - cx) * k, cy + (y - cy) * k) for x, y in pts])
            self.a_poly((196, 176, 114), pts)
            self.a_poly((92, 62, 30), pts, 2)
            for m in range(3):
                mx, my = cx + (m - 1) * 11, cy + (m % 2) * 6 - 4
                self.a_poly((132, 96, 52), [(mx - 6, my + 5), (mx, my - 6), (mx + 6, my + 5)])

        # the mainland coasts, ringed with ripples
        asia = [(780, 96), (780, 360), (752, 316), (730, 262), (744, 218), (724, 186), (746, 158), (734, 128), (752, 104)]
        europe = [(24, 90), (24, 124), (130, 112), (260, 130), (400, 112), (530, 128), (660, 108), (700, 96)]
        africa = [(500, 580), (540, 528), (574, 488), (610, 452), (660, 440), (704, 470), (780, 500), (780, 580)]
        for off in (14, 7):
            self.a_poly((208, 214, 192), [(x - off, y) for x, y in asia])
            self.a_poly((208, 214, 192), [(x, y + off) for x, y in europe])
            self.a_poly((208, 214, 192), [(x, y - off) for x, y in africa])
        for pts in (asia, europe, africa):
            self.a_poly((196, 176, 114), pts)
            self.a_poly((92, 62, 30), pts, 2)
        for mx, my in ((760, 200), (766, 280), (748, 340), (500, 100), (300, 98), (140, 100), (620, 552), (700, 540)):
            self.a_poly((132, 96, 52), [(mx - 9, my + 7), (mx, my - 9), (mx + 9, my + 7)])
            self.a_poly((236, 224, 190), [(mx - 3, my - 3), (mx, my - 9), (mx + 3, my - 3)])
        # islands, one for each place on the voyage
        sizes = {"cicones": 22, "cyclops": 38, "laestrygonians": 26, "circe": 32, "sirens": 12, "scylla": 22, "helios": 34, "ogygia": 26, "phaeacia": 30, "ithaca": 28}
        for idx, loc in enumerate(self.locations):
            lid = loc["id"]
            if lid in sizes:
                land(blob(loc["x"], loc["y"] - 4, sizes[lid], idx * 7 + 3))
        for ax_, ay_ in ((428, 148), (452, 170), (470, 150)):
            land(blob(ax_, ay_, 11, int(ax_)), ((1.3, (200, 208, 192)),))
        # the misty edge of the world where the shades dwell
        hx, hy = [(l["x"], l["y"]) for l in self.locations if l["id"] == "hades"][0]
        self.a_glow(hx, hy, 70, (70, 60, 90), 120)
        for k in range(3):
            self.a_lines((60, 50, 80), [(hx + math.cos(j * 0.6 + k * 2.1) * (6 + j * 3), hy + math.sin(j * 0.6 + k * 2.1) * (6 + j * 3)) for j in range(12)], 2)
        # sea serpent, for good measure
        sp = [(560 + j * 11, 330 + math.sin(j * 0.9) * 9) for j in range(14)]
        self.a_lines((80, 120, 96), sp, 4)
        self.a_circle((80, 120, 96), sp[-1][0], sp[-1][1], 6)
        self.a_circle((236, 224, 190), sp[-1][0] + 2, sp[-1][1] - 2, 2)
        # compass rose
        cx, cy = 94, 148
        self.a_circle((236, 220, 176), cx, cy, 40)
        self.a_circle((92, 62, 30), cx, cy, 40, 2)
        self.a_circle((92, 62, 30), cx, cy, 30, 1)
        for k in range(4):
            a = k * 1.5708 - 1.5708
            tip = (cx + math.cos(a) * 38, cy + math.sin(a) * 38)
            self.a_poly((150, 40, 30) if k == 0 else (92, 62, 30), [tip, (cx + math.cos(a + 0.35) * 9, cy + math.sin(a + 0.35) * 9), (cx, cy), (cx + math.cos(a - 0.35) * 9, cy + math.sin(a - 0.35) * 9)])
        for k in range(4):
            a = k * 1.5708 - 0.7854
            self.a_poly((170, 140, 90), [(cx + math.cos(a) * 24, cy + math.sin(a) * 24), (cx + math.cos(a + 0.4) * 7, cy + math.sin(a + 0.4) * 7), (cx, cy), (cx + math.cos(a - 0.4) * 7, cy + math.sin(a - 0.4) * 7)])
        self.draw_text("N", self.small_font, (150, 40, 30), cx - 4, cy - 58)
        # title banner and the ornate border
        title = "MEDITERRANEAN SEA CHART"
        tw, th = self.title_font.size(title)
        bw, bh = tw + 72, th + 20
        bx, by = (WIDTH - bw) // 2, 30
        self.a_rect((92, 62, 30), bx - 5, by - 5, bw + 10, bh + 10)
        self.a_rect((236, 218, 170), bx, by, bw, bh)
        self.a_rect((92, 62, 30), bx, by, bw, bh, 2)
        for cxb in (bx - 6, bx + bw + 6):
            self.a_circle((92, 62, 30), cxb, by + bh // 2, 11)
            self.a_circle((236, 218, 170), cxb, by + bh // 2, 5)
        self.draw_text(title, self.title_font, (70, 44, 18), WIDTH // 2, by + 10, center=True)
        pygame.draw.rect(self.screen, (92, 62, 30), (14, 14, WIDTH - 28, HEIGHT - 28), 7)
        pygame.draw.rect(self.screen, (150, 110, 60), (24, 24, WIDTH - 48, HEIGHT - 48), 2)
        for fx, fy in ((24, 24), (WIDTH - 24, 24), (24, HEIGHT - 24), (WIDTH - 24, HEIGHT - 24)):
            self.a_circle((92, 62, 30), fx, fy, 12)
            self.a_circle((236, 218, 170), fx, fy, 6)
        self.screen, self.shake_offset = saved
        vig = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        vig.fill((110, 70, 30, 110))
        for i in range(12):
            alpha = int(110 * (1 - i / 11.0) ** 2)
            pygame.draw.ellipse(vig, (110, 70, 30, alpha), (i * 34 - 40, i * 26 - 30, WIDTH - i * 68 + 80, HEIGHT - i * 52 + 60))
        bg.blit(vig, (0, 0))
        pygame.draw.rect(bg, (92, 62, 30), (14, 14, WIDTH - 28, HEIGHT - 28), 7)
        self._map_bg = bg

    def draw_map(self):
        ox, oy = self.shake_offset
        tk = pygame.time.get_ticks() // 16
        if self._map_bg is None:
            self.build_map_bg()
        self.screen.blit(self._map_bg, (ox, oy))
        ink, red = (70, 40, 20), (160, 36, 28)
        # the route taken so far; a return along the same road bows the other way
        seen = {}
        for i in range(1, self.location_index + 1):
            a, b = self.map_node(i - 1), self.map_node(i)
            if a == b:
                continue
            key = frozenset((a, b))
            sign = 1 if seen.get(key, 0) % 2 == 0 else -1
            seen[key] = seen.get(key, 0) + 1
            mx_, my_ = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
            dx, dy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(dx, dy) or 1.0
            cx_, cy_ = mx_ - dy / d * 26 * sign, my_ + dx / d * 26 * sign
            col = red if sign == 1 else (40, 90, 150)
            pts = [((1 - u) ** 2 * a[0] + 2 * (1 - u) * u * cx_ + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * cy_ + u * u * b[1]) for u in [k / 20.0 for k in range(21)]]
            for k in range(0, 20, 2):
                self.a_line(col, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], 3)
            ex, ey = pts[-1]
            ang = math.atan2(pts[-1][1] - pts[-3][1], pts[-1][0] - pts[-3][0])
            self.a_poly(col, [(ex, ey), (ex - math.cos(ang - 0.45) * 12, ey - math.sin(ang - 0.45) * 12), (ex - math.cos(ang + 0.45) * 12, ey - math.sin(ang + 0.45) * 12)])
        # the places, each marked once however often the ship has been there
        drawn = set()
        for i in range(len(self.locations)):
            loc = self.locations[i]
            if loc["id"] == "circe_return":
                continue
            x, y = loc["x"], loc["y"]
            if i > self.location_index:
                self.draw_text("?", self.small_font, (140, 110, 70), x - 4 + ox, y - 8 + oy)
                continue
            drawn.add(i)
            self.a_circle((236, 220, 176), x, y, 7)
            self.a_circle(red, x, y, 7, 2)
            self.a_circle(red, x, y, 3)
            name = loc["name"].replace(" (Circe Return)", "")
            lw = self.small_font.size(name)[0]
            lx = min(max(x - lw // 2, 36), WIDTH - 36 - lw)
            ly = y + 14
            self.draw_text(name, self.small_font, (240, 226, 188), lx + 1 + ox, ly + 1 + oy, max_width=1000)
            self.draw_text(name, self.small_font, (60, 34, 14), lx + ox, ly + oy, max_width=1000)
        # the ship, bobbing at the current stop
        cxn, cyn = self.map_node(self.location_index)
        bob = math.sin(tk * 0.08) * 3
        self.a_circle(red, cxn, cyn, 12 + int(math.sin(tk * 0.1) * 2), 2)
        self.a_poly((92, 52, 24), [(cxn - 12, cyn - 16 + bob), (cxn + 12, cyn - 16 + bob), (cxn + 7, cyn - 9 + bob), (cxn - 7, cyn - 9 + bob)])
        self.a_rect((92, 52, 24), cxn - 1, cyn - 30 + bob, 2, 14)
        self.a_poly((244, 236, 214), [(cxn + 1, cyn - 30 + bob), (cxn + 10, cyn - 26 + bob), (cxn + 1, cyn - 18 + bob)])
        self.draw_text("YOU ARE HERE", self.small_font, (240, 226, 188), cxn - 41 + ox, cyn - 52 + oy)
        self.draw_text("YOU ARE HERE", self.small_font, red, cxn - 42 + ox, cyn - 53 + oy)
        self.draw_text("Press ANY KEY to return", self.font, (240, 226, 188), WIDTH // 2 + 1 + ox, HEIGHT - 51 + oy, center=True)
        self.draw_text("Press ANY KEY to return", self.font, (70, 40, 20), WIDTH // 2 + ox, HEIGHT - 52 + oy, center=True)

    # ==================================================================
    #  THE TITLE SCREEN: TROY BURNS
    # ==================================================================
    def build_troy_bg(self):
        bg = pygame.Surface((WIDTH, HEIGHT))
        saved = (self.screen, self.shake_offset)
        self.screen, self.shake_offset = bg, (0, 0)
        rnd = random.Random(9)
        fires, torches = [], []
        # sky: smoke-dark above, burning orange at the horizon
        for i in range(31):
            k = i / 30.0
            col = _mix((8, 6, 24), (150, 52, 24), k ** 1.4) if k < 0.8 else _mix((150, 52, 24), (255, 132, 50), (k - 0.8) / 0.2)
            self.a_rect(col, 0, i * 12, WIDTH, 14)
        for _ in range(70):
            self.a_rect((230, 220, 210), rnd.randint(0, 800), rnd.randint(0, 150), 1, 1)
        self.a_glow(700, 66, 60, (255, 190, 150), 70)
        self.a_circle((226, 176, 146), 700, 66, 20)
        self.a_circle((200, 150, 124), 693, 62, 5)
        # the Achaean fleet on the dark sea beyond the plain
        self.a_rect((44, 22, 30), 0, 356, 190, 36)
        for k in range(8):
            self.a_rect((190, 80, 40), 10 + k * 22, 362 + (k % 3) * 9, 12, 2)
        self.a_ship(14, 346, 0, 0.32, True, False, 0, 0.8)
        self.a_ship(86, 354, 0, 0.28, True, False, 0, 0.8)
        self.a_poly((34, 20, 32), [(0, 392), (0, 372), (160, 358), (300, 368), (520, 352), (700, 362), (800, 350), (800, 392)])
        # the hill of Ilium
        self.a_poly((50, 36, 34), [(40, 404), (110, 350), (200, 300), (290, 258), (350, 236), (420, 256), (500, 296), (580, 346), (650, 404)])
        Lp = [(404, 40), (350, 110), (300, 200), (258, 290), (236, 350)]
        Rp = [(404, 650), (346, 580), (296, 500), (256, 420), (236, 350)]

        def interp(pts, y):
            for (y0, x0), (y1, x1) in zip(pts, pts[1:]):
                if y1 <= y <= y0:
                    return x0 + (x1 - x0) * (y0 - y) / float(y0 - y1)
            return pts[-1][1]
        # terraces of houses climbing the hill, windows lit by the flames
        for yb in (270, 292, 314, 336, 358, 378):
            xl, xr = interp(Lp, yb - 14), interp(Rp, yb - 14)
            x = xl + 10
            while x < xr - 40:
                w = rnd.randint(28, 46)
                h = rnd.randint(22, 40)
                sh = rnd.randint(-8, 8)
                self.a_rect((66 + sh, 50 + sh, 44 + sh), x, yb - h, w, h)
                self.a_rect((44, 32, 28), x - 2, yb - h - 4, w + 4, 5)
                self.a_rect((150, 78, 36), x, yb - h, 3, h)
                for wx in range(int(x) + 8, int(x + w) - 8, 12):
                    self.a_rect((255, 168, 56) if rnd.random() < 0.6 else (30, 18, 14), wx, yb - h + 8, 5, 8)
                self.a_rect((28, 18, 14), x + w // 2 - 4, yb - 12, 8, 12)
                if rnd.random() < 0.28:
                    fires.append((x + w / 2.0, yb - h - 4, w * 0.9, 26 + rnd.random() * 42, rnd.random() * 6))
                x += w + rnd.randint(2, 8)
        # the great curtain wall, its towers, and the Scaean Gate
        self.a_rect((78, 60, 52), 40, 376, 612, 30)
        for cx in range(40, 650, 22):
            self.a_rect((78, 60, 52), cx, 368, 14, 9)
        for tx, ty in ((86, 330), (188, 338), (412, 338), (516, 330), (612, 340)):
            self.a_rect((88, 68, 58), tx - 18, ty, 36, 76)
            for k in range(4):
                self.a_rect((88, 68, 58), tx - 18 + k * 10, ty - 8, 8, 9)
            self.a_rect((150, 78, 36), tx - 18, ty, 3, 76)
            self.a_rect((255, 168, 56), tx - 3, ty + 20, 6, 12)
            fires.append((tx, ty - 6, 28, 46, tx * 0.01))
        self.a_rect((30, 16, 10), 276, 360, 48, 46)
        self.a_circle((30, 16, 10), 300, 360, 24)
        self.a_rect((255, 130, 44), 286, 372, 28, 34)
        self.a_circle((255, 130, 44), 300, 372, 14)
        self.a_rect((70, 46, 30), 298, 360, 4, 46)
        # Priam's palace, the tower of Ilium, and the temple of Athena crown the hill
        self.a_rect((98, 78, 66), 262, 228, 124, 32)
        for k in range(9):
            self.a_rect((142, 108, 86), 268 + k * 13, 230, 6, 30)
        self.a_rect((190, 100, 44), 262, 228, 3, 32)
        self.a_poly((104, 52, 36), [(256, 228), (392, 228), (324, 200)])
        self.a_rect((92, 70, 60), 392, 168, 34, 90)
        for k in range(4):
            self.a_rect((92, 70, 60), 392 + k * 10, 160, 8, 9)
        self.a_rect((255, 168, 56), 405, 196, 6, 14)
        self.a_rect((190, 100, 44), 392, 168, 3, 90)
        self.a_rect((98, 78, 66), 196, 262, 66, 24)
        for k in range(5):
            self.a_rect((142, 108, 86), 202 + k * 13, 264, 5, 22)
        self.a_poly((104, 52, 36), [(190, 262), (268, 262), (229, 242)])
        fires += [(324, 204, 76, 92, 1.0), (409, 162, 34, 74, 2.0), (230, 244, 44, 56, 3.0), (300, 362, 34, 36, 4.0)]
        # the plain before the walls, strewn with ruin
        for i in range(10):
            self.a_rect(_mix((78, 30, 22), (26, 20, 24), i / 9.0), 0, 404 + i * 5, WIDTH, 6)
        for i in range(15):
            self.a_rect(_mix((44, 36, 36), (18, 16, 20), i / 14.0), 0, 450 + i * 10, WIDTH, 11)
        self.a_rect((190, 70, 30), 0, 450, WIDTH, 2)
        for _ in range(30):
            sx, sy, sw = rnd.randint(0, 800), rnd.randint(410, 446), rnd.randint(8, 22)
            self.a_ellipse((58, 46, 44), sx, sy, sw, sw * 0.5)
            self.a_ellipse((96, 66, 52), sx + 2, sy, sw * 0.6, sw * 0.25)
        for cx, cy in ((330, 424), (130, 430)):
            self.a_rect((120, 98, 82), cx, cy, 30, 14)
            self.a_ellipse((150, 126, 104), cx - 2, cy - 4, 34, 8)
        for sx, sy in ((250, 436), (440, 430), (60, 440)):
            self.a_circle((70, 50, 28), sx, sy, 11)
            self.a_circle((150, 104, 48), sx, sy, 11, 2)
            self.a_circle((150, 104, 48), sx, sy, 4)
        # the wooden horse, wheeled up to the gate
        hx, hy, k = 556, 442, 0.78

        def hp(dx, dy):
            return (hx + dx * k, hy + dy * k)
        wood, dk = (104, 66, 34), (66, 40, 22)
        self.a_rect((70, 46, 26), hx - 8, hy - 8, 160, 10)
        for wx in (14, 52, 100, 136):
            self.a_circle((54, 36, 22), hx + wx, hy + 4, 11)
            self.a_circle((126, 84, 44), hx + wx, hy + 4, 11, 2)
            self.a_line((126, 84, 44), hx + wx - 9, hy + 4, hx + wx + 9, hy + 4, 2)
            self.a_line((126, 84, 44), hx + wx, hy - 5, hx + wx, hy + 13, 2)
        for lx in (4, 38, 88, 120):
            self.a_rect(wood, hx + lx * k, hy - 78 * k, 18 * k, 70 * k)
            self.a_rect(dk, hx + (lx + 12) * k, hy - 78 * k, 6 * k, 70 * k)
            self.a_rect((40, 26, 16), hx + (lx - 2) * k, hy - 14 * k, 22 * k, 8 * k)
        body = [hp(0, -84), hp(2, -148), hp(70, -168), hp(122, -160), hp(150, -214), hp(166, -256), hp(196, -262), hp(210, -246), hp(184, -232),
                hp(176, -196), hp(160, -150), hp(156, -84)]
        self.a_poly(wood, body)
        for i in range(6):
            yy = -96 - i * 13
            self.a_line(dk, hp(6, yy)[0], hp(6, yy)[1], hp(152, yy)[0], hp(152, yy)[1], 2)
        self.a_poly(dk, [hp(176, -196), hp(160, -150), hp(156, -84), hp(140, -84), hp(150, -170)])
        self.a_poly(wood, [hp(166, -256), hp(206, -250), hp(216, -236), hp(200, -226), hp(176, -232)])
        self.a_poly(dk, [hp(176, -258), hp(184, -284), hp(190, -258)])
        self.a_circle((255, 190, 90), hp(186, -246)[0], hp(186, -246)[1], 3)
        for i in range(8):
            a, b = hp(124 + i * 5.6, -164 - i * 11.5), hp(112 + i * 5.6, -170 - i * 11.5)
            self.a_poly(dk, [a, b, (a[0] - 4, a[1] - 9)])
        self.a_lines((190, 150, 50), [hp(176, -232), hp(160, -214), hp(150, -214)], 2)
        self.a_lines(dk, [hp(0, -140), hp(-12, -120), hp(-8, -96)], 4)
        self.a_rect((50, 30, 16), hp(60, -130)[0], hp(60, -130)[1], 22 * k, 30 * k)
        self.a_lines((200, 110, 50), [hp(0, -84), hp(2, -148), hp(70, -168)], 3)
        # Greek soldiers with torches, spreading the fire
        for x, y in ((96, 446), (212, 448), (470, 446)):
            self.a_man(x, y, (78, 36, 32), 1, 0, 0, "up", 1.3, skin=(190, 140, 110))
            self.a_line((110, 76, 40), x, y - 52, x, y - 66, 3)
            torches.append((x, y - 66))
        self.screen, self.shake_offset = saved
        self._troy_bg, self._troy_fires, self._troy_torches = bg, fires, torches

    def draw_troy(self):
        ox, oy = self.shake_offset
        tk = pygame.time.get_ticks() // 16
        if self._troy_bg is None:
            self.build_troy_bg()
        self.screen.blit(self._troy_bg, (ox, oy))
        # the firestorm, glowing behind and above the citadel
        self.a_glow(340, 260, 250, (255, 100, 30), 85 + int(math.sin(tk * 0.07) * 14))
        self.a_glow(340, 140, 150, (255, 140, 50), 45)
        for sx, sy in ((324, 200), (409, 160), (230, 240), (470, 270)):
            self.a_smoke(sx, sy, tk, 5, (44, 40, 44))
        for i, (x, y, w, h, seed) in enumerate(self._troy_fires):
            self.a_flame(x, y, w, h, tk, seed)
            if i < 4 or i % 5 == 0:
                self.a_glow(x, y - h * 0.4, 36, (255, 140, 50), 55)
        self.a_glow(300, 384, 44, (255, 120, 40), 110)
        for x, y in self._troy_torches:
            self.a_glow(x, y - 8, 30, (255, 170, 70), 90)
            self.a_flame(x, y, 12, 26, tk, x * 0.1)
        for i in range(44):
            u = ((tk * 1.2 + i * 29) % 170) / 170.0
            ex = 120 + (i * 53) % 460 + math.sin(u * 7 + i) * 20 + u * 50
            ey = 340 - u * 300
            self.a_rect(_mix((255, 214, 96), (200, 50, 20), u), ex, ey, 2 + (i % 2), 2 + (i % 2))

    # ==================================================================
    #  THE HUNT - Odysseus with his bow, wild boars in the forest
    # ==================================================================
    def a_boar(self, x, y, w, h, tk):
        """A wild boar charging to the right. (x, y, w, h) is its hit box."""
        dark, mid, snout = (92, 68, 48), (112, 84, 60), (156, 118, 96)
        for k in range(3):
            self.a_circle((176, 150, 108), x - 8 - k * 12, y + h - 3 - k * 2, 5 - k)
        for k, fx in enumerate((0.20, 0.36, 0.62, 0.78)):
            lx = x + w * fx
            sw = math.sin(tk * 0.6 + k * 1.7) * 6
            self.a_line((54, 40, 30), lx, y + h * 0.6, lx + sw, y + h - 2, 4)
            self.a_rect((30, 22, 16), lx + sw - 3, y + h - 4, 6, 4)
        self.a_ellipse(dark, x + w * 0.06, y + h * 0.14, w * 0.72, h * 0.60)
        self.a_ellipse((120, 92, 66), x + w * 0.14, y + h * 0.22, w * 0.46, h * 0.28)
        for i in range(8):
            bx = x + w * (0.12 + i * 0.075)
            self.a_poly((50, 36, 26), [(bx, y + h * 0.26), (bx + w * 0.07, y + h * 0.26), (bx + w * 0.035, y + h * 0.0 + (i % 2) * 3)])
        self.a_lines((54, 40, 30), [(x + w * 0.07, y + h * 0.34), (x + w * 0.0, y + h * 0.28), (x + w * 0.04, y + h * 0.16), (x - w * 0.02, y + h * 0.08)], 2)
        self.a_ellipse(mid, x + w * 0.56, y + h * 0.18, w * 0.36, h * 0.52)
        self.a_poly(dark, [(x + w * 0.62, y + h * 0.22), (x + w * 0.66, y - h * 0.02), (x + w * 0.76, y + h * 0.22)])
        self.a_ellipse(snout, x + w * 0.80, y + h * 0.36, w * 0.20, h * 0.30)
        self.a_circle((40, 28, 22), x + w * 0.96, y + h * 0.46, 2)
        self.a_poly((244, 240, 224), [(x + w * 0.84, y + h * 0.62), (x + w * 0.94, y + h * 0.54), (x + w * 0.88, y + h * 0.78)])
        self.a_circle((20, 14, 10), x + w * 0.74, y + h * 0.34, 2)
        self.a_circle((200, 40, 30), x + w * 0.745, y + h * 0.335, 1)

    def a_boar_down(self, x, y, w, h, age):
        """A boar struck by an arrow, rolled onto its side."""
        dark, mid, snout = (92, 68, 48), (112, 84, 60), (156, 118, 96)
        for k in range(4):
            lx = x + w * (0.18 + k * 0.15)
            self.a_line((54, 40, 30), lx, y + h * 0.55, lx + 3 + (k % 2) * 4, y + h * 0.04, 4)
        self.a_ellipse(dark, x + w * 0.04, y + h * 0.36, w * 0.74, h * 0.58)
        self.a_ellipse(mid, x + w * 0.14, y + h * 0.42, w * 0.44, h * 0.24)
        self.a_ellipse(mid, x + w * 0.60, y + h * 0.46, w * 0.36, h * 0.46)
        self.a_ellipse(snout, x + w * 0.84, y + h * 0.58, w * 0.16, h * 0.26)
        self.a_poly((244, 240, 224), [(x + w * 0.86, y + h * 0.60), (x + w * 0.95, y + h * 0.50), (x + w * 0.9, y + h * 0.42)])
        self.a_line((20, 14, 10), x + w * 0.70, y + h * 0.56, x + w * 0.76, y + h * 0.66, 2)
        self.a_line((20, 14, 10), x + w * 0.76, y + h * 0.56, x + w * 0.70, y + h * 0.66, 2)
        # the arrow that brought it down
        self.a_line((214, 184, 124), x + w * 0.38, y + h * 0.48, x + w * 0.22, y - h * 0.34, 3)
        self.a_line((200, 50, 50), x + w * 0.22, y - h * 0.34, x + w * 0.18, y - h * 0.5, 3)
        for k in range(3):
            ang = age * 0.22 + k * 2.1
            self.a_circle((255, 220, 90), x + w * 0.8 + math.cos(ang) * 16, y + h * 0.1 + math.sin(ang) * 6, 3)

    def hunter_pose(self, target):
        """Where Odysseus' bow hand is, and which way he is aiming at `target`."""
        s = 2.7
        x, y = 105, 578
        sx, sy = x + 2, y - 26 * s
        ang = math.atan2(target[1] - sy, max(60, target[0] - sx))
        ang = max(-1.1, min(0.45, ang))
        dx, dy = math.cos(ang), math.sin(ang)
        return (sx + dx * 36, sy + dy * 36), (dx, dy), (sx, sy)

    def shoot_arrow(self, target):
        hand, (dx, dy), shoulder = self.hunter_pose(target)
        x0, y0 = hand[0] + dx * 30, hand[1] + dy * 30
        vx, vy = target[0] - x0, target[1] - y0
        d = math.hypot(vx, vy)
        if d < 1:
            return
        speed = 60.0
        self.arrows.append({"x": x0, "y": y0, "tx": target[0], "ty": target[1], "vx": vx / d * speed, "vy": vy / d * speed,
                            "state": 0, "life": 0, "hit": False})
        self.shot_age = 0

    def update_hunt_extras(self):
        for a in self.arrows:
            if a["state"] == 0:
                a["x"] += a["vx"]
                a["y"] += a["vy"]
                if (a["tx"] - a["x"]) * a["vx"] + (a["ty"] - a["y"]) * a["vy"] <= 0:
                    a["x"], a["y"] = a["tx"], a["ty"]
                    a["state"] = 1
                    a["life"] = 14 if a["hit"] else 50
            else:
                a["life"] -= 1
        self.arrows = [a for a in self.arrows if a["state"] == 0 or a["life"] > 0]
        self.shot_age += 1
        if self.fallen_boar:
            self.fallen_boar["age"] += 1
        if self.hunting_timer <= 0:
            self.arrows = []
            self.fallen_boar = None

    def draw_hunter(self):
        s = 2.7
        x, y = 105, 578
        hand, (dx, dy), (sx, sy) = self.hunter_pose(self.crosshair_pos)
        age = self.shot_age
        pull = 0 if age < 8 else min(24, (age - 8) * 2)
        skin = (236, 198, 158)
        # quiver on his back
        self.a_line((112, 74, 38), x - 6, y - 44, x - 20, y - 84, 10)
        for k in range(3):
            self.a_line((214, 184, 124), x - 20 + k * 3, y - 84, x - 24 + k * 4, y - 100, 2)
            self.a_poly((200, 50, 50), [(x - 24 + k * 4, y - 100), (x - 28 + k * 4, y - 108), (x - 20 + k * 4, y - 106)])
        self.a_odysseus(x, y, s, "king", "none")
        # the bow, held out toward the crosshair
        px, py = -dy, dx
        pts = []
        for k in range(-6, 7):
            u = k / 6.0
            pts.append((hand[0] + px * u * 42 - dx * 15 * u * u, hand[1] + py * u * 42 - dy * 15 * u * u))
        self.a_lines((124, 80, 38), pts, 6)
        self.a_circle(GOLD, hand[0], hand[1], 4)
        nock = (hand[0] - dx * (14 + pull), hand[1] - dy * (14 + pull))
        self.a_line((238, 232, 214), pts[0][0], pts[0][1], nock[0], nock[1], 2)
        self.a_line((238, 232, 214), nock[0], nock[1], pts[-1][0], pts[-1][1], 2)
        self.a_line(skin, sx, sy, hand[0], hand[1], 6)
        self.a_line(skin, sx, sy + 2, nock[0], nock[1], 6)
        if age >= 8:
            tip = (hand[0] + dx * 30, hand[1] + dy * 30)
            self.a_line((214, 184, 124), nock[0], nock[1], tip[0], tip[1], 3)
            self.a_poly((196, 196, 206), [(tip[0] + dx * 9, tip[1] + dy * 9), (tip[0] - dy * 4, tip[1] + dx * 4), (tip[0] + dy * 4, tip[1] - dx * 4)])
            self.a_line((200, 50, 50), nock[0], nock[1], nock[0] + dx * 9 + px * 4, nock[1] + dy * 9 + py * 4, 2)
            self.a_line((200, 50, 50), nock[0], nock[1], nock[0] + dx * 9 - px * 4, nock[1] + dy * 9 - py * 4, 2)

    def build_hunt_background(self):
        """Paint the forest once into cached surfaces (scenery behind and in front of the action)."""
        bg = pygame.Surface((WIDTH, HEIGHT))
        fg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        saved = (self.screen, self.shake_offset)
        rnd = random.Random(5)
        self.screen, self.shake_offset = bg, (0, 0)
        for i in range(14):
            self.a_rect(_mix((118, 178, 214), (214, 234, 206), i / 13.0), 0, i * 20, WIDTH, 22)
        self.a_glow(650, 70, 130, (255, 248, 200), 120)
        self.a_circle((255, 250, 214), 650, 70, 30)
        self.a_poly((112, 152, 142), [(0, 250), (0, 190), (120, 150), (260, 200), (380, 160), (520, 210), (660, 170), (800, 200), (800, 250)])
        self.a_poly((92, 136, 112), [(0, 272), (0, 232), (160, 198), (300, 240), (470, 206), (620, 244), (800, 214), (800, 272)])
        for i in range(16):
            self.a_rect(_mix((100, 150, 74), (40, 84, 42), i / 15.0), 0, 250 + i * 22, WIDTH, 24)
        for i in range(15):
            tx = 14 + i * 56 + rnd.randint(-14, 14)
            h = rnd.randint(120, 170)
            base = 268 + rnd.randint(-6, 10)
            self.a_rect((54, 40, 28), tx - 6, base - h, 12, h)
            self.a_circle((30, 78, 48), tx, base - h - 6, rnd.randint(38, 52))
            self.a_circle((44, 100, 60), tx - 14, base - h - 18, 26)
        # the game trail the boars follow
        self.a_poly((160, 128, 86), [(0, 436), (0, 392), (200, 374), (420, 382), (640, 370), (800, 382), (800, 444), (620, 460), (400, 452), (180, 460)])
        self.a_lines((138, 106, 68), [(0, 440), (180, 462), (400, 454), (620, 462), (800, 446)], 3)
        self.a_lines((176, 146, 100), [(0, 394), (200, 376), (420, 384), (640, 372), (800, 384)], 2)
        for k in range(140):
            gx, gy = rnd.randint(0, 800), rnd.randint(282, 592)
            if 372 < gy < 452:
                continue
            self.a_line(_mix((70, 130, 56), (130, 190, 90), rnd.random()), gx, gy, gx + rnd.randint(-3, 3), gy - rnd.randint(5, 12), 2)
        for k in range(50):
            fx, fy = rnd.randint(0, 800), rnd.randint(290, 595)
            if 372 < fy < 452:
                continue
            self.a_circle(rnd.choice([(255, 240, 120), (255, 255, 255), (240, 150, 200)]), fx, fy, 2)
        for bx, by, br in ((60, 300, 30), (230, 296, 24), (420, 300, 28), (590, 298, 26), (700, 304, 30)):
            self.a_circle((36, 92, 52), bx, by, br)
            self.a_circle((52, 116, 66), bx - 8, by - 8, br * 0.6)
        self.a_ellipse((120, 118, 124), 300, 340, 56, 30)
        self.a_ellipse((148, 146, 152), 306, 340, 40, 18)
        self.a_rect((92, 66, 40), 470, 332, 110, 22)
        self.a_ellipse((116, 84, 50), 466, 332, 16, 22)
        self.a_beam([(420, 90), (500, 90), (360, 500), (240, 500)], (255, 244, 180), 34)
        self.a_beam([(560, 90), (620, 90), (560, 500), (470, 500)], (255, 244, 180), 28)
        # foreground: a great trunk on the right, ferns along the bottom
        self.screen = fg
        self.a_poly((62, 44, 30), [(746, 600), (754, 0), (800, 0), (800, 600)])
        for k in range(9):
            self.a_line((44, 30, 20), 760 + (k % 3) * 12, 20 + k * 64, 764 + (k % 3) * 12, 70 + k * 64, 3)
        for cx, cy, r in ((780, 30, 60), (730, 60, 44), (790, 100, 40), (700, 24, 38)):
            self.a_circle((28, 76, 44), cx, cy, r)
            self.a_circle((44, 100, 60), cx - 10, cy - 8, r * 0.5)
        for fx in (10, 190, 330, 500, 640, 720):
            for k in range(7):
                ang = -math.pi / 2 + (k - 3) * 0.42
                self.a_line((44 + k * 4, 112 + k * 5, 60), fx, 604, fx + math.cos(ang) * 46, 604 + math.sin(ang) * 46, 4)
        self.screen, self.shake_offset = saved
        self._hunt_bg, self._hunt_fg = bg, fg

    def draw_hunting(self):
        ox, oy = self.shake_offset
        tk = pygame.time.get_ticks() // 16
        if self._hunt_bg is None:
            self.build_hunt_background()
        self.screen.blit(self._hunt_bg, (ox, oy))
        # butterflies drifting through the sunbeams
        for k in range(3):
            bx = 150 + k * 220 + math.sin(tk * 0.03 + k * 2) * 60
            by = 300 + math.cos(tk * 0.05 + k) * 30
            wing = abs(math.sin(tk * 0.4 + k)) * 5 + 1
            self.a_ellipse((250, 190, 70), bx - wing * 2, by - 3, wing * 2, 6)
            self.a_ellipse((250, 190, 70), bx, by - 3, wing * 2, 6)
        if self.animal:
            self.a_boar(self.animal.x, self.animal.y, self.animal.width, self.animal.height, tk)
        if self.fallen_boar:
            fb = self.fallen_boar
            self.a_boar_down(fb["x"], fb["y"], fb["w"], fb["h"], fb["age"])
        self.draw_hunter()
        for a in self.arrows:
            n = math.hypot(a["vx"], a["vy"]) or 1.0
            dx, dy = a["vx"] / n, a["vy"] / n
            tail = (a["x"] - dx * 38, a["y"] - dy * 38)
            self.a_line((214, 184, 124), tail[0], tail[1], a["x"], a["y"], 3)
            self.a_poly((196, 196, 206), [(a["x"] + dx * 9, a["y"] + dy * 9), (a["x"] - dy * 4, a["y"] + dx * 4), (a["x"] + dy * 4, a["y"] - dx * 4)])
            self.a_line((200, 50, 50), tail[0], tail[1], tail[0] + dx * 10 - dy * 5, tail[1] + dy * 10 + dx * 5, 2)
            self.a_line((200, 50, 50), tail[0], tail[1], tail[0] + dx * 10 + dy * 5, tail[1] + dy * 10 - dx * 5, 2)
            if a["state"] == 1 and not a["hit"] and a["life"] > 38:
                self.a_circle((180, 150, 100), a["x"], a["y"], 4 + (50 - a["life"]), 2)
        self.screen.blit(self._hunt_fg, (ox, oy))
        # HUD
        self.a_title(f"HUNTING - TIME: {self.hunting_timer // 60}s", CRT_GREEN, 22)
        self.draw_text("Click on game to shoot!", self.font, BLACK, WIDTH // 2 + ox + 2, 72 + oy, center=True)
        self.draw_text("Click on game to shoot!", self.font, WHITE, WIDTH // 2 + ox, 70 + oy, center=True)
        cx, cy = self.crosshair_pos
        pulse = int(math.sin(tk * 0.15) * 2)
        for col, wd, rr in ((BLACK, 4, 14 + pulse), (RED, 2, 14 + pulse), (BLACK, 3, 6), (RED, 1, 6)):
            pygame.draw.circle(self.screen, col, (cx + ox, cy + oy), rr, wd)
        for ddx, ddy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            pygame.draw.line(self.screen, BLACK, (cx + ddx * 9 + ox, cy + ddy * 9 + oy), (cx + ddx * 22 + ox, cy + ddy * 22 + oy), 4)
            pygame.draw.line(self.screen, RED, (cx + ddx * 9 + ox, cy + ddy * 9 + oy), (cx + ddx * 22 + ox, cy + ddy * 22 + oy), 2)

    def draw_phaeacian_ship(self, x, y, t, ox, oy, with_cargo=True):
        """Phaeacian ship with rowing oars. (x, y) is the top-left of the deck line."""
        for i in range(5):
            px = x + 30 + i * 22
            swing = int(math.sin(t * 0.12 + i * 0.5) * 10)
            pygame.draw.line(self.screen, (120, 80, 40), (px + ox, y + 14 + oy), (px - 14 + swing + ox, y + 52 + oy), 3)
        pygame.draw.polygon(self.screen, BROWN, [(x + ox, y + oy), (x + 150 + ox, y + oy), (x + 130 + ox, y + 28 + oy), (x + 25 + ox, y + 28 + oy)])
        pygame.draw.polygon(self.screen, BROWN, [(x + 150 + ox, y + oy), (x + 172 + ox, y - 16 + oy), (x + 150 + ox, y + 12 + oy)])
        pygame.draw.line(self.screen, GOLD, (x + 6 + ox, y + 6 + oy), (x + 144 + ox, y + 6 + oy), 2)
        for i in range(5):
            px = x + 30 + i * 22
            pygame.draw.circle(self.screen, WHITE, (px + ox, y - 14 + oy), 5)
            pygame.draw.rect(self.screen, PURPLE, (px - 4 + ox, y - 9 + oy, 8, 9))
        if with_cargo:
            # Sleeping Odysseus under a red cloak
            pygame.draw.circle(self.screen, WHITE, (x + 120 + ox, y - 6 + oy), 5)
            pygame.draw.rect(self.screen, RED, (x + 124 + ox, y - 11 + oy, 22, 11))
            # Treasure chests
            pygame.draw.rect(self.screen, GOLD, (x + 10 + ox, y - 12 + oy, 14, 12))
            pygame.draw.rect(self.screen, ORANGE, (x + 10 + ox, y - 12 + oy, 14, 12), 1)
            pygame.draw.rect(self.screen, GOLD, (x + 6 + ox, y - 5 + oy, 10, 5))

    def draw(self):
        self.screen.fill(BLACK)
        ox, oy = self.shake_offset
        
        if self.state == "INTRO":
            visible_text = self.intro_text[:self.intro_char_index]
            self.draw_wrapped_text(visible_text, self.font, WHITE, 50 + ox, HEIGHT//3 + oy, WIDTH - 100)
            
            if self.intro_char_index >= len(self.intro_text):
                self.draw_text("Press SPACE to proceed", self.font, CRT_GREEN, WIDTH//2 + ox, HEIGHT - 100 + oy, center=True)
            else:
                self.draw_text("[ SPACE / Click to skip ]", self.small_font, CRT_GREEN, WIDTH//2 + ox, HEIGHT - 50 + oy, center=True)

        elif self.state == "TITLE":
            self.draw_troy()

            self.draw_text("THE ITHACA TRAIL", self.title_font, WHITE, WIDTH//2 + ox, 80 + oy, center=True)
            self.draw_text("The Fall of Troy and the Long Way Home", self.font, CRT_GREEN, WIDTH//2 + ox, 130 + oy, center=True)

            pygame.draw.rect(self.screen, CYAN, self.set_sail_button)
            pygame.draw.rect(self.screen, WHITE, self.set_sail_button, 3)
            self.draw_text("SET SAIL", self.font, BLACK, WIDTH//2 + ox, HEIGHT - 92 + oy, center=True)

        elif self.state == "MENU":
            current_loc = self.locations[self.location_index]
            
            pygame.draw.rect(self.screen, WHITE, (ox, oy, WIDTH, 50))
            self.draw_title_fit(f"The Ithaca Trail - {current_loc['name']}", BLACK, 20 + ox, 10 + oy)
            
            pygame.draw.rect(self.screen, WHITE, (20 + ox, 70 + oy, WIDTH-40, HEIGHT-90), 3)
            
            self.draw_text("CAPTAIN'S LOG", self.font, CRT_GREEN, 50 + ox, 100 + oy)
            self.draw_text("-----------------", self.font, WHITE, 50 + ox, 120 + oy)
            self.draw_text(f"Ships:         {self.ships}", self.font, WHITE, 50 + ox, 150 + oy)
            self.draw_text(f"Crew:          {self.crew} men", self.font, WHITE, 50 + ox, 180 + oy)
            self.draw_text(f"Food:          {self.food} lbs", self.font, WHITE, 50 + ox, 210 + oy)
            self.draw_text(f"Rations:       {self.rations}", self.font, WHITE, 50 + ox, 240 + oy)
            
            if self.message:
                pygame.draw.rect(self.screen, BLACK, (50 + ox, 290 + oy, WIDTH-100, 100))
                self.draw_text(self.message, self.font, CRT_GREEN, 50 + ox, 300 + oy)
            
            self.draw_text("You may:", self.font, WHITE, 50 + ox, 400 + oy)
            self.draw_text("  1. Continue on course", self.font, WHITE, 50 + ox, 430 + oy)
            self.draw_text("  2. Check map", self.font, WHITE, 50 + ox, 460 + oy)
            self.draw_text("  3. Change rations", self.font, WHITE, 50 + ox, 490 + oy)
            
            if current_loc["can_hunt"] and not self.hunted_here:
                self.draw_text("  4. Hunt for food", self.font, CRT_GREEN, 50 + ox, 520 + oy)
            else:
                self.draw_text("  4. Hunt for food (N/A)", self.font, (100, 100, 100), 50 + ox, 520 + oy)
                
            self.draw_text("What is your choice? ", self.font, WHITE, 50 + ox, 560 + oy)
                   
        elif self.state == "MAP":
            self.draw_map()

        elif self.state == "RATIONS":
            pygame.draw.rect(self.screen, WHITE, (100 + ox, 150 + oy, WIDTH-200, 300), 3)
            self.draw_text("CHANGE RATIONS", self.title_font, WHITE, WIDTH//2 + ox, 180 + oy, center=True)
            self.draw_text("1. Filling    (3 lbs per man)", self.font, CRT_GREEN if self.rations == "Filling" else WHITE, 150 + ox, 290 + oy)
            self.draw_text("2. Meager     (2 lbs per man)", self.font, CRT_GREEN if self.rations == "Meager" else WHITE, 150 + ox, 330 + oy)
            self.draw_text("3. Bare Bones (1 lb per man)", self.font, CRT_GREEN if self.rations == "Bare Bones" else WHITE, 150 + ox, 370 + oy)

        elif self.state == "SAILING":
            self.draw_sailing_sky()
            self.draw_text("SAILING ON THE OPEN SEA...", self.title_font, WHITE, WIDTH//2 + ox, 80 + oy, center=True)
            time_ticks = pygame.time.get_ticks() / 200.0
            for x in range(0, WIDTH, 40):
                wave_y = 420 + int(math.sin((x / 100.0) + time_ticks) * 20)
                pygame.draw.rect(self.screen, self.sail_wave_col, (x + ox, wave_y + oy, 40, HEIGHT - wave_y))
                pygame.draw.rect(self.screen, self.sail_foam_col, (x + ox, wave_y + oy, 40, 5)) 
            active_ships = max(1, self.ships)
            spacing = 700 // active_ships
            for i in range(self.ships):
                ship_x = 50 + (i * spacing)
                ship_y = 400 + int(math.sin(((ship_x + 50) / 100.0) + time_ticks) * 15)
                pygame.draw.rect(self.screen, BROWN, (ship_x + ox, ship_y + oy, 35, 14)) 
                pygame.draw.rect(self.screen, WHITE, (ship_x + 10 + ox, ship_y - 25 + oy, 15, 25)) 
                pygame.draw.rect(self.screen, BLACK, (ship_x + 17 + ox, ship_y - 28 + oy, 2, 32)) 

        elif self.state == "ANIMATION":
            pygame.draw.rect(self.screen, WHITE, (50 + ox, 80 + oy, WIDTH-100, HEIGHT-160), 3)
            
            anim_method = getattr(self, "anim_" + self.anim_type, None)
            if anim_method is not None:
                anim_method()
            elif self.anim_type == "odysseus_crying":
                t = 420 - self.anim_timer
                ticks = pygame.time.get_ticks() / 300.0
                pygame.draw.rect(self.screen, DARK_BLUE, (53 + ox, 83 + oy, WIDTH - 106, 320))
                for sx, sy in [(120, 200), (200, 240), (300, 190), (420, 230), (520, 200), (600, 250), (690, 215), (350, 260), (470, 190)]:
                    pygame.draw.rect(self.screen, WHITE, (sx + ox, sy + oy, 2, 2))
                pygame.draw.circle(self.screen, (230, 230, 200), (640 + ox, 215 + oy), 26)
                for x in range(53, 747, 30):
                    wave_y = 400 + int(math.sin((x / 60.0) + ticks) * 6)
                    pygame.draw.rect(self.screen, BLUE, (x + ox, wave_y + oy, min(30, 747 - x), 516 - wave_y))
                    pygame.draw.rect(self.screen, WHITE, (x + ox, wave_y + oy, min(30, 747 - x), 3))
                shore = [(53, 516), (53, 375), (150, 360), (200, 385), (330, 385), (380, 430), (480, 516)]
                shore_pts = [(px + ox, py + oy) for px, py in shore]
                pygame.draw.polygon(self.screen, (85, 85, 85), shore_pts)
                pygame.draw.polygon(self.screen, (130, 130, 130), shore_pts, 3)
                pygame.draw.ellipse(self.screen, (110, 110, 110), (90 + ox, 420 + oy, 90, 50))
                pygame.draw.ellipse(self.screen, (70, 70, 70), (240 + ox, 420 + oy, 70, 40))
                pygame.draw.ellipse(self.screen, (100, 100, 100), (330 + ox, 445 + oy, 60, 35))
                # Odysseus, seated and sobbing
                sob = int(math.sin(t * 0.25) * 2)
                pygame.draw.rect(self.screen, WHITE, (238 + ox, 377 + oy, 22, 8))
                pygame.draw.rect(self.screen, RED, (220 + ox, 361 + sob + oy, 18, 24))
                pygame.draw.circle(self.screen, WHITE, (229 + ox, 353 + sob + oy), 8)
                pygame.draw.line(self.screen, WHITE, (221 + ox, 366 + sob + oy), (225 + ox, 355 + sob + oy), 3)
                pygame.draw.line(self.screen, WHITE, (237 + ox, 366 + sob + oy), (233 + ox, 355 + sob + oy), 3)
                for i in range(4):
                    ty = 361 + ((t * 2 + i * 15) % 24)
                    pygame.draw.circle(self.screen, CYAN, (223 + i * 4 + ox, ty + oy), 2)
                self.draw_text("ALONE ON OGYGIA'S SHORE...", self.title_font, WHITE, WIDTH//2 + ox, 100 + oy, center=True)
                self.draw_text("Far from home, Odysseus weeps for Ithaca.", self.font, CRT_GREEN, WIDTH//2 + ox, 150 + oy, center=True)

            elif self.anim_type == "raft_building":
                t = 540 - self.anim_timer
                p = t / 540.0
                ticks = pygame.time.get_ticks() / 300.0
                pygame.draw.rect(self.screen, (40, 90, 160), (53 + ox, 83 + oy, WIDTH - 106, 247))
                pygame.draw.circle(self.screen, GOLD, (690 + ox, 210 + oy), 26)
                for x in range(53, 747, 30):
                    wave_y = 330 + int(math.sin((x / 60.0) + ticks) * 4)
                    pygame.draw.rect(self.screen, BLUE, (x + ox, wave_y + oy, min(30, 747 - x), 55))
                pygame.draw.rect(self.screen, (194, 170, 110), (53 + ox, 380 + oy, WIDTH - 106, 137))
                # Trees disappear as they are felled
                if p < 0.4:
                    pygame.draw.rect(self.screen, BROWN, (90 + ox, 290 + oy, 14, 100))
                    pygame.draw.circle(self.screen, GREEN, (97 + ox, 280 + oy), 35)
                if p < 0.7:
                    pygame.draw.rect(self.screen, BROWN, (160 + ox, 310 + oy, 12, 80))
                    pygame.draw.circle(self.screen, GREEN, (166 + ox, 300 + oy), 28)
                # The raft grows log by log
                n = min(6, 1 + int(p * 7))
                for k in range(n):
                    pygame.draw.rect(self.screen, BROWN, (330 + ox, 400 + k * 14 + oy, 170, 12))
                    pygame.draw.rect(self.screen, (100, 50, 10), (330 + ox, 400 + k * 14 + oy, 170, 12), 1)
                if p > 0.85:
                    pygame.draw.rect(self.screen, BROWN, (410 + ox, 335 + oy, 6, 140))
                    pygame.draw.rect(self.screen, WHITE, (416 + ox, 345 + oy, 55, 40))
                # Odysseus swinging the axe
                pygame.draw.rect(self.screen, RED, (262 + ox, 420 + oy, 14, 30))
                pygame.draw.circle(self.screen, WHITE, (269 + ox, 412 + oy), 8)
                pygame.draw.line(self.screen, WHITE, (266 + ox, 450 + oy), (264 + ox, 470 + oy), 3)
                pygame.draw.line(self.screen, WHITE, (272 + ox, 450 + oy), (276 + ox, 470 + oy), 3)
                a = math.sin(t * 0.25) * 0.8 - 0.3
                ax = 276 + int(math.cos(a) * 30)
                ay = 426 - int(math.sin(a) * 30)
                pygame.draw.line(self.screen, BROWN, (276 + ox, 426 + oy), (ax + ox, ay + oy), 4)
                pygame.draw.circle(self.screen, (200, 200, 200), (ax + ox, ay + oy), 6)
                for i in range(4):
                    cx = 295 + ((t * 2 + i * 17) % 30)
                    cy = 455 - ((t * 2 + i * 23) % 35)
                    pygame.draw.rect(self.screen, BROWN, (cx + ox, cy + oy, 4, 3))
                self.draw_text("ODYSSEUS BUILDS A RAFT!", self.title_font, GOLD, WIDTH//2 + ox, 100 + oy, center=True)
                self.draw_text("With Calypso's bronze axe he fells trees and lashes the logs.", self.font, WHITE, WIDTH//2 + ox, 150 + oy, center=True)

            elif self.anim_type == "drifting_phaeacia":
                t = 660 - self.anim_timer
                p = t / 660.0
                ticks = pygame.time.get_ticks() / 150.0
                storm = 0.70 <= p < 0.85
                arrive = p >= 0.85
                self.screen.set_clip(pygame.Rect(53 + ox, 83 + oy, WIDTH - 106, 434))
                if storm:
                    sky_color = (20, 20, 30)
                elif arrive:
                    sky_color = (60, 100, 160)
                else:
                    sky_color = DARK_BLUE
                pygame.draw.rect(self.screen, sky_color, (53 + ox, 83 + oy, WIDTH - 106, 434))
                if not storm and not arrive:
                    for sx, sy in [(120, 200), (200, 240), (300, 190), (420, 230), (520, 200), (600, 250), (690, 215), (350, 260), (470, 190)]:
                        pygame.draw.rect(self.screen, WHITE, (sx + ox, sy + oy, 2, 2))
                if arrive:
                    k = min(1.0, (p - 0.85) / 0.12)
                    shift = int((1.0 - k) * 320)
                    land = [(520, 420), (570, 340), (640, 310), (700, 330), (780, 350), (780, 420)]
                    pygame.draw.polygon(self.screen, (40, 120, 50), [(lx + shift + ox, ly + oy) for lx, ly in land])
                    pygame.draw.rect(self.screen, (194, 170, 110), (520 + shift + ox, 400 + oy, 260, 30))
                    self.draw_text("SCHERIA", self.small_font, WHITE, 610 + shift + ox, 285 + oy)
                amp = 30 if storm else 15
                for x in range(53, 747, 30):
                    wave_y = 400 + int(math.sin((x / 60.0) + ticks) * amp)
                    w = min(30, 747 - x)
                    pygame.draw.rect(self.screen, BLUE, (x + ox, wave_y + oy, w, 516 - wave_y))
                    pygame.draw.rect(self.screen, WHITE, (x + ox, wave_y + oy, w, 4))
                raft_x = int(100 + p * 360)
                bob = int(math.sin(ticks * 1.3) * (amp // 2))
                raft_y = 385 + bob
                pygame.draw.rect(self.screen, BROWN, (raft_x + ox, raft_y + oy, 60, 12))
                pygame.draw.rect(self.screen, BROWN, (raft_x + 28 + ox, raft_y - 32 + oy, 4, 32))
                pygame.draw.rect(self.screen, WHITE, (raft_x + 32 + ox, raft_y - 30 + oy, 20, 18))
                pygame.draw.circle(self.screen, WHITE, (raft_x + 14 + ox, raft_y - 9 + oy), 6)
                pygame.draw.line(self.screen, WHITE, (raft_x + 14 + ox, raft_y - 3 + oy), (raft_x + 14 + ox, raft_y + oy), 3)
                if storm:
                    for _ in range(30):
                        rain_x = random.randint(53, 747) + ox
                        rain_y = random.randint(150, 420) + oy
                        pygame.draw.line(self.screen, CYAN, (rain_x, rain_y), (rain_x - 6, rain_y + 14), 1)
                    if (self.anim_timer // 6) % 3 == 0:
                        pygame.draw.polygon(self.screen, YELLOW, [(520 + ox, 90 + oy), (500 + ox, 220 + oy), (530 + ox, 220 + oy), (510 + ox, 370 + oy), (545 + ox, 240 + oy), (515 + ox, 240 + oy)])
                    self.draw_text("POSEIDON'S STORM!", self.title_font, RED, WIDTH//2 + ox, 100 + oy, center=True)
                    self.draw_text("The sea god shatters the sky and the waves rise!", self.font, WHITE, WIDTH//2 + ox, 150 + oy, center=True)
                elif arrive:
                    self.draw_text("THE LAND OF THE PHAEACIANS!", self.title_font, GOLD, WIDTH//2 + ox, 100 + oy, center=True)
                    self.draw_text("Athena calms the waves. Land at last!", self.font, WHITE, WIDTH//2 + ox, 150 + oy, center=True)
                else:
                    day = min(17, 1 + int(p / 0.7 * 17))
                    self.draw_text("ADRIFT ON THE OPEN SEA...", self.title_font, WHITE, WIDTH//2 + ox, 100 + oy, center=True)
                    self.draw_text(f"Day {day} on the raft, steering by the stars.", self.font, CRT_GREEN, WIDTH//2 + ox, 150 + oy, center=True)
                self.screen.set_clip(None)

            elif self.anim_type == "phaeacian_voyage":
                t = 480 - self.anim_timer
                p = t / 480.0
                ticks = pygame.time.get_ticks() / 200.0
                self.screen.set_clip(pygame.Rect(53 + ox, 83 + oy, WIDTH - 106, 434))
                pygame.draw.rect(self.screen, (8, 8, 28), (53 + ox, 83 + oy, WIDTH - 106, 434))
                for sx, sy in [(90, 210), (170, 250), (260, 200), (380, 240), (470, 205), (560, 255), (650, 215), (720, 245), (330, 280), (610, 290)]:
                    if (t // 20 + sx) % 7 != 0:
                        pygame.draw.rect(self.screen, WHITE, (sx + ox, sy + oy, 2, 2))
                pygame.draw.circle(self.screen, (230, 230, 200), (640 + ox, 215 + oy), 28)
                pygame.draw.circle(self.screen, (8, 8, 28), (652 + ox, 209 + oy), 24)
                for x in range(53, 747, 30):
                    wave_y = 400 + int(math.sin((x / 60.0) + ticks) * 8)
                    w = min(30, 747 - x)
                    pygame.draw.rect(self.screen, DARK_BLUE, (x + ox, wave_y + oy, w, 517 - wave_y))
                    pygame.draw.rect(self.screen, (60, 80, 140), (x + ox, wave_y + oy, w, 3))
                ship_x = int(70 + p * 380)
                ship_y = 360 + int(math.sin(ticks * 1.2) * 5)
                self.draw_phaeacian_ship(ship_x, ship_y, t, ox, oy)
                self.draw_text("zZz", self.small_font, CYAN, ship_x + 120 + ox, ship_y - 36 + oy - int((t // 4) % 12))
                self.screen.set_clip(None)
                self.draw_text("THE PHAEACIANS CARRY HIM HOME", self.title_font, GOLD, WIDTH//2 + ox, 100 + oy, center=True)
                if getattr(self, "told_story", False):
                    self.draw_text("Lulled by his own tale, Odysseus sleeps as the ship flies on.", self.font, WHITE, WIDTH//2 + ox, 150 + oy, center=True)
                else:
                    self.draw_text("Worn out from his trials, Odysseus sleeps as the ship flies on.", self.font, WHITE, WIDTH//2 + ox, 150 + oy, center=True)

            elif self.anim_type == "phaeacian_landing":
                t = 480 - self.anim_timer
                p = t / 480.0
                ticks = pygame.time.get_ticks() / 250.0
                self.screen.set_clip(pygame.Rect(53 + ox, 83 + oy, WIDTH - 106, 434))
                night, dawn = (8, 8, 28), (255, 170, 110)
                sky = tuple(int(night[i] + (dawn[i] - night[i]) * p) for i in range(3))
                pygame.draw.rect(self.screen, sky, (53 + ox, 83 + oy, WIDTH - 106, 434))
                pygame.draw.circle(self.screen, GOLD, (650 + ox, int(350 - p * 90) + oy), 26)
                pygame.draw.polygon(self.screen, (30, 90, 45), [(380 + ox, 345 + oy), (480 + ox, 280 + oy), (560 + ox, 320 + oy), (640 + ox, 270 + oy), (747 + ox, 330 + oy), (747 + ox, 360 + oy), (380 + ox, 360 + oy)])
                for x in range(53, 747, 30):
                    wave_y = 355 + int(math.sin((x / 60.0) + ticks) * 4)
                    pygame.draw.rect(self.screen, BLUE, (x + ox, wave_y + oy, min(30, 747 - x), 517 - wave_y))
                    pygame.draw.rect(self.screen, WHITE, (x + ox, wave_y + oy, min(30, 747 - x), 3))
                pygame.draw.polygon(self.screen, (194, 170, 110), [(300 + ox, 517 + oy), (360 + ox, 395 + oy), (747 + ox, 365 + oy), (747 + ox, 517 + oy)])
                # Ship waits at the shore, then sails away
                if p < 0.6:
                    ship_x = 130
                else:
                    ship_x = int(130 - ((p - 0.6) / 0.4) * 320)
                self.draw_phaeacian_ship(ship_x, 345, t, ox, oy, with_cargo=False)
                # Treasures carried ashore one at a time
                spots = [(470, 450), (500, 468), (530, 452), (560, 470)]
                for i, (sx, sy) in enumerate(spots):
                    start = i * 0.15
                    k = (p - start) / 0.10
                    if k >= 1.0:
                        pygame.draw.rect(self.screen, GOLD, (sx + ox, sy + oy, 18, 14))
                        pygame.draw.rect(self.screen, ORANGE, (sx + ox, sy + oy, 18, 14), 1)
                    elif k > 0:
                        cx = int(280 + (sx - 280) * k)
                        cy = int(400 + (sy - 400) * k)
                        step = int(math.sin(t * 0.3) * 4)
                        pygame.draw.circle(self.screen, WHITE, (cx + ox, cy - 14 + oy), 5)
                        pygame.draw.rect(self.screen, PURPLE, (cx - 4 + ox, cy - 9 + oy, 8, 14))
                        pygame.draw.line(self.screen, WHITE, (cx + ox, cy + 5 + oy), (cx - step + ox, cy + 16 + oy), 2)
                        pygame.draw.line(self.screen, WHITE, (cx + ox, cy + 5 + oy), (cx + step + ox, cy + 16 + oy), 2)
                        pygame.draw.rect(self.screen, GOLD, (cx - 8 + ox, cy - 26 + oy, 16, 11))
                # Odysseus sleeping on the sand
                pygame.draw.circle(self.screen, WHITE, (610 + ox, 470 + oy), 7)
                pygame.draw.rect(self.screen, RED, (617 + ox, 463 + oy, 44, 14))
                self.draw_text("zZz", self.small_font, CYAN, 615 + ox, 440 + oy - int((t // 5) % 12))
                self.screen.set_clip(None)
                self.draw_text("LEFT ASLEEP ON ITHACA'S SHORE", self.title_font, GOLD, WIDTH//2 + ox, 100 + oy, center=True)
                self.draw_text("His treasures are laid beside him before he wakes.", self.font, WHITE, WIDTH//2 + ox, 150 + oy, center=True)

        elif self.state == "ENCOUNTER":
            current_loc = self.locations[self.location_index]
            pygame.draw.rect(self.screen, WHITE, (20 + ox, 20 + oy, WIDTH - 40, HEIGHT - 40), 3)
            # Hide the Thrinacia header during the second Charybdis encounter
            if not (current_loc["id"] == "helios" and self.encounter_step >= 1):
                self.draw_title_fit(f"ENCOUNTER: {current_loc['name'].upper()}", CRT_GREEN, WIDTH//2 + ox, 50 + oy, center=True)

            if current_loc["id"] == "cyclops":
                if self.encounter_step == 0:
                    text = "You are trapped in a cave with Polyphemus!|1. Negotiate with him.|2. Offer him strong unmixed wine."
                elif self.encounter_step == 1:
                    text = "He refuses your terms.|1. Offer wine now."
                elif self.encounter_step == 2:
                    text = "The giant passes out drunk!|1. Drive a sharpened olive stake into his eye!"
                elif self.encounter_step == 3:
                    text = "He is blind and raging at the exit!|1. Try to rush past him.|2. Cling to the underside of his rams."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "laestrygonians":
                if self.encounter_step == 0:
                    text = current_loc["text"]
                elif self.encounter_step == 1:
                    text = "The giant inhabitants attack!|1. Attempt to fight back.|2. Order immediate retreat."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "circe":
                if self.encounter_step == 0:
                    text = current_loc["text"]
                elif self.encounter_step == 5:
                    text = "Having hunted food, you explore further.|1. Investigate Circe's hall."
                elif self.encounter_step == 1:
                    text = "Circe turned your scouts into swine! Hermes appears.|1. Accept the magic herb (Moly)."
                elif self.encounter_step == 2:
                    text = "With Moly, you resist her magic.|1. Demand she restore your crew.|2. Strike a deal."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "hades":
                if self.encounter_step == 0:
                    text = current_loc["text"]
                elif self.encounter_step == 1:
                    text = "The spirits crowd around the sacrificial blood!|1. Speak with Tiresias and the dead."
                elif self.encounter_step == 10:
                    text = "Tiresias warns: Do not touch the Cattle of Helios!|[Press SPACE to continue]"
                elif self.encounter_step == 11:
                    text = "Your mother's spirit appears with tragic news from home.|[Press SPACE to continue]"
                elif self.encounter_step == 12:
                    text = "Agamemnon and Achilles advise you on honor and caution.|[Press SPACE to continue]"
                elif self.encounter_step == 13:
                    text = "Elpenor begs for a proper burial back on Circe's island.|[Press SPACE to continue]"
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "circe_return":
                if self.encounter_step == 0:
                    text = "You return to Aeaea to fulfill Elpenor's request.|1. Erect the oar and perform burial rites."
                elif self.encounter_step == 1:
                    text = "Circe warns you of upcoming dangers:| |1. Sirens: Plug ears with wax or bind yourself to the mast.|2. Scylla & Charybdis: Choose Scylla over the whirlpool.|3. Helios' Cattle: DO NOT eat them under any circumstances!"
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "scylla":
                if self.encounter_step == 0:
                    text = "You reach the narrow strait!|1. Sail past Charybdis (Whirlpool).|2. Sail past Scylla (Six-headed Monster)."
                elif self.encounter_step == 1:
                    text = "Remember Circe's warning!|Charybdis will swallow the whole ship! You must choose Scylla.| |2. Sail past Scylla (Six-headed Monster)."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "helios":
                if self.encounter_step == 0:
                    text = "Unfavorable winds trap you here and food runs out!|1. Allow the men to eat the sacred cattle.|2. Make the men starve."
                elif self.encounter_step == 1:
                    text = "Charybdis is pulling down your raft!|1. Get sucked in.|2. Jump up and grab onto the fig tree."
                elif self.encounter_step == 2:
                    text = "Are you sure?| |2. Jump up and grab onto the fig tree."
                elif self.encounter_step == 3:
                    text = "You are hanging over the churning abyss!|1. Jump into the whirlpool.|2. Keep hanging."
                elif self.encounter_step == 4:
                    text = "Are you sure?| |2. Keep hanging."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "cicones":
                if self.encounter_step == 0:
                    text = current_loc["text"]
                elif self.encounter_step == 1:
                    text = "The crew insists to stay the night.| |1. Stay the night, slaughter sheep & drink."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "ithaca":
                if self.encounter_step == 0:
                    text = "Athena has disguised you as an old beggar. Strangers fill your halls, and no one knows you.|1. Go straight to Penelope.|2. Go to the loyal swineherd Eumaeus."
                elif self.encounter_step == 1:
                    text = "Remember what Agamemnon said.| |2. Go to the loyal swineherd Eumaeus."
                elif self.encounter_step == 2:
                    text = "Eumaeus shares his supper and listens to your tale, though he does not believe that Odysseus lives.|1. Stay with Eumaeus.|2. Go straight to take on the suitors."
                elif self.encounter_step == 3:
                    text = "Remember what Agamemnon said.| |1. Stay with Eumaeus."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "phaeacia":
                text = "King Alcinous and Queen Arete welcome you and offer gold, bronze tripods, and fine robes, and they promise a swift ship to carry you home.|1. Accept the gracious gifts but leave quickly.|2. Accept the gracious gifts and tell your story, then leave."
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            elif current_loc["id"] == "ogygia":
                if self.encounter_step == 0:
                    text = "Seven long years you have lived on Calypso's island, weeping each day for home.|Zeus sends Hermes with a command: let Odysseus go.|[Press SPACE to continue]"
                elif self.encounter_step == 1:
                    text = "Calypso: 'Son of Laertes, I will hold you no longer.|You must build a raft to cross the sea. Take this bronze axe, bread, and wine, and I will send you a fair wind.'|[Press SPACE to continue]"
                self.draw_text(text, self.font, WHITE, 50 + ox, 150 + oy)

            else:
                self.draw_text(current_loc["text"], self.font, WHITE, 50 + ox, 150 + oy)

        elif self.state == "HUNTING":
            self.draw_hunting()

        elif self.state == "BATTLE":
            self.draw_battle()

        elif self.state == "STRING_GAME":
            self.draw_string_game()

        elif self.state == "TIMING_GAME":
            self.draw_timing_game()

        elif self.state == "GAME_OVER":
            self.draw_text("YOUR JOURNEY ENDS HERE", self.title_font, RED, WIDTH//2 + ox, HEIGHT//3 + oy, center=True)
            self.draw_text("All ships and crew have perished.", self.font, WHITE, WIDTH//2 + ox, HEIGHT//2 + oy, center=True)
            self.draw_text("Press SPACE to try again", self.font, CRT_GREEN, WIDTH//2 + ox, HEIGHT - 100 + oy, center=True)

        elif self.state == "VICTORY":
            self.draw_victory_beach()

        pygame.display.flip()

if __name__ == "__main__":
    game = OdysseyPygame()
    game.run()
