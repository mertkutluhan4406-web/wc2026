import sys
import os

sys.path.insert(0, r"C:\WC2026\backend")
from app.data.players import PLAYERS_DB

PLAYERS_FILE = r"C:\WC2026\backend\app\data\players.py"

def normalize_name(name):
    if not name:
        return ""
    name = name.lower().strip()
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o', 'ø': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c', 'ß': 'ss',
        'ğ': 'g', 'ş': 's', 'ı': 'i',
        'ð': 'd', 'þ': 'th', 'æ': 'ae',
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    # Map junior/júnior to jr
    name = name.replace("junior", "jr")
    name = name.replace("júnior", "jr")
    # Remove non-alphanumeric characters
    name = "".join(c for c in name if c.isalnum())
    return name

def is_wc_league(league):
    if not league:
        return True
    l_lower = league.lower()
    return 'world cup' in l_lower or 'country' in l_lower

def merge_players(p1, p2):
    """Merge player p2 into p1 (p1 is modified in place)."""
    # 1. Image Url: Keep custom if p1 has default
    if p1.get('image_url') in ('/avatars/default.png', '') and p2.get('image_url') not in ('/avatars/default.png', ''):
        p1['image_url'] = p2['image_url']
        
    # 2. Team: Keep club team rather than national team name at the root
    t1_is_nat = p1.get('team') == p1.get('nationality')
    t2_is_nat = p2.get('team') == p2.get('nationality')
    
    # Also if one team is Grêmio FBPA (incorrectly matched) and the other is Real Madrid CF, keep Real Madrid CF
    p1_team = p1.get('team', '')
    p2_team = p2.get('team', '')
    
    if 'grêmio' in p1_team.lower() and 'real madrid' in p2_team.lower():
        p1['team'] = p2['team']
    elif t1_is_nat and not t2_is_nat:
        p1['team'] = p2['team']
    
    # 3. Position: Keep more detailed/accurate midfielder/forward position if CM/ST/CF
    pos_rank = {'GK': 0, 'CB': 1, 'LB': 1, 'RB': 1, 'CDM': 2, 'CM': 2, 'LM': 3, 'RM': 3, 'CAM': 4, 'LW': 5, 'RW': 5, 'ST': 6, 'CF': 6}
    pos1 = p1.get('position', 'CM')
    pos2 = p2.get('position', 'CM')
    if pos_rank.get(pos2, 2) > pos_rank.get(pos1, 2):
        p1['position'] = pos2

    # 4. Merge seasons
    if 'seasons' not in p1:
        p1['seasons'] = {}
    if 'seasons' in p2:
        for sk, sdata2 in p2['seasons'].items():
            if sk not in p1['seasons']:
                p1['seasons'][sk] = sdata2
            else:
                sdata1 = p1['seasons'][sk]
                l1 = sdata1.get('league', '')
                l2 = sdata2.get('league', '')
                
                # Check if p2 season has club stats, and p1 has WC/mock
                if is_wc_league(l1) and not is_wc_league(l2):
                    # Overwrite with club stats
                    p1['seasons'][sk] = sdata2
                elif not is_wc_league(l1) and is_wc_league(l2):
                    # Keep p1, it has club stats
                    pass
                elif 'brazil' in l1.lower() and 'la liga' in l2.lower():
                    # Special case for Vinicius (keep La Liga stats over Grêmio stats)
                    p1['seasons'][sk] = sdata2
                else:
                    # Both are club or both are WC, keep the one with more apps or goals
                    apps1 = sdata1.get('raw_stats', {}).get('playedMatches', sdata1.get('apps', 0))
                    apps2 = sdata2.get('raw_stats', {}).get('playedMatches', sdata2.get('apps', 0))
                    if apps2 > apps1:
                        p1['seasons'][sk] = sdata2
                        
    # 5. Merge career history
    if 'career_history' not in p1:
        p1['career_history'] = {}
    if 'career_history' in p2:
        for sk, ch2 in p2['career_history'].items():
            if sk not in p1['career_history']:
                p1['career_history'][sk] = ch2
            else:
                ch1 = p1['career_history'][sk]
                # Special case for Vinicius: Grêmio rating is lower / apps is different
                # We prefer Real Madrid stats (higher goals/assists or rating)
                if ch2.get('rating', 0) > ch1.get('rating', 0) or ch2.get('goals', 0) > ch1.get('goals', 0):
                    p1['career_history'][sk] = ch2

    # 6. Merge pressure trend
    if 'tournament_pressure_trend' not in p1:
        p1['tournament_pressure_trend'] = {}
    if 'tournament_pressure_trend' in p2:
        p1['tournament_pressure_trend'].update(p2['tournament_pressure_trend'])

    # 7. Merge club vs country
    if 'club_vs_country' not in p1:
        p1['club_vs_country'] = p2.get('club_vs_country', {'club': {}, 'country': {}})
    elif 'club_vs_country' in p2:
        cc1 = p1['club_vs_country']
        cc2 = p2['club_vs_country']
        for key in ('club', 'country'):
            if key not in cc1 or not cc1[key]:
                cc1[key] = cc2.get(key, {})
            elif key in cc2 and cc2[key]:
                if cc2[key].get('goals', 0) > cc1[key].get('goals', 0):
                    cc1[key] = cc2[key]
                    
    # Update peak season
    if p1.get('career_history'):
        best_season = max(p1['career_history'].items(), key=lambda x: x[1].get('rating', 0))
        p1['career_peak_season'] = best_season[0]

