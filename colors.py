# ═══════════════════════════════════════════════════════
# PREMIER COLOR SYSTEM — "Frost Aurora"
# Light, Soft, Eye-Friendly Strategy Palette
# ═══════════════════════════════════════════════════════


# ───────────────────────────────────────────────────────
# FOUNDATION (Soft Light Mode Core)
# ───────────────────────────────────────────────────────
C_BG_PRIMARY    = (30, 32, 48)      # Deep Charcoal Blue
C_BG_SECONDARY  = (38, 42, 62)     # Muted Navy
C_BG_TERTIARY   = (52, 58, 82)     # Dusty Slate
C_BG_GRADIENT_T = (38, 42, 65)
C_BG_GRADIENT_B = (25, 28, 42)


# ───────────────────────────────────────────────────────
# ACCENTS (Pastel & Gentle)
# ───────────────────────────────────────────────────────
C_ACCENT        = (100, 175, 195)   # Dusty Teal
C_ACCENT_GLOW   = (140, 195, 210)   # Soft Sky
C_ACCENT_DARK   = (65, 120, 145)

C_GOLD          = (195, 165, 85)    # Warm Sand
C_GOLD_BRIGHT   = (215, 195, 130)
C_GOLD_DARK     = (140, 120, 65)


# ───────────────────────────────────────────────────────
# GAMEPLAY TOKENS (Team Identity — Gentle Pastels)
# ───────────────────────────────────────────────────────
C_PLAYER        = (100, 190, 155)   # Sage Green
C_PLAYER_GLOW   = (155, 215, 190)

C_ENEMY         = (195, 110, 120)   # Dusty Rose
C_ENEMY_GLOW    = (215, 160, 170)


# ───────────────────────────────────────────────────────
# RANGE INDICATORS (Subtle & Soft)
# ───────────────────────────────────────────────────────
C_RANGE_MOVE    = (90, 135, 185)    # Soft Periwinkle
C_RANGE_ATK     = (140, 110, 180)   # Muted Lavender
C_RANGE_INVALID = (180, 100, 100)   # Dusty Coral


# ───────────────────────────────────────────────────────
# ELEMENTS (Pastel Fantasy Palette)
# ───────────────────────────────────────────────────────
E_FIRE          = (200, 115, 75)    # Warm Terracotta
E_FIRE_GLOW     = (220, 165, 130)

E_WATER         = (95, 150, 195)    # Calm Blue
E_WATER_GLOW    = (155, 190, 220)

E_LEAF          = (100, 180, 120)   # Soft Fern
E_LEAF_GLOW     = (160, 215, 175)

E_AIR           = (185, 200, 220)   # Misty Silver
E_AIR_GLOW      = (210, 220, 235)

E_NULL          = (150, 120, 185)   # Soft Amethyst
E_NULL_GLOW     = (190, 175, 215)


# ───────────────────────────────────────────────────────
# TEXT & UI (Soft Warmth)
# ───────────────────────────────────────────────────────
C_TEXT          = (210, 215, 225)   # Warm Off-White
C_TEXT_SEC      = (160, 168, 185)
C_TEXT_DIM      = (115, 122, 145)
C_WHITE         = (225, 230, 240)


# ───────────────────────────────────────────────────────
# SYSTEM STATES
# ───────────────────────────────────────────────────────
C_VICTORY       = (110, 195, 145)   # Soft Mint
C_DEFEAT        = (190, 100, 115)   # Muted Rose
C_WARNING       = (200, 160, 85)    # Warm Honey
C_SUCCESS       = C_PLAYER


# ───────────────────────────────────────────────────────
# EFFECTS
# ───────────────────────────────────────────────────────
C_CONFETTI = [
    (100, 190, 155),    # Sage Green
    (195, 110, 120),    # Dusty Rose
    (100, 175, 195),    # Dusty Teal
    (195, 165, 85),     # Warm Sand
    (150, 120, 185)     # Soft Amethyst
]

C_SHADOW = (10, 10, 15)


# ───────────────────────────────────────────────────────
# GRID & PANELS
# ───────────────────────────────────────────────────────
C_GRID      = (55, 62, 90)          # Soft Grid
C_PANEL     = C_BG_SECONDARY
C_BG        = C_BG_PRIMARY
C_HIGHLIGHT = C_ACCENT_GLOW
C_SELECT    = C_GOLD


# ═══════════════════════════════════════════════════════
# OPTIONAL: Recommended Glow Alpha Values (Pygame)
# ═══════════════════════════════════════════════════════
GLOW_ALPHA_SOFT   = 60
GLOW_ALPHA_MEDIUM = 90
GLOW_ALPHA_STRONG = 120