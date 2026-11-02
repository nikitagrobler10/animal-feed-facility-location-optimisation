
## Model Functions ##

## 1.   def old_load_data(path)
## 1.1. def load_master_data(path)
## 1.2. def build_experiment_data(master, plants, suppliers, buyers, materials, feeds, trucks)

## 2.   def build_model(data, objective="cost", emissions_cap=None, cost_cap=None, force_closed=None, force_open=None)

## 3.1. def new_solve_and_extract(mdl, vars_, data, log_output=True)
## 3.2. def old_solve_and_extract(mdl, vars_, data, log_output=True)

## 4.   def old_report(results)

## 5.   def check_utilisation_use(mdl, vars_, data, tol=1e-6)

## 6.1. def pareto_table(data, build_model_func, solve_and_extract_func, cap_min, cap_max, n_points=20, objective="cost", cap_type="emissions")
## 6.2. def plot_pareto(df_pareto)

## 7.1. def load_node_coordinates(coord_file="Node_Coordinates.xlsx")
## 7.2. def aggregate_flows(results)
## 7.2. def get_linewidth(trips, min_trips, max_trips, lw_min=1.0, lw_max=5.0)
## 7.3. def plot_flp_solution(results, coord_file="Node_Coordinates.xlsx", figsize=(10, 8), label_nodes=True, show_title=True)



import pandas as pd
from docplex.mp.model import Model
import matplotlib.pyplot as plt
import numpy as np

## 1. Old Load Model Data ##

def old_load_data(path):
    # ----------------------------
    # 2.1 Define sets
    # ----------------------------
    raw_materials = pd.read_excel(path, sheet_name="Raw Materials")
    feed_types = pd.read_excel(path, sheet_name="Feed Types")
    plants = pd.read_excel(path, sheet_name="Plant Locations")
    suppliers = pd.read_excel(path, sheet_name="Suppliers")
    buyers = pd.read_excel(path, sheet_name="Buyers")
    trucks = pd.read_excel(path, sheet_name="Trucks")
    utilisation = pd.read_excel(path, sheet_name="Utilisation")

    # ----------------------------
    # 2.2 Create sets
    # ----------------------------
    S = suppliers["Variable"].tolist()
    P = plants["Variable"].tolist()
    B = buyers["Variable"].tolist()
    M = raw_materials["Variable"].tolist()
    F = feed_types["Variable"].tolist()
    T = trucks["Variable"].tolist()
    U = utilisation["Variable"].tolist()

    # ----------------------------
    # 4.0 Data Frames
    # ----------------------------
    DF_cost_materials = pd.read_excel(path, sheet_name="Cost Materials", index_col=0)
    DF_cost_transport = pd.read_excel(path, sheet_name="Cost Transport", index_col=0)
    DF_cost_production = pd.read_excel(path, sheet_name="Cost Production", index_col=0)
    DF_cost_plant = pd.read_excel(path, sheet_name="Cost Plant", index_col=0)

    DF_distance_supplier = pd.read_excel(path, sheet_name="Distance Supplier", index_col=0)
    DF_distance_buyer = pd.read_excel(path, sheet_name="Distance Buyer", index_col=0)

    DF_feed_formulation = pd.read_excel(path, sheet_name="Feed Formulation", index_col=0)
    DF_buyer_demand = pd.read_excel(path, sheet_name="Buyer Demand", index_col=0)

    DF_cap_supplier = pd.read_excel(path, sheet_name="Cap Supplier", index_col=0)
    DF_cap_plant = pd.read_excel(path, sheet_name="Cap Plant", index_col=0)
    DF_cap_truck_in = pd.read_excel(path, sheet_name="Cap Truck Inbound", index_col=0)
    DF_cap_truck_out = pd.read_excel(path, sheet_name="Cap Truck Outbound", index_col=0)

    DF_emissions_plant = pd.read_excel(path, sheet_name="Plant Emissions", index_col=0)
    DF_emissions_truck = pd.read_excel(path, sheet_name="Truck Emissions", index_col=0)

    DF_util_lower = pd.read_excel(path, sheet_name="Utilisation Lower Bound", index_col=0)

    DF_scalar_parameters = pd.read_excel(path, sheet_name="Scalar Parameters")

    # ----------------------------
    # 4.1 - 4.12 Parameters
    # ----------------------------
    c_sm = {(s, m): DF_cost_materials.loc[s, m] for s in S for m in M}
    c_t = {t: DF_cost_transport.loc[t, "Cost"] for t in T}
    c_pf = {(p, f): DF_cost_production.loc[p, f] for p in P for f in F}
    c_p = {p: DF_cost_plant.loc[p, "Cost"] for p in P}

    d_ps = {(p, s): DF_distance_supplier.loc[p, s] for p in P for s in S}
    d_pb = {(p, b): DF_distance_buyer.loc[p, b] for p in P for b in B}

    r_fm = {(f, m): DF_feed_formulation.loc[f, m] for f in F for m in M}
    h_bf = {(b, f): DF_buyer_demand.loc[b, f] for b in B for f in F}

    a_sm = {(s, m): DF_cap_supplier.loc[s, m] for s in S for m in M}
    a_tm = {(t, m): DF_cap_truck_in.loc[t, m] for t in T for m in M}
    a_tf = {(t, f): DF_cap_truck_out.loc[t, f] for t in T for f in F}
    a_pf = {(p, f): DF_cap_plant.loc[p, f] for p in P for f in F}

    e_tu = {(t, u): DF_emissions_truck.loc[t, u] for t in T for u in U}
    e_pf = {(p, f): DF_emissions_plant.loc[p, f] for p in P for f in F}

    l_u = {u: DF_util_lower.loc[u, "LowerBound"] for u in U}

    alpha = DF_scalar_parameters.loc[
        DF_scalar_parameters["Parameter"] == "alpha", "Value"
    ].iloc[0]

    data = {
        "S": S, "P": P, "B": B, "M": M, "F": F, "T": T, "U": U,
        "c_sm": c_sm, "c_t": c_t, "c_pf": c_pf, "c_p": c_p,
        "d_ps": d_ps, "d_pb": d_pb,
        "r_fm": r_fm, "h_bf": h_bf, 
        "a_sm": a_sm, "a_tm": a_tm,  "a_tf": a_tf, "a_pf": a_pf,
        "e_tu": e_tu, "e_pf": e_pf, 
        "l_u": l_u,
        "alpha": alpha
    }

    return data



