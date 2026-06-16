

#%%
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime

from get_ebird_data import get_ebird_data, get_filtered_ebird_data
from ebird_species_statistics import get_ebird_taxonomy, get_ebird_taxa

def get_ebird_activity_statistics(year:int, countries:list[str] = None) -> dict:
    df_taxonomy = get_ebird_taxonomy()
    df = get_filtered_ebird_data(years=[year], countries=countries)
    # make a date entry with python datetime objects without time, and ignore errors (if the date is not in a valid format, we will get NaT, which we can filter out later)
    df['date_python'] = pd.to_datetime(df['Date'], errors='coerce').dt.normalize()
    
    # make a list of all days since start of the years until end of the years, optionally cut for until today.
    start_date = datetime(year, 1, 1)
    end_date = datetime(year, 12, 31)
    today = datetime.today()
    if end_date > today:
        end_date = today
    date_range = pd.date_range(start=start_date, end=end_date)
    date_range_str = date_range.strftime('%Y-%m-%d')

    activity_dict = {}
    year_species_ticks = []
    year_species_total = 0
    for date, date_str in zip(date_range, date_range_str):
        # filter the dataframe for the current date
        df_date = df[df['date_python'] == date]
        #print(f"Processing date {date_str} with {len(df_date)} records.")
        if len(df_date) == 0:
            activity_dict[date_str] = {
                'species': 0,
                'total_birds': 0,
                'checklist_count': 0,
                'total_traveled': 0,
                'total_duration': 0,
                'year_species_total': year_species_total
            }
            continue
        # get the taxa for the current date
        taxa_date = get_ebird_taxa(df_date, df_taxonomy)
        # add the species that are not in the year_species ticks and take the unique count
        year_species_ticks.extend([species for species in taxa_date['species_common'] if species not in year_species_ticks])
        year_species_total = len(year_species_ticks)
        # total number of birds seen on that day
        total_birds = sum(int(count) for count in df_date['Count'] if str(count).isdigit())
        # get the checklists of that date:
        checklist_IDs = df_date['Submission ID'].unique()
        checklist_count = len(checklist_IDs)
        # df with one row per checklist - we ignore the species part and just care about effort and protocol
        checklist_df = df_date.drop_duplicates(subset=['Submission ID'])
        checklist_total_traveled = checklist_df['Distance Traveled (km)'].sum()
        checklist_total_duration = checklist_df['Duration (Min)'].sum()
        activity_dict[date_str] = {
            'species': taxa_date['species_count'],
            'total_birds': total_birds,
            'checklist_count': checklist_count,
            'total_traveled': checklist_total_traveled,
            'total_duration': checklist_total_duration,
            'year_species_total': year_species_total
        }

    return activity_dict


