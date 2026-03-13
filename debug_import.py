
try:
    import game_grid
    print("Exported names:", dir(game_grid))
    print("Has chebyshev_dist?", hasattr(game_grid, 'chebyshev_dist'))
except Exception as e:
    print("Import failed:", e)
