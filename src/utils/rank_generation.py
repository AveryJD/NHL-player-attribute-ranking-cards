# ====================================================================================================
# FUNCTIONS FOR RANKING NHL PLAYERS BASED ON ATTRIBUTE SCORES
# ====================================================================================================

# Imports
import pandas as pd
from utils import rank_scores as rs
from utils import constants
from utils import load_save as file

DATA_DIR = constants.DATA_DIR

forward_scorer = rs.SkaterScorer(constants.F_WEIGHTS)
defensemen_scorer = rs.SkaterScorer(constants.D_WEIGHTS)
goalie_scorer = rs.GoalieScorer(constants.G_WEIGHTS)


def calculate_scores(position: str, all_row: pd.Series, evs_row: pd.Series, pkl_row: pd.Series, ppl_row: pd.Series=pd.Series()) -> dict:
    """
    ADD
    """
    if position == 'G':
        scores = {
            'all_score': goalie_scorer.total_score(all_row),
            'evs_score': goalie_scorer.total_score(evs_row),
            'pkl_score': goalie_scorer.total_score(pkl_row),
            'ldg_score': goalie_scorer.score_by_zone(all_row, 'LD'),
            'mdg_score': goalie_scorer.score_by_zone(all_row, 'MD'),
            'hdg_score': goalie_scorer.score_by_zone(all_row, 'HD'),
        }
    elif position == 'D':
        scores = {
            'off_score': defensemen_scorer.offensive_score(all_row),
            'def_score': defensemen_scorer.defensive_score(all_row),
            'evo_score': defensemen_scorer.offensive_score(evs_row),
            'evd_score': defensemen_scorer.defensive_score(evs_row),
            'ppl_score': defensemen_scorer.offensive_score(ppl_row),
            'pkl_score': defensemen_scorer.defensive_score(pkl_row),
            'sht_score': defensemen_scorer.shooting_score(all_row),
            'plm_score': defensemen_scorer.playmaking_score(all_row),
            'phy_score': defensemen_scorer.physicality_score(all_row),
            'pen_score': defensemen_scorer.penalties_score(all_row),
            'fof_score': defensemen_scorer.faceoff_score(all_row),
            'spd_score': 0          # Might be used in the future
        }
    else:
        scores = {
            'off_score': forward_scorer.offensive_score(all_row),
            'def_score': forward_scorer.defensive_score(all_row),
            'evo_score': forward_scorer.offensive_score(evs_row),
            'evd_score': forward_scorer.defensive_score(evs_row),
            'ppl_score': forward_scorer.offensive_score(ppl_row),
            'pkl_score': forward_scorer.defensive_score(pkl_row),
            'sht_score': forward_scorer.shooting_score(all_row),
            'plm_score': forward_scorer.playmaking_score(all_row),
            'phy_score': forward_scorer.physicality_score(all_row),
            'pen_score': forward_scorer.penalties_score(all_row),
            'fof_score': forward_scorer.faceoff_score(all_row),
            'spd_score': 0          # Might be used in the future
        }
        
    return scores


def make_player_rankings(season: str, position: str) -> None:
    """
    ADD
    """

    if position != 'G':

        # Load all skater data
        all_data = file.load_stats_csv(season, position, 'all')
        ev_data = file.load_stats_csv(season, position, '5v5')
        pp_data = file.load_stats_csv(season, position, '5v4')
        pk_data = file.load_stats_csv(season, position, '4v5')

        # Filter skaters who do not meet the minimum games played requirement
        min_gp = constants.MIN_GP_SKATER
        valid_players = all_data.loc[all_data['GP'] >= min_gp, 'Player']

        all_data = all_data[all_data['Player'].isin(valid_players)]
        evs_data = ev_data[ev_data['Player'].isin(valid_players)]
        ppl_data = pp_data[pp_data['Player'].isin(valid_players)]
        pkl_data = pk_data[pk_data['Player'].isin(valid_players)]

        # Initialize ranking and scores lists
        rankings = all_data[['Player', 'Position', 'Team']].copy()
        scores_list = []

        # For each skater in the all data DataFrame
        for _, all_row in all_data.iterrows():
            name = all_row['Player']
            pos = all_row['Position']

            # Get the skater's data rows
            evs_row = evs_data.loc[evs_data['Player'] == name].iloc[0]
            if name in ppl_data['Player'].values:
                ppl_row = ppl_data.loc[ppl_data['Player'] == name].iloc[0]
            else:
                ppl_row = pd.Series()

            if name in pkl_data['Player'].values:
                pkl_row = pkl_data.loc[pkl_data['Player'] == name].iloc[0]
            else:
                pkl_row = pd.Series()

            # Calculate the skater's scores
            scores = calculate_scores(pos, all_row, evs_row, pkl_row, ppl_row)
            scores_list.append(scores)

        # Rank the skater's scores
        scores_df = pd.DataFrame(scores_list)
        rankings = pd.concat([pd.DataFrame({'Season': [season] * len(all_data)}), rankings.reset_index(drop=True), scores_df], axis=1)

        # Correct column names
        score_columns = [col for col in scores_df.columns if col.endswith('_score')]
        for col in score_columns:
            attr = col.split('_')[0]
            rankings[f'{attr}_rank'] = rankings[col].rank(ascending=False, method='min')

        # Save rankings CSV file
        if position == 'F':
            pos_folder = 'forwards' 
        else:
            pos_folder = 'defensemen'
        filename = f'{season}_{position}_rankings.csv'
        file.save_csv(rankings, 'rankings', pos_folder, filename)

    else:
        # Load all goalie data
        all_data = file.load_stats_csv(season, 'G', 'all')
        ev_data = file.load_stats_csv(season, 'G', '5v5')
        pk_data = file.load_stats_csv(season, 'G', '4v5')

        # Filter goalies who do not meet the minimum games played requirement
        min_gp = constants.MIN_GP_GOALIE
        valid_players = all_data.loc[all_data['GP'] >= min_gp, 'Player']

        all_data = all_data[all_data['Player'].isin(valid_players)]
        ev_data = ev_data[ev_data['Player'].isin(valid_players)]
        pk_data = pk_data[pk_data['Player'].isin(valid_players)]

        # Initialize ranking and scores lists
        rankings = all_data[['Player', 'Team']].copy()
        rankings.insert(1, 'Position', 'G')
        scores_list = []

        # For each goalie in the all data DataFrame
        for _, row in all_data.iterrows():
            name = row['Player']

            # Get the goalie's data rows
            ev_row = ev_data.loc[ev_data['Player'] == name].iloc[0]
            pk_row = pk_data.loc[pk_data['Player'] == name].iloc[0]

            # Calculate the skater's scores
            scores = calculate_scores('G', row, ev_row, pk_row)
            scores_list.append(scores)

        # Rank the skater's scores
        scores_df = pd.DataFrame(scores_list)
        rankings = pd.concat([pd.DataFrame({'Season': [season] * len(all_data)}), rankings.reset_index(drop=True), scores_df], axis=1)

        # Correct column names
        score_columns = [col for col in scores_df.columns if col.endswith('_score')]
        for col in score_columns:
            attr = col.split('_')[0]
            rankings[f'{attr}_rank'] = rankings[col].rank(ascending=False, method='min')

        # Save rankings CSV file
        filename = f'{season}_G_rankings.csv'
        file.save_csv(rankings, 'rankings', 'goalies', filename)

