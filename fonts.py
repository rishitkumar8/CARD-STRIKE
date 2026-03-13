import pygame

pygame.init()

# ═══════════════════════════════════════
# 4K Typography System (8px Grid)
# ═══════════════════════════════════════

# Body — Clean & Readable
FONT_MICRO  = pygame.font.Font(None, 16)   # Tiny labels
FONT_SMALL  = pygame.font.Font(None, 20)   # Secondary info
FONT_MAIN   = pygame.font.Font(None, 24)   # Body text
FONT_MEDIUM = pygame.font.Font(None, 28)   # Subheadings
FONT_BIG    = pygame.font.Font(None, 32)   # Headings
FONT_LARGE  = pygame.font.Font(None, 40)   # Section titles

# Display — Bold & Thematic
FONT_DMG    = pygame.font.Font(None, 48)   # Damage numbers
FONT_XL     = pygame.font.Font(None, 56)   # Hero text
FONT_TITLE  = pygame.font.Font(None, 80)   # Screen titles
FONT_HERO   = pygame.font.Font(None, 96)   # Banner text
