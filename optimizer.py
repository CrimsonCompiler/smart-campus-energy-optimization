import pulp
import json

class GridWiseOptimizer:
    def __init__(self, hours_data, battery_data, directives):
        self.hours = hours_data     
        self.battery = battery_data  
        self.directives = directives 

        self.prob = pulp.LpProblem("GridWise_Energy_Optimization", pulp.LpMinimize)
        
        # Decision Variables (for 24 hours)
        self.grid_kwh = [pulp.LpVariable(f"grid_{h}", lowBound=0) for h in range(24)]
        self.solar_used = [pulp.LpVariable(f"solar_{h}", lowBound=0) for h in range(24)]
        self.charge = [pulp.LpVariable(f"charge_{h}", lowBound=0) for h in range(24)]
        self.discharge = [pulp.LpVariable(f"discharge_{h}", lowBound=0) for h in range(24)]
        self.energy_after = [pulp.LpVariable(f"energy_{h}", lowBound=0) for h in range(24)]

    def apply_directives(self):
        """
        Convert directive interpretations into optimization constraints.
        """
        for directive in self.directives:
            if not directive['applies']:
                continue 
                
            d_type = directive['directive_type']
            adj = directive['structured_adjustment']
            hours_list = adj['hours']
            
            if d_type == 'solar_reduction':
                factor = adj['factor']
                for h in hours_list:
                    effective_solar = self.hours[h]['solar_kwh'] * factor
                    self.prob += self.solar_used[h] <= effective_solar, f"Solar_Red_{h}"
                    
            elif d_type == 'no_charge_window':
                for h in hours_list:
                    self.prob += self.charge[h] == 0, f"No_Charge_{h}"
                    
            elif d_type == 'no_discharge_window':
                for h in hours_list:
                    self.prob += self.discharge[h] == 0, f"No_Discharge_{h}"
                    
            elif d_type == 'max_grid_window':
                max_grid = adj['max_grid_kwh']
                for h in hours_list:
                    self.prob += self.grid_kwh[h] <= max_grid, f"Max_Grid_{h}"
                    
            elif d_type == 'minimum_battery_reserve':
                min_reserve = adj['minimum_energy_kwh']
                for h in hours_list:
                    base_min = self.battery['minimum_energy_kwh']
                    effective_min = max(base_min, min_reserve)
                    self.prob += self.energy_after[h] >= effective_min, f"Min_Reserve_{h}"

    def build_constraints(self):
        """
        Energy Balance & Battery Physics constraints.
        """
        prev_energy = self.battery['initial_energy_kwh']
        
        for h in range(24):
            hour_data = self.hours[h]
            
            # 1. Energy Balance: grid + solar + discharge = demand + charge
            self.prob += (self.grid_kwh[h] + self.solar_used[h] + self.discharge[h] == 
                          hour_data['demand_kwh'] + self.charge[h]), f"Balance_{h}"
            
            # 2. Solar Limit (Base limit if no directives apply)
            self.prob += self.solar_used[h] <= hour_data['solar_kwh'], f"Solar_Limit_{h}"
            
            # 3. Battery State Transition
            self.prob += (self.energy_after[h] == prev_energy + self.charge[h] - self.discharge[h]), f"State_{h}"
            
            # 4. Battery Bounds (Capacity & Base Minimum)
            self.prob += self.energy_after[h] <= self.battery['capacity_kwh'], f"Cap_Max_{h}"
            self.prob += self.energy_after[h] >= self.battery['minimum_energy_kwh'], f"Cap_Min_{h}"
            
            # 5. Charge/Discharge Rate Limits
            self.prob += self.charge[h] <= self.battery['max_charge_kwh_per_hour'], f"Rate_Charge_{h}"
            self.prob += self.discharge[h] <= self.battery['max_discharge_kwh_per_hour'], f"Rate_Discharge_{h}"
            
            prev_energy = self.energy_after[h]
            
        # 6. End-of-Day Neutrality
        self.prob += self.energy_after[23] == self.battery['initial_energy_kwh'], "End_of_Day"

    def set_objective(self):
        """
        Objective: Minimize total electricity cost from the grid.
        """
        total_cost = pulp.lpSum([
            self.grid_kwh[h] * self.hours[h]['tariff_bdt_per_kwh'] for h in range(24)
        ])
        self.prob += total_cost, "Total_Cost"

    def solve_and_build_response(self, scenario_id):
        """
        Solve optimization problem and build response dictionary.
        """
        self.build_constraints()
        self.apply_directives()
        self.set_objective()
        
        status = self.prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[status] != 'Optimal':
            raise ValueError("Optimizer failed to find an optimal solution.")
            
        hourly_plan = []
        total_grid = 0
        total_cost = 0
        peak_grid = 0
        
        for h in range(24):
            g = pulp.value(self.grid_kwh[h])
            s = pulp.value(self.solar_used[h])
            c = pulp.value(self.charge[h])
            d = pulp.value(self.discharge[h])
            e = pulp.value(self.energy_after[h])
            
            if c > 0.001: action = "charge"
            elif d > 0.001: action = "discharge"
            else: action = "idle"
            
            b_kwh = c if action == "charge" else (d if action == "discharge" else 0)
            
            hourly_plan.append({
                "hour": h,
                "grid_kwh": round(g, 2),
                "solar_used_kwh": round(s, 2),
                "battery_action": action,
                "battery_kwh": round(b_kwh, 2),
                "battery_energy_after_kwh": round(e, 2)
            })
            
            total_grid += g
            total_cost += g * self.hours[h]['tariff_bdt_per_kwh']
            if g > peak_grid: peak_grid = g

        return {
            "scenario_id": scenario_id,
            "directive_interpretation": self.directives,
            "hourly_plan": hourly_plan,
            "total_grid_kwh": round(total_grid, 2),
            "total_cost_bdt": round(total_cost, 2),
            "peak_grid_kwh": round(peak_grid, 2),
            "plan_summary": "Optimized schedule minimizing grid cost while satisfying all directives and battery constraints."
        }

if __name__ == "__main__":
    dummy_hours = [{"hour": h, "demand_kwh": 100, "solar_kwh": 0, "tariff_bdt_per_kwh": 10} for h in range(24)]
    dummy_battery = {
        "capacity_kwh": 200, "initial_energy_kwh": 100, "minimum_energy_kwh": 20,
        "max_charge_kwh_per_hour": 50, "max_discharge_kwh_per_hour": 50
    }
    dummy_directives = [
        {
            "note_index": 0, "applies": True, "directive_type": "no_charge_window",
            "structured_adjustment": {"hours": [2, 3]}, "explanation": "Maintenance"
        }
    ]
    
    optimizer = GridWiseOptimizer(dummy_hours, dummy_battery, dummy_directives)
    result = optimizer.solve_and_build_response("TEST-01")
    
    print(json.dumps(result, indent=2))