## 1. Load Data

## 1.1. Read Excel Workbook

def load_master_data(path):
    master = {}

    sheet_names = [
        "Raw Materials",
        "Feed Types",
        "Plant Locations",
        "Suppliers",
        "Buyers",
        "Trucks",
        "Utilisation",
        "Cost Materials",
        "Cost Transport",
        "Cost Production",
        "Cost Plant",
        "Distance Supplier",
        "Distance Buyer",
        "Feed Formulation",
        "Buyer Demand",
        "Cap Supplier",
        "Cap Plant",
        "Cap Truck Inbound",
        "Cap Truck Outbound",
        "Plant Emissions",
        "Truck Emissions",
        "Utilisation Lower Bound",
        "Scalar Parameters",
    ]

    for sheet in sheet_names:
        if sheet in [
            "Raw Materials",
            "Feed Types",
            "Plant Locations",
            "Suppliers",
            "Buyers",
            "Trucks",
            "Utilisation",
            "Scalar Parameters",
        ]:
            master[sheet] = pd.read_excel(path, sheet_name=sheet)
        else:
            master[sheet] = pd.read_excel(path, sheet_name=sheet, index_col=0)

    return master

## 1.2. Extract Data 

def build_experiment_data(
    master,
    plants,
    suppliers,
    buyers,
    materials,
    feeds,
    trucks
):
    # Sets
    S = suppliers
    P = plants
    B = buyers
    M = materials
    F = feeds
    T = trucks
    U = master["Utilisation"]["Variable"].tolist()

    # Filter dataframes
    DF_cost_materials = master["Cost Materials"].loc[S, M]
    DF_cost_transport = master["Cost Transport"].loc[T]
    DF_cost_production = master["Cost Production"].loc[P, F]
    DF_cost_plant = master["Cost Plant"].loc[P]

    DF_distance_supplier = master["Distance Supplier"].loc[P, S]
    DF_distance_buyer = master["Distance Buyer"].loc[P, B]

    DF_feed_formulation = master["Feed Formulation"].loc[F, M]
    DF_buyer_demand = master["Buyer Demand"].loc[B, F]

    DF_cap_supplier = master["Cap Supplier"].loc[S, M]
    DF_cap_plant = master["Cap Plant"].loc[P, F]
    DF_cap_truck_in = master["Cap Truck Inbound"].loc[T, M]
    DF_cap_truck_out = master["Cap Truck Outbound"].loc[T, F]

    DF_emissions_plant = master["Plant Emissions"].loc[P, F]
    DF_emissions_truck = master["Truck Emissions"].loc[T, U]

    DF_util_lower = master["Utilisation Lower Bound"].loc[U]

    DF_scalar_parameters = master["Scalar Parameters"]

    # Dictionaries
    c_sm = {(s, m): DF_cost_materials.loc[s, m] for s in S for m in M}
    c_t = {t: DF_cost_transport.loc[t, "Cost"] for t in T}
    c_pf = {(p, f): DF_cost_production.loc[p, f] for p in P for f in F}
    c_p = {p: DF_cost_plant.loc[p, "Cost"] for p in P}

    d_ps = {(p, s): DF_distance_supplier.loc[p, s] for p in P for s in S}
    d_pb = {(p, b): DF_distance_buyer.loc[p, b] for p in P for b in B}

    r_fm = {(f, m): DF_feed_formulation.loc[f, m] for f in F for m in M}
    h_bf = {(b, f): DF_buyer_demand.loc[b, f] for b in B for f in F}

    a_sm = {(s, m): DF_cap_supplier.loc[s, m] for s in S for m in M}
    a_tm = {(t, m): DF_cap_truck_in.loc[t, m] for t in T for m in M}
    a_tf = {(t, f): DF_cap_truck_out.loc[t, f] for t in T for f in F}
    a_pf = {(p, f): DF_cap_plant.loc[p, f] for p in P for f in F}

    e_tu = {(t, u): DF_emissions_truck.loc[t, u] for t in T for u in U}
    e_pf = {(p, f): DF_emissions_plant.loc[p, f] for p in P for f in F}

    l_u = {u: DF_util_lower.loc[u, "LowerBound"] for u in U}

    alpha = DF_scalar_parameters.loc[
        DF_scalar_parameters["Parameter"] == "alpha", "Value"
    ].iloc[0]

    data = {
        "S": S, "P": P, "B": B, "M": M, "F": F, "T": T, "U": U,
        "c_sm": c_sm, "c_t": c_t, "c_pf": c_pf, "c_p": c_p,
        "d_ps": d_ps, "d_pb": d_pb,
        "r_fm": r_fm, "h_bf": h_bf,
        "a_sm": a_sm, "a_tm": a_tm, "a_tf": a_tf, "a_pf": a_pf,
        "e_tu": e_tu, "e_pf": e_pf,
        "l_u": l_u,
        "alpha": alpha
    }

    return data


## 2. Optimisation Model ##

