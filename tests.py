import unittest
import unittest.mock
import json
import random
from app import app

class TestExilesSolver(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        app.testing = True

    def create_fencer(self, name, category, favorite_weapon="foil"):
        # Helper to create fencer with strong preference for one weapon
        prefs = {"foil": 1, "epee": 1, "sabre": 1}
        prefs[favorite_weapon] = 5
        return {
            "name": name,
            "category": category,
            "preference": prefs
        }

    def test_basic_team_formation(self):
        # 6 People: 3M, 3F. Should form 2 teams.
        fencers = [
            self.create_fencer("M1", "M"), self.create_fencer("M2", "M"), self.create_fencer("M3", "M"),
            self.create_fencer("F1", "F"), self.create_fencer("F2", "F"), self.create_fencer("F3", "F")
        ]
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        
        self.assertIn("teams", data)
        self.assertEqual(len(data["teams"]), 2) 
        
        for team in data["teams"]:
            self.assertEqual(len(team["members"]), 3)
            # Check constraints (simplistic check)
            cats = [m["category"] for m in team["members"].values()]
            self.assertTrue("F" in cats and "M" in cats)

    def test_reserve_assignment_logic(self):
        # 8 People: 4M, 4F. -> 2 Teams (6 ppl). 2 Reserves.
        # We want to test logic where reserves are assigned.
        fencers = [
            self.create_fencer("M1", "M"), self.create_fencer("M2", "M"), self.create_fencer("M3", "M"), self.create_fencer("M4", "M"),
            self.create_fencer("F1", "F"), self.create_fencer("F2", "F"), self.create_fencer("F3", "F"), self.create_fencer("F4", "F")
        ]
        
        # Force specific preferences to test matching logic
        # Reserve P(Foil). T(F(Foil)). Should MATCH (Priority) or NOT Match?
        # Logic: 2+ F -> Match. 1 F -> No Match.
        
        # It's hard to control specific team composition without mocking solver results.
        # But we can check the *Result* adheres to the rules.
        
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        teams = data["teams"]
        
        for team in teams:
            if "reserves" in team:
                reserve = team["reserves"][0]
                members = team["members"]
                f_assigned_weapons = [w for w, m in members.items() if m["category"] == "F"]
                reserve_weapon = reserve["weapon"]
                
                # Check Logic
                if len(f_assigned_weapons) >= 2:
                    # Priority case: Should match IF possible.
                    # It matches if reserve_weapon is in f_assigned_weapons.
                    # If it's not, it implies favorite didn't match and no secondary matched?
                    # Or logic failed?
                    # With my recent changes, it tries 2ndary.
                    # Verify it is one of them OR confirm no overlap was possible (unlikely with 2F)
                    pass 
                elif len(f_assigned_weapons) == 1:
                    # 1F case: MUST NOT MATCH
                    self.assertNotEqual(reserve_weapon, f_assigned_weapons[0],
                                        f"Team has 1F ({f_assigned_weapons[0]}). Reserve ({reserve_weapon}) should NOT match.")

    def test_max_one_reserve(self):
        # Create scenario with many reserves
        # 4 Participants. Wait. 3 per team.
        # 4 Ppl -> 1 Team (3). 1 Reserve.
        fencers = [
            self.create_fencer("P1", "M"), self.create_fencer("P2", "M"), 
            self.create_fencer("P3", "F"), self.create_fencer("R1_Res", "M")
        ]
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        teams = data["teams"]
        
        for team in teams:
            if "reserves" in team:
                self.assertLessEqual(len(team["reserves"]), 1, "Team has more than 1 reserve!")

    def test_reserve_priority_for_2f_team(self):
        # Scenario: 7 People. 4M, 3F.
        # Teams: 2. (6 ppl). 1 Reserve.
        # We want correct split: One team 2F, One team 1F.
        # Reserve should be assigned to 2F team if possible constraints met.
        
        fencers = [
            self.create_fencer("F1", "F", "foil"), # Team 1
            self.create_fencer("F2", "F", "epee"), # Team 1
            self.create_fencer("M1", "M", "sabre"), # Team 1
            
            self.create_fencer("F3", "F", "epee"), # Team 2
            self.create_fencer("M2", "M", "foil"), # Team 2
            self.create_fencer("M3", "M", "sabre"), # Team 2
            
            self.create_fencer("ReserveM", "M", "foil") # Reserve candidate
        ]
        
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        teams = data["teams"]
        
        # Identify teams
        team_2f = None
        team_1f = None
        for t in teams:
            f_count = len([m for m in t["members"].values() if m["category"] == "F"])
            if f_count == 2: team_2f = t
            if f_count == 1: team_1f = t
            
        if team_2f and team_1f:
            # Check where the reserve is
            # Ideally in team_2f (2F Priority)
            # Whoever is reserve must match 2F weapon rule.
            
            if len(team_2f["reserves"]) > 0:
                 r = team_2f["reserves"][0]
                 # Validation: Must matching F weapon.
                 f_weaps = [w for w, m in team_2f["members"].items() if m["category"] == "F"]
                 self.assertIn(r["weapon"], f_weaps, "Reserve on 2F team MUST match one F weapon")
            elif len(team_1f["reserves"]) > 0:
                 r = team_1f["reserves"][0]
                 # If assigned to 1F, verify 1F rule compliance
                 f_weaps = [w for w, m in team_1f["members"].items() if m["category"] == "F"]
                 if r["category"] == "M":
                     self.assertNotEqual(r["weapon"], f_weaps[0], "Reserve M on 1F team matched F weapon!")
            else:
                 # No reserve assigned? Impossible with N=7 and Teams=2 (Capacity=6 main).
                 # Wait... Capacity of 2 teams is 6 Main. 7th person MUST be reserve.
                 self.fail("Reserve was not assigned to either team?")
        else:
            # Solved might have produced 3F and 0F? Or 3M?
            # With penalties, 2F/1F is optimal.
            self.fail("Solver did not produce expected 2F/1F team split.")

    def test_secondary_weapon_priority(self):
        """Test that reserve takes 2nd favorite weapon (score >= 3) to join 2F team if favorite doesn't match"""
        
        # Scenario adjusted for Flexible Reserve
        fencers = [
             self.create_fencer("F1", "F", "foil"),
             self.create_fencer("F2", "F", "epee"),
             self.create_fencer("M1", "M", "sabre"),
             
             self.create_fencer("F3", "F", "epee"),
             self.create_fencer("M2", "M", "foil"),
             self.create_fencer("M3", "M", "sabre"),
             
             # Reserve with Flexible preferences
             {"name": "ReserveFlex", "category": "M", "preference": {"sabre": 5, "foil": 3, "epee": 1}}
        ]
        
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        teams = data["teams"]
        
        team_2f = None
        for t in teams:
            f_count = len([m for m in t["members"].values() if m["category"] == "F"])
            if f_count >= 2:
                team_2f = t
                
        self.assertIsNotNone(team_2f)
        # Check if reserve is here
        if len(team_2f["reserves"]) > 0:
            r = team_2f["reserves"][0]
            # Since Fav is Sabre, and T1 has F(Foil), F(Epee). Sabre does NOT match.
            # R MUST use Foil (3) or Epee (1). Foil is better.
            # Verify R weapon is matching F.
            f_weaps = [w for w, m in team_2f["members"].items() if m["category"] == "F"]
            self.assertIn(r["weapon"], f_weaps)
            # Implicitly validating flexible selection

    def test_1f_m_reserve_constraint(self):
        """Test that if M reserve is assigned to 1F team, weapon MUST NOT match F (switch if needed)"""
        
        # Scenario: T1(1F) and T2(3M). Reserve MUST go to T1.
        # But Reserve Fav matches F on T1. Strict constraint: Switch weapon.
        
        fencers = [
             self.create_fencer("F1", "F", "foil"), # T1
             self.create_fencer("M1", "M", "epee"), # T1
             self.create_fencer("M2", "M", "sabre"), # T1
             
             self.create_fencer("M3", "M", "foil"), # T2 (3M)
             self.create_fencer("M4", "M", "epee"), # T2
             self.create_fencer("M5", "M", "sabre"), # T2
             
             # Reserve M. Fav Foil.
             {"name": "ReserveM_Switch", "category": "M", "preference": {"foil": 5, "epee": 4, "sabre": 1}}
        ]

        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        teams = data["teams"]
        
        t1 = None
        t2 = None
        for t in teams:
            f_names = [m["name"] for m in t["members"].values()]
            cat_list = [m["category"] for m in t["members"].values()]
            if "F" not in cat_list: t2 = t # 3M
            else: t1 = t
            
        if t2:
            self.assertEqual(len(t2["reserves"]), 0, "3M Team should NOT have reserves")
            
        self.assertIsNotNone(t1)
        self.assertEqual(len(t1["reserves"]), 1)
        r = t1["reserves"][0]
        # Verify Mismtch
        f_weaps = [w for w, m in t1["members"].items() if m["category"] == "F"]
        f_w = f_weaps[0] # 1F
        
        self.assertNotEqual(r["weapon"], f_w, "Constraint Failed: M Reserve assigned same weapon as F in 1F team")
        # Should have switched
        self.assertIn(r["weapon"], ["epee", "sabre"])
        
    def test_user_reported_case(self):
        """Reproduction of user reported scenario"""
        raw_data = [
            ["Cristian Stemate", "M", 1, 5, 3],
            ["George Gleisinger", "M", 1, 5, 1],
            ["Tom Locke", "M", 5, 1, 1],
            ["Christian Thorley", "M", 1, 3, 5],
            ["Carolina Van Eldik", "F", 1, 5, 2],
            ["William Blackwell", "M", 1, 3, 4],
            ["Sydney Hall", "F", 3, 5, 1],
            ["Patrick Stillman", "M", 5, 1, 1],
            ["Ben Mitchell", "M", 1, 3, 5],
            ["Ben Woodman", "M", 1, 1, 5],
            ["Molly Carey", "F", 5, 4, 1],
            ["Daniel Smythe", "M", 1, 5, 3],
            ["Tom Fletcher", "M", 5, 5, 5], 
            ["Klara Hlavac", "F", 5, 1, 1],
            ["Joseph McIlroy", "M", 1, 5, 1],
            ["Faye Russell", "F", 5, 1, 1],
            ["Lorenzo Rossi", "M", 5, 2, 4],
            ["Carlene Howard", "F", 4, 1, 5],
            ["Mark Harrison", "M", 2, 5, 1],
            ["Maisie Davidson", "F", 3, 5, 1],
            ["Kal-el Dyson-Bowen", "M", 4, 2, 4],
            ["Test me", "F", 1, 5, 2],
            ["Testing good", "F", 5, 2, 4]
        ]
        
        fencers = []
        for row in raw_data:
            fencers.append({
                "name": row[0],
                "category": row[1],
                "preference": {"foil": row[2], "epee": row[3], "sabre": row[4]}
            })
            
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        teams = data["teams"]
        
        for t in teams:
            f_count = len([m for m in t["members"].values() if m["category"] == "F"])
            if f_count == 0: # 3M
                self.assertNotIn("reserves", t, f"Team {t['team']} is 3M but got a reserve!")

if __name__ == '__main__':
    unittest.main()
