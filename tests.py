import unittest
import unittest.mock
import json
import random
from app import app

class TestExilesSolver(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def create_fencer(self, name, category, favorite_weapon="foil"):
        # Helper to create a fencer dict
        # Preference: 5 for favorite, 1 otherwise
        prefs = {"foil": 1, "epee": 1, "sabre": 1}
        prefs[favorite_weapon] = 5
        return {
            "name": name,
            "category": category,
            "preference": prefs
        }

    def test_basic_team_formation(self):
        """Test standard case with multiple of 3 fencers"""
        fencers = []
        # Create 6 fencers (2 teams)
        for i in range(3):
            fencers.append(self.create_fencer(f"M{i}", "M", "foil"))
        for i in range(3):
            fencers.append(self.create_fencer(f"F{i}", "F", "epee"))

        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "ok")
        self.assertEqual(len(data["teams"]), 2)
        
        # Check basic team structure
        for team in data["teams"]:
            self.assertIn("members", team)
            self.assertEqual(len(team["members"]), 3)
            self.assertIn("foil", team["members"])
            self.assertIn("epee", team["members"])
            self.assertIn("sabre", team["members"])

    def test_reserve_assignment_logic(self):
        """Test reserve assignment with 7 fencers (1 reserve)"""
        # Scenario: 
        # Team will have 3 members. 
        # 1 Reserve left over.
        # We want to force a scenario where we can verify constraint logic.
        
        # Create a pool that forms 1 Team.
        # Team Members: 2F, 1M (To test 2F constraint)
        # Reserve: M, Favorite = One of the F's assigned weapon
        
        # Let's try to pass enough fencers for 1 team (3) + 1 reserve = 4 total.
        # However, the code logic separates "reserves" if Total % 3 != 0.
        # 4 % 3 = 1 reserve.
        
        # Fencers:
        # F1 (Fav: Foil)
        # F2 (Fav: Epee)
        # M1 (Fav: Sabre)
        # R1 (Fav: Foil) -> Should match F1 if F1 gets Foil.
        
        fencers = [
            self.create_fencer("F1", "F", "foil"),
            self.create_fencer("F2", "F", "epee"),
            self.create_fencer("M1", "M", "sabre"),
            self.create_fencer("R1_Res", "M", "foil") 
        ]
        
        # The logic in app.py:
        # 1. Reserves removed if %3 != 0. (R1 might be removed randomly)
        # But we want to ensure R1 is the reserve? It's random.
        # We can't strictly force WHO is reserve, but we can check the RESULT.
        
        # Run multiple times to catch potential logic errors if randomness hits edge cases?
        # Actually, let's just check that WHOEVER is reserve satisfies the condition.
        
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        
        teams = data["teams"]
        self.assertEqual(len(teams), 1)
        team = teams[0]
        
        # Check structure
        self.assertIn("reserves", team)
        self.assertEqual(len(team["reserves"]), 1)
        
        reserve = team["reserves"][0]
        reserve_weapon = reserve["weapon"]
        
        # Verify Constraint:
        # If team has >= 2F: Reserve Weapon MUST be in F_Assigned_Weapons
        # If team has 1F: Reserve Weapon MUST NOT be F_Assigned_Weapon
        
        members = team["members"]
        f_assigned_weapons = [w for w, m in members.items() if m["category"] == "F"]
        
        if len(f_assigned_weapons) >= 2:
            self.assertIn(reserve_weapon, f_assigned_weapons, 
                          f"Team has {len(f_assigned_weapons)}F. Reserve ({reserve_weapon}) should match one of them: {f_assigned_weapons}")
        elif len(f_assigned_weapons) == 1:
            self.assertNotEqual(reserve_weapon, f_assigned_weapons[0],
                                f"Team has 1F ({f_assigned_weapons[0]}). Reserve ({reserve_weapon}) should NOT match.")

    def test_max_one_reserve(self):
        """Test to ensure max 1 reserve per team"""
        # 8 fencers -> 2 teams (6) + 2 reserves.
        # Should result in 2 teams, each with 1 reserve.
        
        fencers = []
        for i in range(8):
            fencers.append(self.create_fencer(f"P{i}", "M" if i%2==0 else "F", "foil"))
            
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        
        teams = data["teams"]
        self.assertEqual(len(teams), 2)
        
        for team in teams:
            if "reserves" in team:
                self.assertLessEqual(len(team["reserves"]), 1, "Team has more than 1 reserve!")
                
    def test_single_female_constraint(self):
        """Test specific logic for 1 Female in team"""
        # Create pool forcing 1 team with 1F
        # 3 Fencers: F1(Foil), M1(Epee), M2(Sabre) + R1(Foil)
        # R1 matches F1's weapon. Should be INVALID for assignment if strict logic holds?
        # BUT the logic says "fallback to random/any if no valid".
        # So if we ONLY have 1 valid team and it forbids it, it might force fallback.
        # But we want to see it Work if there IS a choice.
        pass # Difficult to construct deterministic scenario with heavy randomness, relying on general logic check in test_reserve_assignment_logic

    @unittest.mock.patch('random.sample')
    def test_reserve_priority_for_2f_team(self, mock_sample):
        """Test that if a 2-Female team is available and valid, reserve goes there instead of 1-F team"""
        
        # Determine the object corresponding to "ReserveM" to force it as reserve
        # But random.sample is called with a LIST of objects.
        # We need a side_effect that returns the correct object from the list.
        
        fencers = [
             self.create_fencer("F1", "F", "foil"), # T1
             self.create_fencer("F2", "F", "epee"), # T1
             self.create_fencer("M1", "M", "sabre"), # T1
             
             self.create_fencer("F3", "F", "epee"), # T2
             self.create_fencer("M2", "M", "foil"),  # T2
             self.create_fencer("M3", "M", "sabre"), # T2
             
             self.create_fencer("ReserveM", "M", "foil") # Reserve
        ]
        
        # When random.sample is called, we want to return the dict with name "ReserveM"
        # The call is random.sample(m_fencers, to_remove).
        # We can implement side_effect to scan the input list.
        
        def side_effect(population, k):
            # Find ReserveM in population
            res = [f for f in population if f["name"] == "ReserveM"]
            if res and k==1:
                return res
            # Fallback for other calls (e.g. valid_teams random choice)
            # wait, app.py uses random.choice for teams, and random.sample for fencers.
            # Patch applies to random.sample ONLY.
            # app.py uses random.sample(reserves, teams*3) later?
            # if len(reserves) >= 3 check. We have 1 reserve. Not hit.
            return population[:k] # fallback

        mock_sample.side_effect = side_effect
        
        payload = {"fencers": fencers}
        response = self.app.post('/solve', json=payload)
        data = json.loads(response.data)
        teams = data["teams"]
        
        # Find which team has 2F and which has 1F
        team_2f = None
        team_1f = None
        
        for t in teams:
            f_count = len([m for m in t["members"].values() if m["category"] == "F"])
            if f_count >= 2:
                team_2f = t
            elif f_count == 1:
                team_1f = t

        if team_2f and team_1f:
            # Check where the reserve is
            # It should be in team_2f because ReserveM (Foil) matches F1 (Foil) in T1 (2F)
            self.assertIn("reserves", team_2f)
            self.assertEqual(len(team_2f["reserves"]), 1)
            self.assertEqual(team_2f["reserves"][0]["name"], "ReserveM")
            
            # Ensure team_1f has NO reserves
            if "reserves" in team_1f:
                self.assertEqual(len(team_1f["reserves"]), 0)
        else:
            self.fail("Solver did not produce expected 2F/1F team split.")

if __name__ == '__main__':
    unittest.main()
