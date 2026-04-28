import pandas as pd

# Load the dataset
df = pd.read_csv('SpiceRack-website-main/FRWR_cut_down.csv')

# Filter out rows where the "spices" column is the string "set()"
df_filtered = df[df['spices'] != 'set()']

# Save the result to a new file
df_filtered.to_csv('preliminary_use_dataset.csv', index=False) #final dataset made with terminal commands.