def build_model(
    data,
    objective="cost",
    emissions_cap=None,
    cost_cap=None,
    force_closed=None,
    force_open=None
):
    
    if force_closed is None:
        force_closed = []
    if force_open is None:
        force_open = []

    # ----------------------------
    # 2. Sets
    # ----------------------------
    S = data["S"]
    P = data["P"]
    B = data["B"]
    M = data["M"]
    F = data["F"]
    T = data["T"]
    U = data["U"]

    # ----------------------------
    # 4. Parameters
    # ----------------------------
    c_sm = data["c_sm"]
    c_t = data["c_t"]
    c_pf = data["c_pf"]
    c_p  = data["c_p"]

    d_ps = data["d_ps"]
    d_pb = data["d_pb"]

    r_fm = data["r_fm"]
    h_bf = data["h_bf"]
    
    a_sm = data["a_sm"]
    a_pf = data["a_pf"]
    a_tm = data["a_tm"]
    a_tf = data["a_tf"]

    e_tu = data["e_tu"]
    e_pf = data["e_pf"]
    
    l_u = data["l_u"]
    alpha = data["alpha"]

    mdl = Model(name="feed_plant_location")


    # ----------------------------
    # 6. Decision variables
    # ----------------------------

    # 6.1 Inbound Raw Material [tonne] 
    x = mdl.continuous_var_dict(
        ((s, p, m, t, u) for s in S for p in P for m in M for t in T for u in U),
        lb=0,
        name="x"
    )

    #6.2 Outbound Feed [tonne]
    y = mdl.continuous_var_dict(
        ((p, b, f, t, u) for p in P for b in B for f in F for t in T for u in U),
        lb=0,
        name="y"
    )

    # 6.3 Inbound trips
    n_in = mdl.integer_var_dict(
        ((s, p, m, t, u) for s in S for p in P for m in M for t in T for u in U),
        lb=0,
        name="n_in"
    )

    # 6.4 Outbound trips
    n_out = mdl.integer_var_dict(
        ((p, b, f, t, u) for p in P for b in B for f in F for t in T for u in U),
        lb=0,
        name="n_out"
    )

    #6.5 Production
    z = mdl.continuous_var_dict(
        ((p, f) for p in P for f in F),
        lb=0,
        name="z"
    )

    # Plant Opening 
    q = mdl.binary_var_dict(P, name="q")

    # ----------------------------
    # 7. Constraints
    # ----------------------------

    # 7.1. Buyer demand satisfaction
    for b in B:
        for f in F:
            mdl.add_constraint(
                mdl.sum(y[p, b, f, t, u] for p in P for t in T for u in U) == h_bf[(b, f)],
                ctname=f"demand_{b}_{f}"
            )

    # 7.2. Production balance
    for p in P:
        for f in F:
            mdl.add_constraint(
                mdl.sum(y[p, b, f, t, u] for b in B for t in T for u in U) == z[(p, f)],
                ctname=f"prod_balance_{p}_{f}"
            )

    # 7.3. Feed formulation constraint
    for p in P:
        for m in M:
            mdl.add_constraint(
                mdl.sum(x[s, p, m, t, u] for s in S for t in T for u in U)
                == mdl.sum(r_fm[(f, m)] * z[(p, f)] for f in F),
                ctname=f"mat_balance_{p}_{m}"
            )

    # 7.4. Supplier capacity
    for s in S:
        for m in M:
            mdl.add_constraint(
                mdl.sum(x[s, p, m, t, u] for p in P for t in T for u in U) <= a_sm[(s, m)],
                ctname=f"supplier_cap_{s}_{m}"
            )

    # 7.5 Inbound truck capacity
    for s in S:
        for p in P:
            for m in M:
                for t in T:
                    for u in U:
                        mdl.add_constraint(
                            x[s, p, m, t, u] <= a_tm[t, m] * u * n_in[s, p, m, t, u],
                            ctname=f"in_trip_link_{s}_{p}_{m}_{t}_{u}"
                        )

                        mdl.add_constraint(
                            x[s, p, m, t, u] >= a_tm[t, m] * l_u[u] * n_in[s, p, m, t, u],
                            ctname=f"in_trip_lower_{s}_{p}_{m}_{t}_{u}"
                        )
                    
    # 7.6 Outbound truck-capacity linking
    for p in P:
        for b in B:
            for f in F:
                for t in T:
                    for u in U:
                        mdl.add_constraint(
                            y[p, b, f, t, u] <= a_tf[t, f] * u * n_out[p, b, f, t, u],
                            ctname=f"out_trip_link_{p}_{b}_{f}_{t}_{u}"
                        )

                        mdl.add_constraint(
                            y[p, b, f, t, u] >= a_tf[t, f] * l_u[u] * n_out[p, b, f, t, u],
                            ctname=f"out_trip_lower_{p}_{b}_{f}_{t}_{u}"
                        )

    # 7.7. Plant capacity
    for p in P:
        for f in F:
            mdl.add_constraint(
                z[(p, f)] <= a_pf[(p, f)] * q[p],
                ctname=f"plant_cap_{p}_{f}"
            )

    # 7.8. Plant activation (alpha)
    for p in P:
        mdl.add_constraint(
            mdl.sum(z[p, f] for f in F) >= alpha * q[p],
            ctname=f"plant_activation_{p}"
        )
    
    # Forced OPEN & CLOSE 
    for p in force_closed:
        mdl.add_constraint(q[p] == 0, ctname=f"force_closed_{p}")

    for p in force_open:
        mdl.add_constraint(q[p] == 1, ctname=f"force_open_{p}")

    # ----------------------------
    # 8. Objectives
    # ----------------------------

    # 8.1. Cost 

    raw_material_cost = mdl.sum(
        c_sm[(s, m)] * x[s, p, m, t, u]
        for s in S for p in P for m in M for t in T for u in U
    )

    inbound_transport_cost = mdl.sum(
        c_t[t] * d_ps[(p, s)] * n_in[s, p, m, t, u]
        for s in S for p in P for m in M for t in T for u in U
    )

    production_cost = mdl.sum(
        c_pf[(p, f)] * z[(p, f)]
        for p in P for f in F
    )

    plant_opening_cost = mdl.sum(
        c_p[p] * q[p]
        for p in P
    )

    outbound_transport_cost = mdl.sum(
        c_t[t] * d_pb[(p, b)] * n_out[p, b, f, t, u]
        for p in P for b in B for f in F for t in T for u in U
    )

    total_cost = (
        raw_material_cost
        + inbound_transport_cost
        + production_cost
        + plant_opening_cost
        + outbound_transport_cost
    )

    # 8.2. Emissions

    inbound_emissions = mdl.sum(
        e_tu[(t, u)] * d_ps[(p, s)] * x[s, p, m, t, u]
        for s in S for p in P for m in M for t in T for u in U
    )

    plant_emissions = mdl.sum(
        e_pf[(p, f)] * z[(p, f)]
        for p in P for f in F
    )

    outbound_emissions = mdl.sum(
        e_tu[(t, u)] * d_pb[(p, b)] * y[p, b, f, t, u]
        for p in P for b in B for f in F for t in T for u in U
    )

    total_emissions = (
        inbound_emissions
        + plant_emissions
        + outbound_emissions
    )

    # Objective selection for epsilon-constraint method
    
    if emissions_cap is not None:
        mdl.add_constraint(total_emissions <= emissions_cap, ctname="emissions_cap")

    if cost_cap is not None:
        mdl.add_constraint(total_cost <= cost_cap, ctname="cost_cap")

    if objective == "cost":
        mdl.minimize(total_cost)
    elif objective == "emissions":
        mdl.minimize(total_emissions)
    else:
        raise ValueError("objective must be 'cost' or 'emissions'")

    vars_ = {
        "x": x,
        "y": y,
        "z": z,
        "q": q,
        "n_in": n_in,
        "n_out": n_out,
        "total_cost": total_cost,
        "total_emissions": total_emissions
    }

    return mdl, vars_


