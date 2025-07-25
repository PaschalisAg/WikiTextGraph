import seaborn as sns

# Define your custom palette
colorblind_palette = [
    "#117733",  # Dark Green - Social Work
    "#332288",  # Dark Blue
    "#DDCC77",  # Mustard - Military
    "#CC6677",  # Reddish Pink - Media
    "#88CCEE",  # Light Blue
    "#AA4499",  # Purple - Healthcare & Medicine
    "#44AA99",  # Teal - Business
    "#999933",  # Olive- Humanities & Philosophy
    "#882255",  # Maroon
    "#661100",  # Brown
    "#6699CC",  # Dusty Blue - Applied Arts
    "#888888",  # Medium Gray - Dramaturgical Arts
    "#F0E442",  # Yellow - Government & Law
    "#D55E00",  # Orange - Sports
]

def set_palette():
    """Apply the custom palette and seaborn context."""
    sns.set_palette(colorblind_palette)
    sns.set_context("paper")