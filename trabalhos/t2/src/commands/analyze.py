from typing import Any

from study import *

def general_pipeline(args: Any):
    import pandas as pd
    
    input_path = args.input
    output_path = args.output
    
    study = Study.load(input_path)
    stats = collect_match_statistics(study)
    
    color_rows = []
    agent_rows = []
    
    for (black_agent, white_agent), player_stats in stats.items():
        black_wr, black_avg_time, black_wins, black_losses, black_draws = compute_player_metrics(
            player_stats[Player.BLACK]
        )
        
        white_wr, white_avg_time, white_wins, white_losses, white_draws = compute_player_metrics(
            player_stats[Player.WHITE]
        )
        
        color_rows.append({
            'black_agent': repr(black_agent),
            'white_agent': repr(white_agent),
            'black_win_rate': round(black_wr, 2),
            'black_avg_time': round(black_avg_time, 3),
            'black_wins': black_wins,
            'black_losses': black_losses,
            'black_draws': black_draws,
            'white_win_rate': round(white_wr, 2),
            'white_avg_time': round(white_avg_time, 3),
            'white_wins': white_wins,
            'white_losses': white_losses,
            'white_draws': white_draws,
        })
        
    for (player_agent, opponent_agent) in stats.keys():
        player_as_black = stats[(player_agent, opponent_agent)][Player.BLACK]
        player_as_white = stats[(opponent_agent, player_agent)][Player.WHITE]
        
        opponent_as_black = stats[(opponent_agent, player_agent)][Player.BLACK]
        opponent_as_white = stats[(player_agent, opponent_agent)][Player.WHITE]
        
        player_stats = {
            'wins': player_as_white['wins'] + player_as_black['wins'],
            'losses': player_as_white['losses'] + player_as_black['losses'],
            'draws': player_as_white['draws'] + player_as_black['draws'],
            'metrics': player_as_white['metrics'] + player_as_black['metrics']
        }
        
        opponent_stats = {
            'wins': opponent_as_white['wins'] + opponent_as_black['wins'],
            'losses': opponent_as_white['losses'] + opponent_as_black['losses'],
            'draws': opponent_as_white['draws'] + opponent_as_black['draws'],
            'metrics': opponent_as_white['metrics'] + opponent_as_black['metrics']
        }
        
        player_metrics = compute_player_metrics(player_stats)
        opponent_metrics = compute_player_metrics(opponent_stats)
        
        agent_rows.append({
            'player_agent': repr(player_agent),
            'opponent_agent': repr(opponent_agent),
            'player_win_rate': round(player_metrics[0], 2),
            'player_avg_time': round(player_metrics[1], 3),
            'player_wins': player_metrics[2],
            'player_losses': player_metrics[3],
            'player_draws': player_metrics[4],
            'opponent_win_rate': round(opponent_metrics[0], 2),
            'opponent_avg_time': round(opponent_metrics[1], 3),
            'opponent_wins': opponent_metrics[2],
            'opponent_losses': opponent_metrics[3],
            'opponent_draws': opponent_metrics[4],
        })
            
        
    color_df = pd.DataFrame(color_rows)
    agent_df = pd.DataFrame(agent_rows)
    
    color_df.to_csv(output_path / 'color_comparison.csv', index=False)
    agent_df.to_csv(output_path / 'agent_comparison.csv', index=False)

def move_analysis(args: Any):
    import numpy as np
    import seaborn as sns
    import matplotlib.pyplot as plt
    
    input_path = args.input
    output_path = args.output
    
    study = Study.load(input_path)
    
    stats = {}
    
    for match in study:
        key = (match.black_agent, match.white_agent)
        
        for i in range(1, len(match.history)):
            previous_turn = match.history[i - 1]
            current_turn = match.history[i]
            
            player = previous_turn.state.player
            
            if key not in stats:
                size = match.state.board.size
                empty = np.zeros((size, size), dtype=int)
                
                stats[key] = {
                    Player.BLACK: { 'captures': empty.copy(), 'placements': empty.copy() },
                    Player.WHITE: { 'captures': empty.copy(), 'placements': empty.copy() }
                }
                
            assert current_turn.move is not None
            
            for pos in current_turn.move.placements:
                stats[key][player]['placements'][pos.row, pos.col] += 1
            
            for pos in current_turn.move.captures:
                stats[key][player]['captures'][pos.row, pos.col] += 1
            
    for key, agent_stats in stats.items():
        black_agent, white_agent = key
        
        # Create a 4x2 grid where rows 0 and 2 are for titles, rows 1 and 3 for heatmaps
        fig = plt.figure(figsize=(16, 12))
        gs = fig.add_gridspec(4, 2, height_ratios=[0.15, 1, 0.15, 1], top=0.96)
        
        for row, (player, player_stats) in enumerate(agent_stats.items()):
            placements = player_stats['placements']
            captures = player_stats['captures']
            
            agent = black_agent if player == Player.BLACK else white_agent
            
            ax_title = fig.add_subplot(gs[row * 2, :])
            ax_title.text(
                0.5,
                0.5,
                f'{player}\n{agent}',
                fontsize=13,
                fontweight='bold',
                ha='center',
                va='center',
                transform=ax_title.transAxes
            )
            
            ax_title.axis('off')
            
            ax_placements = fig.add_subplot(gs[row * 2 + 1, 0])
            ax_captures = fig.add_subplot(gs[row * 2 + 1, 1])
            
            sns.heatmap(placements, ax=ax_placements, cmap='Blues', annot=True, fmt='d', square=True, cbar_kws={'shrink': 0.8})
            ax_placements.set_title(f'Jogadas', pad=10)
            
            sns.heatmap(captures, ax=ax_captures, cmap='Reds', annot=True, fmt='d', square=True, cbar_kws={'shrink': 0.8})
            ax_captures.set_title(f'Capturas', pad=10)
        
        plt.savefig(output_path / f'{black_agent}_vs_{white_agent}_heatmap.png')


def collect_match_statistics(study: Study):
    stats = {}
    
    for match in study:
        key = (match.black_agent, match.white_agent)
        
        if key not in stats:
            stats[key] = {
                Player.BLACK: {
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                    'metrics': []
                },
                Player.WHITE: {
                    'wins': 0,
                    'losses': 0,
                    'draws': 0,
                    'metrics': []
                }
            }
        
        winner = match.state.winner
        if winner == Player.BLACK:
            stats[key][Player.BLACK]['wins'] += 1
            stats[key][Player.WHITE]['losses'] += 1
        elif winner == Player.WHITE:
            stats[key][Player.WHITE]['wins'] += 1
            stats[key][Player.BLACK]['losses'] += 1
        else:
            stats[key][Player.BLACK]['draws'] += 1
            stats[key][Player.WHITE]['draws'] += 1
        
        for i, turn in enumerate(match.history[1:]):
            player = match.history[i].state.player
            stats[key][player]['metrics'].append(turn.metrics)
    
    return stats


def compute_player_metrics(player_stats: dict):
    wins = player_stats['wins']
    losses = player_stats['losses']
    draws = player_stats['draws']
    total = wins + losses + draws
    
    win_rate = wins / total * 100
    move_times = [m['elapsed_time'] for m in player_stats['metrics']]
    avg_time = (sum(move_times) / len(move_times))
    
    return win_rate, avg_time, wins, losses, draws

ANALYZE_PIPELINES = {
    'general': general_pipeline
}

def analyze(args: Any):
    ANALYZE_PIPELINES[args.pipeline](args)