## 3. Solve Model ##

def solve_and_extract(mdl, vars_, data, log_output=True):

    solution = mdl.solve(log_output=log_output)

    if solution is None:
        print("No feasible solution found.")
        return None

    # Sets
    S = data["S"]
    P = data["P"]
    B = data["B"]
    M = data["M"]
    F = data["F"]
    T = data["T"]
    U = data["U"]

    # Parameters
    c_sm = data["c_sm"]
    c_t = data["c_t"]
    c_pf = data["c_pf"]
    c_p = data["c_p"]

    d_ps = data["d_ps"]
    d_pb = data["d_pb"]

    e_tu = data["e_tu"]
    e_pf = data["e_pf"]

    # Variables
    x = vars_["x"]
    y = vars_["y"]
    z = vars_["z"]
    q = vars_["q"]
    n_in = vars_["n_in"]
    n_out = vars_["n_out"]

    total_cost = vars_["total_cost"]
    total_emissions = vars_["total_emissions"]

    tol = 1e-6

    # ----------------------------
    # Basic solution information
    # ----------------------------
    open_plants = [p for p in P if q[p].solution_value > 0.5]

    production = {}
    for p in P:
        for f in F:
            val = z[p, f].solution_value
            if val > tol:
                production[(p, f)] = val

    # ----------------------------
    # Flows
    # ----------------------------
    inbound_flows = {}
    for s in S:
        for p in P:
            for m in M:
                val = sum(
                    x[s, p, m, t, u].solution_value
                    for t in T for u in U
                )
                if val > tol:
                    inbound_flows[(s, p, m)] = val

    outbound_flows = {}
    for p in P:
        for b in B:
            for f in F:
                val = sum(
                    y[p, b, f, t, u].solution_value
                    for t in T for u in U
                )
                if val > tol:
                    outbound_flows[(p, b, f)] = val

    # ----------------------------
    # Trips
    # ----------------------------
    inbound_trips = {}
    for s in S:
        for p in P:
            for m in M:
                for t in T:
                    for u in U:
                        val = n_in[s, p, m, t, u].solution_value
                        if val > tol:
                            inbound_trips[(s, p, m, t, u)] = val

    outbound_trips = {}
    for p in P:
        for b in B:
            for f in F:
                for t in T:
                    for u in U:
                        val = n_out[p, b, f, t, u].solution_value
                        if val > tol:
                            outbound_trips[(p, b, f, t, u)] = val

    # ----------------------------
    # Cost breakdown
    # ----------------------------
    raw_material_cost = sum(
        c_sm[(s, m)] * x[s, p, m, t, u].solution_value
        for s in S for p in P for m in M for t in T for u in U
    )

    inbound_transport_cost = sum(
        c_t[t] * d_ps[(p, s)] * n_in[s, p, m, t, u].solution_value
        for s in S for p in P for m in M for t in T for u in U
    )

    production_cost = sum(
        c_pf[(p, f)] * z[p, f].solution_value
        for p in P for f in F
    )

    plant_opening_cost = sum(
        c_p[p] * q[p].solution_value
        for p in P
    )

    outbound_transport_cost = sum(
        c_t[t] * d_pb[(p, b)] * n_out[p, b, f, t, u].solution_value
        for p in P for b in B for f in F for t in T for u in U
    )

    # ----------------------------
    # Emissions breakdown
    # ----------------------------
    inbound_emissions = sum(
        e_tu[(t, u)] * d_ps[(p, s)] * x[s, p, m, t, u].solution_value
        for s in S for p in P for m in M for t in T for u in U
    )

    plant_emissions = sum(
        e_pf[(p, f)] * z[p, f].solution_value
        for p in P for f in F
    )

    outbound_emissions = sum(
        e_tu[(t, u)] * d_pb[(p, b)] * y[p, b, f, t, u].solution_value
        for p in P for b in B for f in F for t in T for u in U
    )

    # ----------------------------
    # Results dictionary
    # ----------------------------
    results = {
        "objective_value": round(mdl.objective_value, 2),

        "total_cost": round(total_cost.solution_value, 2),
        "total_emissions": round(total_emissions.solution_value, 2),

        "open_plants": open_plants,
        "production": production,

        "inbound_flows": inbound_flows,
        "outbound_flows": outbound_flows,

        "inbound_trips": inbound_trips,
        "outbound_trips": outbound_trips,

        "cost_breakdown": {
            "raw_material_cost": round(raw_material_cost, 2),
            "inbound_transport_cost": round(inbound_transport_cost, 2),
            "production_cost": round(production_cost, 2),
            "plant_opening_cost": round(plant_opening_cost, 2),
            "outbound_transport_cost": round(outbound_transport_cost, 2),
        },

        "emissions_breakdown": {
            "inbound_emissions": round(inbound_emissions, 2),
            "plant_emissions": round(plant_emissions, 2),
            "outbound_emissions": round(outbound_emissions, 2),
        }
    }

    return results



    