def plot_ebird_activity_statistics(activity_dict:dict, save_as:str = None) -> None:
    # Group bars by date on one visual axis and show absolute values via custom tick labels.
    dates = list(activity_dict.keys())
    species_counts = [activity_dict[date]['species'] for date in dates]
    total_birds = [activity_dict[date]['total_birds'] for date in dates]
    checklist_counts = [activity_dict[date]['checklist_count'] for date in dates]
    total_traveled = [activity_dict[date]['total_traveled'] for date in dates]
    total_duration = [activity_dict[date]['total_duration'] for date in dates]
    year_species_totals = [activity_dict[date].get('year_species_total', 0) for date in dates]

    def normalize(values: list[float]) -> list[float]:
        max_value = max(values) if values else 0
        if max_value == 0:
            return [0 for _ in values]
        return [value / max_value for value in values]

    species_norm = normalize(species_counts)
    total_birds_norm = normalize(total_birds)
    checklist_norm = [-value for value in normalize(checklist_counts)]
    traveled_norm = [-value for value in normalize(total_traveled)]
    duration_norm = [-value for value in normalize(total_duration)]

    species_max = max(species_counts) if species_counts else 0
    birds_max = max(total_birds) if total_birds else 0
    traveled_max = max(total_traveled) if total_traveled else 0
    duration_max = max(total_duration) if total_duration else 0

    x = list(range(len(dates)))
    bar_width = 0.16
    group_gap = 0.04
    fig, ax = plt.subplots(figsize=(35, 10))
    species_x = [i -  (bar_width + group_gap)/2 for i in x]
    birds_x = [i + (bar_width + group_gap)/2 for i in x]
    checklist_x = x
    traveled_x = [i - (bar_width + group_gap) for i in x]
    duration_x = [i + (bar_width + group_gap) for i in x]

    ax.bar(species_x, species_norm, width=bar_width, label='Species', color='xkcd:evergreen')
    ax.bar(birds_x, total_birds_norm, width=bar_width, label='Total Birds', color='xkcd:blueberry')
    ax.bar(checklist_x, checklist_norm, width=bar_width, label='Checklist Count', color='xkcd:salmon pink')
    ax.bar(traveled_x, traveled_norm, width=bar_width, label='Distance Traveled (km)', color='xkcd:purple')
    ax.bar(duration_x, duration_norm, width=bar_width, label='Duration (min)', color='xkcd:pale orange')

    year_ticks_max = max(year_species_totals) if year_species_totals else 0
    if year_ticks_max > 0:
        year_ticks_line = [0.5 + 0.5 * (value / year_ticks_max) for value in year_species_totals]
    else:
        year_ticks_line = [0.5 for _ in year_species_totals]

    ax.plot(x, year_ticks_line, color='black', linewidth=1.2, label='Year Ticks')
    for i in range(1, len(year_species_totals)):
        delta = year_species_totals[i] - year_species_totals[i - 1]
        if delta > 0:
            ax.text(x[i], year_ticks_line[i] + 0.015, f'+{delta}\n {year_species_totals[i]}', ha='center', va='bottom', fontsize=7, color='black')

    ax.axhline(0, color='black', linewidth=1)

    species_tick_values = [20, 50, 80]
    distance_tick_values = [5, 10, 20, 40]
    visible_species_tick_values = [value for value in species_tick_values if species_max > 0 and value <= species_max]
    visible_distance_tick_values = [value for value in distance_tick_values if traveled_max > 0 and value <= traveled_max]

    species_tick_positions = [
        value / species_max for value in visible_species_tick_values
    ]
    distance_tick_positions = [
        -value / traveled_max for value in visible_distance_tick_values
    ]

    y_ticks = distance_tick_positions + [0] + species_tick_positions
    distance_tick_labels = []
    for distance_value in visible_distance_tick_values:
        normalized_ratio = distance_value / traveled_max if traveled_max > 0 else 0
        duration_value = int(round(normalized_ratio * duration_max))
        distance_tick_labels.append(f'{distance_value} km | {duration_value} min')

    species_tick_labels = []
    for species_value in visible_species_tick_values:
        normalized_ratio = species_value / species_max if species_max > 0 else 0
        individuals_value = int(round(normalized_ratio * birds_max))
        species_tick_labels.append(f'{species_value} sp | {individuals_value} ind')

    y_labels = (
        distance_tick_labels
        + ['0']
        + species_tick_labels
    )
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)

    for tick_position in species_tick_positions + distance_tick_positions:
        ax.axhline(tick_position, color='grey', linestyle=':', linewidth=0.8, zorder=0)

    label_positions = [
        checklist_norm[i] - 0.03 if checklist_norm[i] < 0 else -0.03
        for i in range(len(checklist_counts))
    ]
    min_label_position = min(label_positions) if label_positions else -0.05
    lower_ylim = min(-1.05, min_label_position - 0.03)
    ax.set_ylim(lower_ylim, 1.1)

    ax.set_xticks(x)
    date_labels = [datetime.strptime(date, '%Y-%m-%d').strftime('%a %Y-%m-%d') for date in dates]
    ax.set_xticklabels(date_labels, rotation=90)
    ax.set_xlabel('Date')
    ax.set_ylabel('Bottom: km traveled | minutes (checklist shown as bar+label)   Top: species | birds')
    ax.set_title('eBird Activity Statistics by Date (Grouped Bars, Single Axis)')

    for i, checklist_count in enumerate(checklist_counts):
        label_y = checklist_norm[i] - 0.03 if checklist_norm[i] < 0 else -0.03
        if checklist_count > 0:
            ax.text(checklist_x[i], label_y, f'{checklist_count}', ha='center', va='top', fontsize=7, color='black')

    ax.legend(loc='upper left')
    fig.tight_layout()
    plt.show()
    if save_as:
        fig.savefig(save_as, dpi=400, bbox_inches='tight')

    return


if __name__ == "__main__":
    from pathlib import Path
    year = 2026
    countries = ['NO']#, 'IT', 'CH', 'DE', 'SE', 'FI', 'DK'] 
    activity_stats = get_ebird_activity_statistics(year=year, countries=countries)#, 'IT', 'CH', 'DE', 'SE', 'FI', 'DK'])
    
    # for date, stats in activity_stats.items():
    #     print(f"{date}: {stats}")
    root_path = Path(__file__).parent
    output_dir = root_path / "plots"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"ebird_activity_statistics_{year}_{'_'.join(countries)}.png"
    plot_ebird_activity_statistics(activity_stats, save_as=output_path)
# %%
