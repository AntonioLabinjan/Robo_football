"""Global configuration constants."""

FIELD_W, FIELD_H = 1000, 640
MARGIN = 40
GOAL_WIDTH = 120
GOAL_DEPTH = 20
PENALTY_W, PENALTY_H = 160, 300
CENTER_CIRCLE_R = 70

SCREEN_W = FIELD_W + MARGIN * 2 + 260
SCREEN_H = FIELD_H + MARGIN * 2 + 60
FPS = 60
DT = 1.0 / FPS

MATCH_SECONDS = 300

ROBOT_RADIUS = 12
BALL_RADIUS = 6

MAX_SPEED = 140.0
ACCELERATION = 220.0
FRICTION_ROBOT = 60.0

BALL_FRICTION = 40.0
BALL_MAX_SPEED = 420.0
PASS_SPEED = 260.0
SHOOT_SPEED = 400.0

POSSESSION_RADIUS = ROBOT_RADIUS + BALL_RADIUS + 2
STEAL_RADIUS = ROBOT_RADIUS * 2
MAX_HOLD_TIME = 3.0  # seconds a robot may hold the ball before it must pass/shoot/clear
MAX_DEFENDERS_IN_BOX = 2  # at most this many teammates may occupy their own penalty box

FOUL_CONTACT_SECONDS = 1.0  # sustained opposing-robot contact before it's called a foul
FOUL_PUSHBACK = 10.0         # cm the non-possessing player is pushed back on a foul

SHOOT_RATE_PER_SEC = 1.5      # chances per second once in range (was 0.7 - more trigger-happy)
SHOOT_RANGE_MULTIPLIER = 1.35  # willing to shoot from well beyond tactics.shooting_distance
SHOOT_JITTER = 0.22            # wider random aim error (was 0.08 - less accurate, more reckless)

TEAM_BLUE = "BLUE"
TEAM_RED = "RED"

COLOR_BLUE = (60, 120, 240)
COLOR_RED = (230, 70, 70)
COLOR_FIELD = (30, 130, 76)
COLOR_LINE = (240, 240, 240)
COLOR_BALL = (250, 220, 40)
COLOR_BG = (18, 18, 22)
COLOR_PANEL = (28, 30, 36)
COLOR_TEXT = (230, 230, 230)

FORMATIONS = ["2-2-1", "1-3-1", "2-1-2"]
ATTACK_BIAS = ["Defensive", "Balanced", "Offensive"]
PASSING_PREF = ["Safe", "Short", "Direct"]

SIM_SPEEDS = [0.5, 1.0, 2.0, 5.0, 10.0]