def old_solve_and_extract(mdl, vars_, data, log_output=True):
    
    solution = mdl.solve(log_output=log_output)

    if solution is None:
        print("No feasible solution found.")
        return None

    q = vars_["q"]
    z = vars_["z"]

    n_in = vars_["n_in"]
    n_out = vars_["n_out"]
    S = data["S"]
    B = data["B"]
    T = data["T"]
    U = data["U"]
    M = data["M"]

    total_cost = vars_["total_cost"]
    total_emissions = vars_["total_emissions"]
    P = data["P"]
    F = data["F"]

    open_plants = [p for p in P if q[p].solution_value > 0.5]

    production = {}
    for p in P:
        for f in F:
            val = z[p, f].solution_value
            if val > 1e-6:
                production[(p, f)] = val

    inbound_trips = {}
    for s in S:
        for p in P:
            for m in M:
                for t in T:
                    for u in U:
                        val = n_in[s, p, m, t, u].solution_value
                        if val > 1e-6:
                            inbound_trips[(s, p, m, t, u)] = val

    outbound_trips = {}
    for p in P:
        for b in B:
            for f in F:
                for t in T:
                    for u in U:
                        val = n_out[p, b, f, t, u].solution_value
                        if val > 1e-6:
                            outbound_trips[(p, b, f, t, u)] = val



    results = {
        "objective_value": round(mdl.objective_value, 2),
        "total_cost": round(total_cost.solution_value, 2),
        "total_emissions": round(total_emissions.solution_value, 2),
        "open_plants": open_plants,
        "production": production,
        "inbound_trips": inbound_trips,
        "outbound_trips": outbound_trips,
    }

    return results



## 4. Report Results ##


def report(results):
    if results is None:
        print("No feasible solution found.")
        return

    print("\n=== Optimal Solution ===")
    print(f"Objective value : {results['objective_value']:.2f}")
    print(f"Cost            : {results['total_cost']:.2f}")
    print(f"Emissions       : {results['total_emissions']:.2f}")
    print(f"Plants          : {', '.join(results['open_plants'])}")

    print("\nProduction:")
    for (p, f), val in results["production"].items():
        print(f"{p} - {f}: {val:.2f}")

    print("\nInbound trips:")
    for (s, p, m, t, u), val in results["inbound_trips"].items():
        print(f"{s} -> {p} | {m} | {t} | util {u}: {val:.0f}")

    print("\nOutbound trips:")
    for (p, b, f, t, u), val in results["outbound_trips"].items():
        print(f"{p} -> {b} | {f} | {t} | util {u}: {val:.0f}")

## 5. Utilisation Check ##

def check_utilisation_use(mdl, vars_, data, tol=1e-6):
    x = vars_["x"]
    y = vars_["y"]
    n_in = vars_["n_in"]
    n_out = vars_["n_out"]

    S = data["S"]
    P = data["P"]
    B = data["B"]
    M = data["M"]
    F = data["F"]
    T = data["T"]
    U = data["U"]

    a_tm = data["a_tm"]   
    a_tf = data["a_tf"]   

    l_u = data["l_u"]  
    
    print("\n=== Inbound utilisation check ===")
    for s in S:
        for p in P:
            for m in M:
                for t in T:
                    for u in U:
                        trips = n_in[s, p, m, t, u].solution_value
                        if trips > tol:
                            flow = x[s, p, m, t, u].solution_value
                            capacity = a_tm[(t, m)] * trips
                            realised_util = flow / capacity if capacity > tol else 0

                            print(
                                f"{s} -> {p} | {m} | {t} | chosen u={u} | "
                                f"lower={l_u[u]} | trips={trips:.0f} | "
                                f"flow={flow:.2f} | realised util={realised_util:.2f}"
                            )

    print("\n=== Outbound utilisation check ===")
    for p in P:
        for b in B:
            for f in F:
                for t in T:
                    for u in U:
                        trips = n_out[p, b, f, t, u].solution_value
                        if trips > tol:
                            flow = y[p, b, f, t, u].solution_value
                            capacity = a_tf[(t, f)] * trips
                            realised_util = flow / capacity if capacity > tol else 0

                            print(
                                f"{p} -> {b} | {f} | {t} | chosen u={u} | "
                                f"lower={l_u[u]} | trips={trips:.0f} | "
                                f"flow={flow:.2f} | realised util={realised_util:.2f}"
                            )


