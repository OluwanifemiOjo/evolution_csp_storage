import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the provided CSV file
csp_output = pd.read_csv("cspoutputandload.csv")
tes_lossfactor = 0.16
pipe_lossfactor = 0.05


# Initialize packed bed storage capacity and tracking variables
pbs_storage = 0  # Initial storage in GJ
pbs_efficiency = 0.80  # Efficiency of the packed bed system
pbs_capacity = []  # Storage level over time
actual_demand = []  # Track actual energy demand over time
pbs_charge = []  # Energy stored in the packed bed
pbs_discharge = []  # Energy withdrawn from the packed bed (now negative)
load_not_satisfied = []  # Energy demand not met
tes_losses = []
pipe_losses = []

# Iterate over the thermal power generated and the total demand
for energy_GJ, total_demand in zip(csp_output["Energy in GJ_June"], csp_output["Demand"]):
    # Store actual demand
    actual_demand.append(total_demand)

    if energy_GJ > total_demand:
        # Excess energy available for storage
        excess_heat = energy_GJ - total_demand
        pbs_storage += excess_heat
        pbs_charge.append(excess_heat)  # Track charging
        pbs_discharge.append(0)  # No discharge
        load_not_satisfied.append(0)  # All load is met
        tes_losses.append(0)
        pipe_losses.append(0)

    else:
        # Energy deficit - draw from storage if available
        load_deficit = total_demand - energy_GJ  # Corrected load deficit calculation
        if pbs_storage > 0:
            #applying TES losses 
            energy_from_pbs = pbs_storage * pbs_efficiency 
            tes_loss = energy_from_pbs*tes_lossfactor
            pipe_loss = energy_from_pbs*pipe_lossfactor
            effective_energy_from_pbs = min(energy_from_pbs - tes_loss-pipe_loss, load_deficit) # only the required energy (up to the load deficit) is withdrawn from storage
            
            pbs_storage -= effective_energy_from_pbs / pbs_efficiency
            pbs_charge.append(0)  # Nothing is stored at this condition of load deficit when CSP cannot supply 
            pbs_discharge.append(-effective_energy_from_pbs)  # Make discharging negative
            load_not_satisfied.append(load_deficit - effective_energy_from_pbs)  # Adjust unmet load

            #track TES losses 
            tes_losses.append(-tes_loss)
            pipe_losses.append(-pipe_loss)

        else:
            # No stored energy, not all load is met
            pbs_charge.append(0)
            pbs_discharge.append(0)
            load_not_satisfied.append(load_deficit)  # Track unmet load
            tes_losses.append(0)
            pipe_losses.append(0)


    # Ensure storage never drops below 0
    pbs_storage = max(0, pbs_storage)

    # Track the state of the storage
    pbs_capacity.append(pbs_storage)

# Create a time vector based on the hours from the dataset
time_vector = csp_output["Hours"]

# Plot CSP output separately
plt.figure(figsize=(12, 6))

# Plot the CSP thermal power output
plt.plot(time_vector, csp_output["Energy in GJ_June"], label="CSP Output", color='red', linewidth=5)

# Plot the stacked area for charging and unmet load
plt.stackplot(time_vector,
              pbs_charge,  # Packed Bed Charging
              #load_not_satisfied,  # Unmet load
              actual_demand,  # Actual energy demand
              labels=['PBS Charging','Actual Demand'],
              colors=['green','purple', "orange"],
              alpha=0.6)

# Plot the discharging energy as a separate layer below zero
plt.fill_between(time_vector, pbs_discharge, color='green', label='PBS Discharging')
plt.fill_between(time_vector, tes_losses, color='orange', label='Tes Losses')
plt.fill_between(time_vector, pipe_losses, color='black', label='Pipe Losses')

# Customizing the plot for better visualization
plt.xlabel('Time (Hours)')
plt.ylabel('Energy (GJ)')
plt.title('Energy Evolution of CSP Plant with Packed Bed Storage Over 24 Hours')
plt.legend(loc='upper right')
plt.grid(True)
plt.show()


# Plot the CSP thermal power output and demand
plt.plot(time_vector, csp_output["Energy in GJ_June"], label="CSP Output", color='red', linewidth=2)
plt.plot(time_vector, csp_output["Demand"], label="Demand", color='blue', linestyle='--', linewidth=2)

# Fill the area where CSP output exceeds demand (Excess energy)
plt.fill_between(time_vector, csp_output["Energy in GJ_June"], csp_output["Demand"], 
                 where=(csp_output["Energy in GJ_June"] > csp_output["Demand"]), 
                 interpolate=True, color='green', alpha=0.5, label="Excess Energy")

#plot the losses during discharge 
plt.plot(time_vector, tes_losses, label="TES Losses", color='orange', linestyle='-', linewidth=2)
plt.plot(time_vector, pipe_losses, label="Pipe Losses", color='black', linestyle='-', linewidth=2)
#plt.plot(time_vector, pbs_discharge, label="Discharging", color='green', linestyle='-', linewidth=2)


# Fill the area where demand exceeds CSP output (Unmet demand)
plt.fill_between(time_vector, csp_output["Energy in GJ_June"], csp_output["Demand"], 
                 where=(csp_output["Energy in GJ_June"] < csp_output["Demand"]), 
                 interpolate=True, color='yellow', alpha=0.5, label="Unmet Demand")

# Customizing the plot
plt.xlabel('Time (Hours)')
plt.ylabel('Energy (GJ)')
plt.title('CSP Output vs. Demand with Filled Areas for Excess and Unmet Energy')
plt.legend(loc='upper right')
plt.grid(True)
plt.show()


# Export to an Excel file
data_to_export = pd.DataFrame({
    'Hours': time_vector,
    'CSP Output (GJ)': csp_output["Energy in GJ_June"],
    'Actual Demand (GJ)': actual_demand,
    'PBS Charging (GJ)': pbs_charge,
    'PBS Discharging (GJ)': pbs_discharge,
    'Load Not Satisfied (GJ)': load_not_satisfied,
    'PBS Storage Capacity (GJ)': pbs_capacity,
    "pbs_losse": tes_losses,
    'Pipe Losses': pipe_losses
})

# Export to an Excel file
data_to_export.to_excel("Energy_Evolution_CSP_Plant_losses.xlsx", index=False)