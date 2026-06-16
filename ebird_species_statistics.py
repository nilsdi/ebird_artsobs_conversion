
#%%
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from datetime import datetime

from get_ebird_data import get_ebird_data, get_filtered_ebird_data

def get_ebird_taxonomy() -> pd.DataFrame:
    df = pd.read_excel('ebird_lists/eBird-Clements_v2025-integrated-checklist-October-2025.xlsx')
    return df

def get_ebird_taxa_total(years:list[int] = None, countries:list[str] = None) -> dict:
    df_taxonomy = get_ebird_taxonomy()
    df = get_filtered_ebird_data(years=years, countries=countries)
    return get_ebird_taxa(df, df_taxonomy)

def get_ebird_taxa(df:pd.DataFrame, df_taxonomy:pd.DataFrame) -> dict:
    taxa_common = df['Common Name'].unique()
    taxa_scientific = df['Scientific Name'].unique()
    taxa_count = len(taxa_common)
    species_common = []
    species_scientific = []
    hybrids_common = []
    subspecies_common = []
    spuhs_common = []
    slashs_common = []
    domestics_common = []
    for t_common, t_scientific in zip(taxa_common, taxa_scientific):
        # find the corresponding row in the taxonomy dataframe
        taxonomy_row = df_taxonomy[df_taxonomy['scientific name'] == t_scientific]
        if not taxonomy_row['English name'].iloc[0] == t_common:
            print(f"Warning: Common name '{t_common}' does not match scientific name '{t_scientific}' in taxonomy.")
        taxa_category = taxonomy_row['category'].iloc[0]
        if taxa_category == 'species':
            species_common.append(t_common)
            species_scientific.append(t_scientific)
        elif taxa_category == 'hybrid':
            hybrids_common.append(t_common)
        elif taxa_category == 'subspecies' or 'group' in taxa_category:
            subspecies_common.append(t_common)
            # make sure that the main species is also included in the list of species
            main_species_scientific = t_scientific.split()[0] + ' ' + t_scientific.split()[1]
            if main_species_scientific not in species_scientific:
                main_species_row = df_taxonomy[df_taxonomy['scientific name'] == main_species_scientific]
                if not main_species_row.empty:
                    species_common.append(main_species_row['English name'].iloc[0])
                    species_scientific.append(main_species_scientific)
                else:
                    print(f"Warning: Main species '{main_species_scientific}' for subspecies '{t_scientific}' not found in taxonomy.")
        elif taxa_category == 'spuh':
            spuhs_common.append(t_common)
        elif taxa_category == 'slash':
            slashs_common.append(t_common)
        elif taxa_category == 'domestic':
            domestics_common.append(t_common)
        else:
            print(f"Warning: Taxa category '{taxa_category}' for '{t_common}' is not recognized.")

    species_count = len(species_common)
    return {
        'species_count': species_count,
        'species_common': species_common,
        'species_scientific': species_scientific,
        'hybrids_common': hybrids_common,
        'subspecies_common': subspecies_common,
        'spuhs_common': spuhs_common,
        'slashs_common': slashs_common,
        'domestics_common': domestics_common
    }

def ebird_species_statistics(years:list[int] = None, countries:list[str] = None) -> dict:
    df = get_filtered_ebird_data(years=years, countries=countries)
    taxa_stats = get_ebird_taxa_total(years=years, countries=countries)
    total_checklists = len(df['Submission ID'].unique())
    species_common = taxa_stats['species_common']
    species_scientific = taxa_stats['species_scientific']
    species_stats = {}
    def get_species_stats(species_scientific_name:str) -> int:
        df_species = df[df['Scientific Name'] == species_scientific_name]
        list_count = len(df_species)
        all_counts = [int(count) for count in df_species['Count'] if str(count).isdigit()]
        return list_count, sum(all_counts)
    
    for common, scientific in zip(species_common, species_scientific):
        count, total_individuals = get_species_stats(scientific)
        species_stats[common] = {
            'scientific_name': scientific,
            'list_count': count,
            'list_percentage': (count / total_checklists) * 100 if total_checklists > 0 else 0,
            'total_individuals': total_individuals
        }
    return species_stats

def plot_species_statistics(species_stats:dict, save_as:str = None) -> None:
    species_names = list(species_stats.keys())
    list_counts = [stats['list_count'] for stats in species_stats.values()]
    list_percentages = [stats['list_percentage'] for stats in species_stats.values()]
    total_individuals = [stats['total_individuals'] for stats in species_stats.values()]

    def normalize(values: list[float]) -> list[float]:
        max_value = max(values) if values else 0
        if max_value == 0:
            return [0 for _ in values]
        return [value / max_value for value in values]

    list_percentages_norm = normalize(list_percentages)
    total_individuals_norm = [-value for value in normalize(total_individuals)]
    checklist_max = max(list_counts) if list_counts else 0
    individuals_max = max(total_individuals) if total_individuals else 0

    x = list(range(len(species_names)))
    bar_width = 0.38

    fig, ax = plt.subplots(figsize=(40, 12))
    freq_bars = ax.bar(
        [i - bar_width / 2 for i in x],
        list_percentages_norm,
        width=bar_width,
        color='tab:blue',
        alpha=0.8,
        label='Checklist Frequency (%)'
    )
    total_bars = ax.bar(
        [i + bar_width / 2 for i in x],
        total_individuals_norm,
        width=bar_width,
        color='tab:red',
        alpha=0.8,
        label='Total Individuals (absolute, downward)'
    )

    ax.axhline(0, color='black', linewidth=1)
    ax.set_ylim(-1.1, 1.1)

    def absolute_tick_formatter(value: float, _: int) -> str:
        if value > 0:
            return f'{int(round(value * checklist_max))}'
        if value < 0:
            return f'{int(round(abs(value) * individuals_max))}'
        return '0'

    ax.yaxis.set_major_formatter(FuncFormatter(absolute_tick_formatter))
    ax.set_xlabel('Species')
    ax.set_ylabel('Up: Checklist Count (absolute) | Down: Total Individuals (absolute)')
    ax.set_title('eBird Species Statistics (Mirrored From Center Axis)')
    ax.set_xticks(x)
    ax.set_xticklabels(species_names, rotation=90)

    for bar, percentage in zip(freq_bars, list_percentages):
        ax.annotate(
            f'{percentage:.1f}%',
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords='offset points',
            ha='center',
            va='bottom',
            color='tab:blue',
            fontsize=7,
        )

    for bar, total in zip(total_bars, total_individuals):
        ax.annotate(
            f'{int(total)}',
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, -3),
            textcoords='offset points',
            ha='center',
            va='top',
            color='tab:red',
            fontsize=7,
        )

    ax.legend(loc='upper left')
    
    if save_as:
        plt.savefig(save_as, dpi=400, bbox_inches='tight')
    plt.tight_layout()
    plt.show()
if __name__ == "__main__":
    from pathlib import Path
    years = [2026]
    countries = ['NO']#, 'IT', 'CH', 'DE', 'SE', 'FI', 'DK']
    stats = get_ebird_taxa_total(years=years, countries=countries)
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    species_freq = ebird_species_statistics(years=years, countries=countries)
    for species, freq in species_freq.items():  
        print(f"{species}: {freq}")
    root_path = Path(__file__).parent
    output_dir = root_path / "plots"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"ebird_species_statistics_{'_'.join(map(str, years))}_{'_'.join(countries)}.png"
    plot_species_statistics(species_freq, save_as=output_path)

# %%