## Pareto ##

## 6.1. Pareto Table ##

def pareto_table(
    data,
    build_model_func,
    solve_and_extract_func,
    cap_min,
    cap_max,
    n_points=20,
    objective="cost",
    cap_type="emissions"   # "emissions" OR "cost"
):
    import pandas as pd
    import numpy as np

    caps = list(np.linspace(cap_max, cap_min, n_points).round(2))
    pareto_results = []

    for cap in caps:

        # decide which cap to apply
        if cap_type == "emissions":
            mdl, vars_ = build_model_func(
                data,
                objective=objective,
                emissions_cap=cap
            )
        elif cap_type == "cost":
            mdl, vars_ = build_model_func(
                data,
                objective=objective,
                cost_cap=cap
            )
        else:
            raise ValueError("cap_type must be 'emissions' or 'cost'")

        res = solve_and_extract_func(mdl, vars_, data, log_output=False)

        if res is not None:
            pareto_results.append({
                "constraint_cap": cap,
                "cost": res["total_cost"],
                "emissions": res["total_emissions"],
                "objective_value": res["objective_value"],
                "plants": ", ".join(res["open_plants"])
            })

    return pd.DataFrame(pareto_results)


## 6.2. Pareto Graph Plotting ##

def plot_pareto(df_pareto):

    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.family": "serif",
        "mathtext.fontset": "cm",
        "font.size": 11
    })

    emissions_m = df_pareto["emissions"] / 1_000_000
    cost_m = df_pareto["cost"] / 1_000_000

    plt.figure(figsize=(8,5))

    plt.grid(True)

    plt.scatter(
        emissions_m,
        cost_m,
        s=35
    )

    plt.xlabel(r"Total emissions [million kg CO$_2$]")
    plt.ylabel(r"Total cost [million R]")
    plt.title(r"Cost-Emissions Pareto frontier")

    plt.tight_layout()
    plt.show()


## 7. Visualization ##

## 7.1. Load Coordinates Data ##

def load_node_coordinates(coord_file="Node_Coordinates.xlsx"):
    
    sheet_map = {
        "Supplier Coordinates": "supplier",
        "Plant Coordinates": "plant",
        "Buyer Coordinates": "buyer",
    }

    frames = []

    for sheet_name, expected_type in sheet_map.items():
        df = pd.read_excel(coord_file, sheet_name=sheet_name)

        if df.empty:
            continue

        df.columns = [c.strip() for c in df.columns]

        required_cols = [
            "node_id",
            "latitude",
            "longitude",
            "plot_color_hex",
            "plot_marker",
        ]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(
                f"Sheet '{sheet_name}' is missing required columns: {missing}"
            )

        if "node_type" not in df.columns:
            df["node_type"] = expected_type

        df["node_type"] = df["node_type"].astype(str).str.strip().str.lower()
        df["node_id"] = df["node_id"].astype(str).str.strip()

        frames.append(df)

    if not frames:
        raise ValueError("No node coordinate data found in the workbook.")

    nodes = pd.concat(frames, ignore_index=True)

    # Use longitude on x-axis and latitude on y-axis
    nodes["x"] = nodes["longitude"]
    nodes["y"] = nodes["latitude"]

    return nodes

## 7.2. Node Flows (aggregated & linewidth) ##

def aggregate_flows(results):
    
    inbound_agg = {}
    outbound_agg = {}

    active_suppliers = set()
    active_plants = set(results.get("open_plants", []))

    # Inbound trips: keys are (s, p, m, t, u)
    for (s, p, m, t, u), trips in results.get("inbound_trips", {}).items():
        if trips > 0:
            inbound_agg[(s, p)] = inbound_agg.get((s, p), 0) + trips
            active_suppliers.add(s)
            active_plants.add(p)

    # Outbound trips: keys are (p, b, f, t, u)
    for (p, b, f, t, u), trips in results.get("outbound_trips", {}).items():
        if trips > 0:
            outbound_agg[(p, b)] = outbound_agg.get((p, b), 0) + trips
            active_plants.add(p)

    return inbound_agg, outbound_agg, active_suppliers, active_plants


def get_linewidth(trips, min_trips, max_trips, lw_min=1.0, lw_max=5.0):
    """
    Scale line thickness based on aggregated trips.
    """
    if max_trips == min_trips:
        return (lw_min + lw_max) / 2
    return lw_min + (trips - min_trips) / (max_trips - min_trips) * (lw_max - lw_min)

## 7.3. Plotting ##

