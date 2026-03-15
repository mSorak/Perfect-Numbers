import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("rent_burden_all.csv")

# =========================
# BLOG STYLE SETTINGS
# =========================
import matplotlib.colors as mc
import colorsys

def lighten_color(hex_color, factor=0.5):
    """
    Lightens a hex color by blending it toward white.
    factor: 0 = original, 1 = white
    """
    rgb = mc.to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(*rgb)
    new_l = l + (1 - l) * factor
    new_rgb = colorsys.hls_to_rgb(h, new_l, s)
    return mc.to_hex(new_rgb)

BG = "#fff7ed"          # blog background
US_DARK = "#5072a7"     # accent blue
US_LIGHT = "#8fa8d6"

state_colors = {
    "Alabama": "#9B2335",      # Crimson Tide
    "Alaska": "#1C6BA0",       # Glacial arctic blue
    "Arizona": "#D2691E",      # Saguaro desert sandstone
    "Arkansas": "#C8102E",     # State flag red diamond
    "California": "#F5C518",   # Golden State / gold rush
    "Colorado": "#4A7C59",     # Rocky Mountain evergreens
    "Connecticut": "#003087",  # Colonial flag blue
    "Delaware": "#7BA7BC",
    "District of Columbia": "#D4AF37",  # Federal district black
    "Florida": "#FF6B35",      # Florida orange / sunshine
    "Georgia": "#E8392A",      # Georgia peach red
    "Hawaii": "#008B8B",       # Teal Pacific waters
    "Idaho": "#8B4513",        # Snake River canyon earth
    "Illinois": "#1A4B8C",     # Chicago Bears / flag navy
    "Indiana": "#002D62",      # Pacers midnight navy
    "Iowa": "#FFD700",         # Cornfield gold
    "Kansas": "#C9A84C",       # Sunflower / wheat gold
    "Kentucky": "#4B7B4B",     # Bluegrass green
    "Louisiana": "#4B2882",    # Mardi Gras purple
    "Maine": "#2C5F8A",        # Atlantic lobster navy
    "Maryland": "#9c2f2f",     # State flag terracotta
    "Massachusetts": "#5E4FA2",# Revolutionary colonial purple
    "Michigan": "#00274C",     # U of Michigan deep navy
    "Minnesota": "#C0C0C0",    # 10,000 Lakes silver
    "Mississippi": "#B8860B",  # Magnolia dark gold
    "Missouri": "#003366",     # Gateway Arch midnight blue
    "Montana": "#6B8E6B",      # Big Sky sage green
    "Nebraska": "#CC2529",     # Cornhuskers scarlet
    "Nevada": "#708090",       # Silver State slate grey
    "New Hampshire": "#2F6B4A",# White Mountain forest green
    "New Jersey": "#F4A460",   # Jersey Shore sandy tan
    "New Mexico": "#CC3300",   # Zia sun red
    "New York": "#F96815",     # Knicks orange
    "North Carolina": "#CC0000",# Cardinal red
    "North Dakota": "#5B3A29", # Badlands prairie brown
    "Ohio": "#BB0000",         # Buckeyes scarlet
    "Oklahoma": "#CC7722",     # Prairie ochre
    "Oregon": "#154734",       # Douglas fir coastal green
    "Pennsylvania": "#002868", # Keystone flag blue
    "Rhode Island": "#0056A2", # Narragansett Bay blue
    "South Carolina": "#006400",# Palmetto green
    "South Dakota": "#A0785A", # Mt. Rushmore granite rose
    "Tennessee": "#FF8200",    # Vols orange
    "Texas": "#BF0A30",        # Lone Star flag red
    "Utah": "#E07B39",         # Arches burnt orange
    "Vermont": "#3B5E2B",      # Green Mountain deep green
    "Virginia": "#003366",     # Colonial Williamsburg navy
    "Washington": "#2B7A0E",   # Evergreen State green
    "West Virginia": "#6B4A3E",# Coal country russet
    "Wisconsin": "#B0001E",    # Badgers red
    "Wyoming": "#AA8800",      # Buffalo Bill plains gold
}

# Generate light variants
state_colors_light = {state: lighten_color(hex) for state, hex in state_colors.items()}

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": BG,
    "savefig.facecolor": BG,

    "font.family": "DejaVu Sans",     # clean sans body
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,

    "xtick.color": "#333333",
    "ytick.color": "#333333",

    "axes.edgecolor": "#d8cfc4",
    "grid.color": "#e6ded3"
})


