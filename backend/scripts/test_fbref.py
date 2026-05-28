import requests
from bs4 import BeautifulSoup

url = "https://fbref.com/en/comps/9/stats/Premier-League-Stats"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    r = requests.get(url, headers=headers, timeout=15)
    print(f"Status: {r.status_code}")
    print(f"Content length: {len(r.text)}")
    
    if r.status_code == 200:
        soup = BeautifulSoup(r.text, "html.parser")
        # Find the main stats table
        table = soup.find("table", {"id": "stats_standard"})
        if table:
            rows = table.find("tbody").find_all("tr")
            print(f"\nFound {len(rows)} player rows!")
            # Print first 10 players
            for row in rows[:10]:
                cells = row.find_all(["th", "td"])
                if len(cells) > 5:
                    name = cells[0].get_text(strip=True)
                    nation = cells[1].get_text(strip=True)
                    pos = cells[2].get_text(strip=True)
                    team = cells[3].get_text(strip=True)
                    age = cells[4].get_text(strip=True)
                    mp = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                    goals = cells[8].get_text(strip=True) if len(cells) > 8 else ""
                    assists = cells[9].get_text(strip=True) if len(cells) > 9 else ""
                    print(f"  {name} | {nation} | {pos} | {team} | Age:{age} | MP:{mp} | G:{goals} | A:{assists}")
        else:
            print("Table not found. Looking for other tables...")
            tables = soup.find_all("table")
            print(f"Found {len(tables)} tables total")
            for t in tables[:5]:
                tid = t.get("id", "no-id")
                print(f"  Table ID: {tid}")
    else:
        print(f"Failed with status {r.status_code}")
        print(r.text[:500])
except Exception as e:
    print(f"Error: {e}")