def new_plot_flp_solution(
    results,
    coord_file="Node_Coordinates.xlsx",
    figsize=(15, 13),
    label_nodes=True,
    show_title=True,
    show_legend=True,
):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter

    nodes = load_node_coordinates(coord_file)

    inbound_agg, outbound_agg, active_suppliers, active_plants = aggregate_flows(results)

    node_lookup = nodes.set_index("node_id")[
        ["x", "y", "node_type", "plot_marker"]
    ].to_dict("index")

    fig, ax = plt.subplots(figsize=figsize)

    # ----------------------------
    # Flow scaling
    # ----------------------------
    all_flow_values = list(inbound_agg.values()) + list(outbound_agg.values())

    if all_flow_values:
        min_trips = min(all_flow_values)
        max_trips = max(all_flow_values)
    else:
        min_trips = max_trips = 0

    # ----------------------------
    # Inbound flows: suppliers -> plants
    # ----------------------------
    for (s, p), trips in inbound_agg.items():
        if s not in node_lookup or p not in node_lookup:
            continue

        x1, y1 = node_lookup[s]["x"], node_lookup[s]["y"]
        x2, y2 = node_lookup[p]["x"], node_lookup[p]["y"]

        lw = get_linewidth(trips, min_trips, max_trips)

        ax.plot(
            [x1, x2],
            [y1, y2],
            linestyle="-",
            linewidth=lw,
            color="green",
            alpha=0.75,
            zorder=1,
        )

    # ----------------------------
    # Outbound flows: plants -> buyers
    # ----------------------------
    for (p, b), trips in outbound_agg.items():
        if p not in node_lookup or b not in node_lookup:
            continue

        x1, y1 = node_lookup[p]["x"], node_lookup[p]["y"]
        x2, y2 = node_lookup[b]["x"], node_lookup[b]["y"]

        lw = get_linewidth(trips, min_trips, max_trips)

        ax.plot(
            [x1, x2],
            [y1, y2],
            linestyle="-",
            linewidth=lw,
            color="red",
            alpha=0.75,
            zorder=1,
        )
    
    # ----------------------------
    # Nodes
    # Show all suppliers and plants,
    # but only buyers that receive flow.
    # Plants are plotted last so they get visual preference.
    # ----------------------------
    active_buyers = {b for (p, b) in outbound_agg.keys()}

    # Plot order matters:
    # suppliers first, buyers second, plants last
    plot_order = {"supplier": 1, "buyer": 2, "plant": 3}
    nodes_plot = nodes.copy()
    nodes_plot["plot_order"] = nodes_plot["node_type"].map(plot_order)
    nodes_plot = nodes_plot.sort_values("plot_order")

    for _, row in nodes_plot.iterrows():
        node_id = row["node_id"]
        node_type = row["node_type"]

        # Skip unused buyers only
        if node_type == "buyer" and node_id not in active_buyers:
            continue

        x = row["x"]
        y = row["y"]

        if node_type == "supplier":
            color = "lightgreen" if node_id in active_suppliers else "lightgrey"
            marker = "o"
            z = 3

        elif node_type == "buyer":
            color = "mistyrose"
            marker = "o"
            z = 4

        elif node_type == "plant":
            color = "lightskyblue" if node_id in active_plants else "lightgrey"
            marker = "s"
            z = 6   # plants on top

        else:
            color = "white"
            marker = "o"
            z = 3

        ax.scatter(
            x,
            y,
            s=900,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=1.2,
            zorder=z,
        )

        if label_nodes:
            ax.text(
                x,
                y,
                node_id,
                fontsize=11,
                ha="center",
                va="center",
                zorder=z + 1,
            )

    # ----------------------------
    # Title
    # ----------------------------
    if show_title:
        cost_million = results["total_cost"] / 1e6
        emissions_tonnes = results["total_emissions"]

        objective_text = (
            "Minimise Cost"
            if abs(results["objective_value"] - results["total_cost"]) < 1e-6
            else "Minimise Emissions"
        )

        ax.set_title(
            f"Objective: {objective_text}\n"
            f"Cost = R{cost_million:.2f} million | "
            f"Emissions = {emissions_tonnes:,.0f} t CO$_2$",
            fontsize=14,
            pad=20,
            fontfamily="serif",
        )

    # ----------------------------
    # SA map-style formatting
    # ----------------------------
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.0f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f"{x:.0f}"))

    ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.5)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # ----------------------------
    # Legend
    # ----------------------------
    if show_legend:
        legend_items = [
            Line2D([0], [0], marker="o", color="w", label="Active supplier",
                   markerfacecolor="lightgreen", markeredgecolor="black", markersize=12),
            Line2D([0], [0], marker="o", color="w", label="Inactive supplier",
                   markerfacecolor="lightgrey", markeredgecolor="black", markersize=12),
            Line2D([0], [0], marker="s", color="w", label="Active plant",
                   markerfacecolor="lightskyblue", markeredgecolor="black", markersize=12),
            Line2D([0], [0], marker="s", color="w", label="Inactive plant",
                   markerfacecolor="lightgrey", markeredgecolor="black", markersize=12),
            Line2D([0], [0], marker="o", color="w", label="Buyer",
                   markerfacecolor="mistyrose", markeredgecolor="black", markersize=12),
            Line2D([0], [0], color="green", lw=2, linestyle="-", label="Inbound flow"),
            Line2D([0], [0], color="red", lw=2, linestyle="-", label="Outbound flow"),
        ]

        ax.legend(handles=legend_items, loc="upper left", bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.show()

#no links

def plot_network_locations(
    coord_file="Node_Coordinates.xlsx",
    figsize=(12, 10),
    label_nodes=True,
    show_title=True,
    show_legend=True,
):
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import FuncFormatter

    nodes = load_node_coordinates(coord_file)

    fig, ax = plt.subplots(figsize=figsize)

    plot_order = {"supplier": 1, "buyer": 2, "plant": 3}
    nodes_plot = nodes.copy()
    nodes_plot["plot_order"] = nodes_plot["node_type"].map(plot_order)
    nodes_plot = nodes_plot.sort_values("plot_order")

    for _, row in nodes_plot.iterrows():
        node_id = row["node_id"]
        node_type = row["node_type"]

        x = row["x"]
        y = row["y"]

        if node_type == "supplier":
            color = "lightgreen"
            marker = "o"
            z = 3

        elif node_type == "buyer":
            color = "mistyrose"
            marker = "o"
            z = 4

        elif node_type == "plant":
            color = "lightskyblue"
            marker = "s"
            z = 5

        else:
            color = "white"
            marker = "o"
            z = 2

        ax.scatter(
            x,
            y,
            s=700,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=1.2,
            zorder=z,
        )

        if label_nodes:
            ax.text(
                x,
                y,
                node_id,
                fontsize=10,
                ha="center",
                va="center",
                zorder=z + 1,
            )

    if show_title:
        ax.set_title(
            "Geographical Distribution of Suppliers, Candidate Plants, and Buyers",
            fontsize=14,
            pad=15,
            fontfamily="serif",
        )

    # Clean thesis figure appearance
    ax.set_aspect("equal", adjustable="datalim")

    # Remove axes completely
    ax.axis("off")


    if show_legend:
        legend_items = [
            Line2D([0], [0], marker="o", color="w", label="Supplier",
                   markerfacecolor="lightgreen", markeredgecolor="black", markersize=12),
            Line2D([0], [0], marker="s", color="w", label="Candidate plant",
                   markerfacecolor="lightskyblue", markeredgecolor="black", markersize=12),
            Line2D([0], [0], marker="o", color="w", label="Buyer",
                   markerfacecolor="mistyrose", markeredgecolor="black", markersize=12),
        ]

        ax.legend(handles=legend_items, loc="upper left", bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.show()








def plot_flp_solution(
    results,
    coord_file="Node_Coordinates.xlsx",
    figsize=(10, 8),
    label_nodes=True,
    show_title=True,
):

    nodes = load_node_coordinates(coord_file)
    inbound_agg, outbound_agg, active_suppliers, active_plants = aggregate_flows(results)

    node_lookup = nodes.set_index("node_id")[["x", "y", "node_type", "plot_color_hex", "plot_marker"]].to_dict("index")

    fig, ax = plt.subplots(figsize=figsize)

    # Plot flows (under nodes)
    
    all_flow_values = list(inbound_agg.values()) + list(outbound_agg.values())
    if all_flow_values:
        min_trips = min(all_flow_values)
        max_trips = max(all_flow_values)
    else:
        min_trips = max_trips = 0

    # Inbound trips
    for (s, p), trips in inbound_agg.items():
        if s not in node_lookup or p not in node_lookup:
            continue

        x1, y1 = node_lookup[s]["x"], node_lookup[s]["y"]
        x2, y2 = node_lookup[p]["x"], node_lookup[p]["y"]
        lw = get_linewidth(trips, min_trips, max_trips)

        ax.plot(
            [x1, x2],
            [y1, y2],
            linestyle="--",
            linewidth=lw,
            color="green",
            alpha=0.8,
            zorder=1,
        )

    # Outbound trips 
    for (p, b), trips in outbound_agg.items():
        if p not in node_lookup or b not in node_lookup:
            continue

        x1, y1 = node_lookup[p]["x"], node_lookup[p]["y"]
        x2, y2 = node_lookup[b]["x"], node_lookup[b]["y"]
        lw = get_linewidth(trips, min_trips, max_trips)

        ax.plot(
            [x1, x2],
            [y1, y2],
            linestyle="-",
            linewidth=lw,
            color="red",
            alpha=0.8,
            zorder=1,
        )
  
    # Plot nodes
  
    for _, row in nodes.iterrows():
        node_id = row["node_id"]
        node_type = row["node_type"]

        x = row["x"]
        y = row["y"]
        marker = row["plot_marker"]

        if node_type == "supplier":
            color = row["plot_color_hex"] if node_id in active_suppliers else "grey"
        elif node_type == "plant":
            color = row["plot_color_hex"] if node_id in active_plants else "grey"
        elif node_type == "buyer":
            color = row["plot_color_hex"]   # buyers always red
        else:
            color = "black"

        ax.scatter(
            x,
            y,
            s=120,
            c=color,
            marker=marker,
            edgecolors="black",
            linewidths=0.8,
            zorder=3,
        )

        if label_nodes:
            ax.text(
                x + 0.12,
                y + 0.12,
                node_id,
                fontsize=9,
                zorder=4,
            )

   
    # Labels & Formatting
    
    ax.set_xlabel("Longitude ($^\circ$)")
    ax.set_ylabel("Latitude ($^\circ$)")

    from matplotlib.ticker import FuncFormatter

    ax.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: f"{x:.0f}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, pos: f"{y:.0f}"))

    if show_title:
        cost_million = results["total_cost"] / 1e6
        emissions_tonnes = results["total_emissions"]

        objective_text = "Minimise Cost" if results["objective_value"] == results["total_cost"] else "Minimise Emissions"

        ax.set_title(
            f"Objective: {objective_text}\n"
            f"Cost = R{cost_million:.2f} million | "
            f"Emissions = {emissions_tonnes:,.0f} t CO$_2$"
)

    ax.grid(True, linestyle=":", alpha=0.5)
    ax.set_aspect("equal", adjustable="datalim")

    ax.tick_params(labelsize=10)

    ax.text(
        x + 0.1,
        y + 0.1,
        node_id,
        fontsize=9,
)
    
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

       
    # Custom legend
    
    legend_items = [
        Line2D([0], [0], marker="o", color="w", label="Active supplier",
               markerfacecolor="green", markeredgecolor="black", markersize=9),
        Line2D([0], [0], marker="o", color="w", label="Inactive supplier",
               markerfacecolor="grey", markeredgecolor="black", markersize=9),
        Line2D([0], [0], marker="s", color="w", label="Active plant",
               markerfacecolor="blue", markeredgecolor="black", markersize=9),
        Line2D([0], [0], marker="s", color="w", label="Inactive plant",
               markerfacecolor="grey", markeredgecolor="black", markersize=9),
        Line2D([0], [0], marker="o", color="w", label="Buyer",
               markerfacecolor="red", markeredgecolor="black", markersize=9),
        Line2D([0], [0], color="green", lw=2, linestyle="--", label="Inbound flow"),
        Line2D([0], [0], color="red", lw=2, linestyle="-", label="Outbound flow"),
    ]
    #ax.legend(handles=legend_items, loc="best")
    ax.legend(handles=legend_items, loc="upper left", bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.show()