def main():
    # Setup output encoding to utf-8 safely
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60)
    print("FUZZY MERGING DUPLICATES IN PLAYERS_DB")
    print("=" * 60)
    
    # Group by (normalized_name, normalized_nationality)
    groups = {}
    for pid, p in PLAYERS_DB.items():
        norm_name = normalize_name(p['name'])
        norm_nat = normalize_name(p.get('nationality', ''))
        key = (norm_name, norm_nat)
        if key not in groups:
            groups[key] = []
        groups[key].append((pid, p))
        
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"Found {len(duplicates)} fuzzy duplicate player groups.")
    
    cleaned_db = {}
    removed_ids = []
    
    # Process all groups
    for key, items in groups.items():
        # Sort items by ID: keep the lowest ID as the primary/target ID
        items_sorted = sorted(items, key=lambda x: x[0])
        primary_id, primary_player = items_sorted[0]
        
        # Merge all secondary players into the primary player
        for secondary_id, secondary_player in items_sorted[1:]:
            print(f"Merging ID {secondary_id} ({secondary_player['name']} - {secondary_player.get('team')}) -> ID {primary_id} ({primary_player['name']} - {primary_player.get('team')})")
            merge_players(primary_player, secondary_player)
            removed_ids.append(secondary_id)
            
        cleaned_db[primary_id] = primary_player

    print(f"\nTotal players before merge: {len(PLAYERS_DB)}")
    print(f"Total players after merge: {len(cleaned_db)}")
    print(f"Removed {len(removed_ids)} duplicate IDs: {removed_ids}")
    
    # Save the database back to players.py
    print(f"\nWriting cleaned PLAYERS_DB to {PLAYERS_FILE}...")
    
    def py_repr(obj, indent=0):
        sp = "    " * indent
        sp1 = "    " * (indent + 1)
        if obj is None:
            return "None"
        elif isinstance(obj, bool):
            return "True" if obj else "False"
        elif isinstance(obj, (int, float)):
            return repr(obj)
        elif isinstance(obj, str):
            return repr(obj)
        elif isinstance(obj, list):
            if not obj:
                return "[]"
            items = ", ".join(py_repr(v, 0) for v in obj)
            if len(items) < 80:
                return f"[{items}]"
            items = (",\n" + sp1).join(py_repr(v, indent + 1) for v in obj)
            return f"[\n{sp1}{items}\n{sp}]"
        elif isinstance(obj, dict):
            if not obj:
                return "{}"
            parts = []
            for k, v in obj.items():
                kr = repr(k)
                vr = py_repr(v, indent + 1)
                parts.append(f"{kr}: {vr}")
            inner = (",\n" + sp1).join(parts)
            return f"{{\n{sp1}{inner}\n{sp}}}"
        return repr(obj)

    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        f.write("# Cleaned database - World Cup 2026 Players (Accents and fuzzy duplicates resolved)\n")
        f.write("PLAYERS_DB = {\n")
        for pid in sorted(cleaned_db.keys()):
            pdata = cleaned_db[pid]
            f.write(f"    {pid}: {py_repr(pdata, 1)},\n")
        f.write("}\n\n")
        f.write("# Convert keys to integers\n")
        f.write("PLAYERS_DB = {int(k): v for k, v in PLAYERS_DB.items()}\n")
        
    print("File saved successfully! Verifying syntax...")
    with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        compile(content, PLAYERS_FILE, "exec")
        print("Syntax check passed! PLAYERS_DB is valid.")
    except SyntaxError as e:
        print(f"SYNTAX ERROR in generated players.py: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
