
import json

def update_status(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for card in data['cards']:
        attacks = card['attacks']
        
        for atk in attacks:
            name = atk['name'].lower()
            desc = atk.get('description', '')
            
            # Default
            atk['status_type'] = "none"
            atk['status_duration'] = 0
            atk['status_value'] = 0
            
            # 1. BURN (Fire themed)
            if 'burn' in name or 'fire' in name or 'flame' in name or 'ember' in name or 'magma' in name:
                atk['status_type'] = "burn"
                atk['status_value'] = 5 
                atk['status_duration'] = 2
                
                # Update description
                if "Burn" not in desc and "Fire" not in desc:
                     atk['description'] = desc + " (Burn 5dmg/2t)"
                elif "Burn" not in desc: # Avoid duplicate
                     atk['description'] += " (Burn 5dmg/2t)"

            # 2. ROOT (Nature/Water/Trap/Anchor)
            elif 'root' in name or 'vine' in name or 'trap' in name or 'anchor' in name or 'freeze' in name:
                atk['status_type'] = "root"
                atk['status_duration'] = 1
                atk['status_value'] = 0
                atk['cooldown'] = max(atk.get('cooldown', 0), 2) # Root needs cooldown
                
                if "Root" not in desc:
                   atk['description'] += " (Root 1t)"

            # 3. STUN (Shock/Slam/Bash/Heavy/Stun)
            elif 'shock' in name or 'slam' in name or 'stun' in name or 'heavy' in name or 'bash' in name:
                # Only if cooldown is high enough or damage low
                if atk.get('cooldown', 0) >= 2:
                    atk['status_type'] = "stun"
                    atk['status_duration'] = 1
                    atk['status_value'] = 0
                    atk['cooldown'] = 3 # Stun needs high cooldown
                    
                    if "Stun" not in desc:
                       atk['description'] += " (Stun 1t)"

            # Clean up description duplicates if run multiple times
            # (Simple check to avoid infinite appending)
            # Not strictly necessary if I run once.

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("Updated cards.json with status effects.")

if __name__ == "__main__":
    update_status("cards.json")
