
import json

def update_cards(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for card in data['cards']:
        attacks = card['attacks']
        elem = card['element']
        
        for i, atk in enumerate(attacks):
            name = atk['name'].lower()
            desc = atk['description'].lower()
            
            # Default values
            atk['range'] = 3
            atk['cooldown'] = 0
            atk['is_life_drain'] = False
            
            # Check for healing
            is_healing = 'heal' in name or 'heal' in desc or 'nature' in name
            if is_healing and elem == 'leaf':
                atk['range'] = 4
                atk['cooldown'] = 3
                atk['flame_trail'] = False # Ensure no conflicting effects
                atk['damage'] = 20 # Strong heal as requested (18-20)
                # Mark as healing type implicitly or explicitly if system demands
                # But Attack class uses is_healing flag. 
                # Let's add is_healing field to JSON too so loader picks it up.
                atk['is_healing'] = True
            elif 'drain' in name or 'sap' in name or (elem == 'leaf' and 'strike' in name):
                 # Life Drain potential
                 if 'life' in desc or 'drain' in desc:
                     atk['is_life_drain'] = True
                     atk['damage'] = 10
                     atk['heal_amount'] = 15
                     atk['cooldown'] = 3
                     atk['range'] = 2

            # Range & Cooldown Logic based on index/power
            # Usually index 0 is basic, 1 is strong, 2 is ult
            
            if i == 0: # Basic
                atk['range'] = 3
                atk['cooldown'] = 0
                if atk.get('damage', 0) > 12:
                    atk['range'] = 2
            
            elif i == 1: # Strong
                atk['range'] = 2
                atk['cooldown'] = 2
                if atk.get('damage', 0) > 14:
                    atk['range'] = 1
            
            elif i == 2: # Ult
                atk['cooldown'] = 3
                if 'fusion' in name:
                    atk['range'] = 3
                    atk['damage'] = 16
                else:
                    atk['range'] = 3

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    update_cards("cards.json")
