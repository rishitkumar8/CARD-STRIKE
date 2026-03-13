import sys
import os
sys.path.append(r'c:\Users\Public\Documents\4thsem\projects\marve-strike\marve-strike')

try:
    from animations import anim_mgr
    print(f"anim_mgr imported: {anim_mgr}")
    import logic_attack
    print("logic_attack imported")
    # Check if 'anim_mgr' is in logic_attack's globals
    if 'anim_mgr' in dir(logic_attack):
        print(f"logic_attack.anim_mgr: {logic_attack.anim_mgr}")
    else:
        print("logic_attack.anim_mgr NOT FOUND")
except Exception as e:
    import traceback
    traceback.print_exc()