# --- Select rows ---
us = df[df["state_name"] == "United States"].iloc[0]
state_data = df[df["state_name"] == "Maryland"].iloc[0]

years = [2001, 2019, 2024]

income_groups = [
    ("under_15k", "Under $15,000"),
    ("15k_29k", "$15k–29k"),
    ("30k_44k", "$30k–44k"),
    ("45k_74k", "$45k–74k"),
    ("75k_plus", "$75k+"),
    ("all_renters", "All Renters")
]

for state_name in df["state_name"].to_list()[1:]:
    fig, axes = plt.subplots(3, 2, figsize=(14, 10), sharey=True)
    axes = axes.flatten()

    state_data = df[df["state_name"] == state_name].iloc[0]

    width = 0.35
    x = np.arange(len(years))

    for ax, (inc_key, inc_label) in zip(axes, income_groups):

        us_severe = [us[f"severe_{inc_key}_{yr}"] for yr in years]
        us_moderate = [us[f"moderate_{inc_key}_{yr}"] for yr in years]

        state_data_severe = [state_data[f"severe_{inc_key}_{yr}"] for yr in years]
        state_data_moderate = [state_data[f"moderate_{inc_key}_{yr}"] for yr in years]

        # --- US ---
        ax.bar(x - width/2, us_severe, width, color=US_DARK)
        ax.bar(x - width/2, us_moderate, width,
            bottom=us_severe, color=US_LIGHT)

        # --- Maryland ---
        ax.bar(x + width/2, state_data_severe, width, color=state_colors[state_name])
        ax.bar(x + width/2, state_data_moderate, width,
            bottom=state_data_severe, color=state_colors_light[state_name])

        # Titles & ticks
        ax.set_title(inc_label, fontfamily="DejaVu Sans Mono")
        ax.set_xticks(x)
        ax.set_xticklabels(years)

        # Minimal grid
        ax.grid(axis="y", linestyle="--", alpha=0.4)

        # Remove top/right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # Y labels on left column
    for i in [0, 2, 4]:
        axes[i].set_ylabel("Share of Renter Households (%)")

    # =========================
    # Legend
    # =========================

    handles = [
        plt.Rectangle((0,0),1,1,color=US_DARK),
        plt.Rectangle((0,0),1,1,color=US_LIGHT),
        plt.Rectangle((0,0),1,1,color=state_colors[state_name]),
        plt.Rectangle((0,0),1,1,color=state_colors_light[state_name]),
    ]

    labels = [
        "US Severely Cost Burdened",
        "US Moderately Cost Burdened",
        f"{state_name} Severely Cost Burdened",
        f"{state_name} Moderately Cost Burdened"
    ]

    fig.legend(handles, labels, loc="upper center", ncol=4, bbox_to_anchor=(0.5, .95),frameon=True, edgecolor="#d8cfc4", facecolor="#fff7ed")

    # =========================
    # Title
    # =========================

    fig.suptitle(
        f"Rent Burden by Income Group — United States vs {state_name}",
        fontsize=18,
        fontfamily="DejaVu Sans Mono",
        y=0.98
    )

    # =========================
    # BRANDING (Bottom Left)
    # =========================

    fig.text(
        0.01, -0.02,
        "Perfect\nNumbers",
        fontfamily="DejaVu Sans Mono",
        fontsize=14,
        color="#333333",
        ha="left",
        va="bottom"
    )


    # Notes (sans)
    notes = (
        "Notes:"
        "Household incomes are adjusted for inflation using the CPI-U for All Items; "
        "Moderately (severely) cost-burdened households spend 30–50% (more than 50%) of income on rent and utilities. \n"
        "Source: JCHS tabulations of US Census Bureau, American Community Survey 1-Year Estimates\n"
        "Created: Matt Sorak - Perfect Numbers"
    )

    fig.text(
        0.09, -0.02,     # positioned to the right of branding
        notes,
        fontsize=9,
        color="#444444",
        ha="left",
        va="bottom",
        wrap=True
    )

    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    plt.savefig(f"state_imgs/{state_name}_rent_burden_chart.png")
    plt.show()