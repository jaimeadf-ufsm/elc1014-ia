import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle

def parse_line(line):
    result = {}

    for part in line.strip().split(', '):
        key, value = part.split(': ')
        result[key.strip()] = value.strip()
    
    return result

def read_experiment(filename):
    with open(filename, 'r') as f:
        content = f.read()
    
    parts = content.split('\n\n')
    
    experiment = {
        'parameters': parse_line(parts[0]),
        'metrics': list(map(parse_line, parts[1].split('\n'))),
        'solution': parse_line(parts[2])
    }

    return experiment

def read_experiments(directory):
    experiments = []

    for filename in os.listdir(directory):
        if filename.endswith('.txt'):
            experiment = read_experiment(os.path.join(directory, filename))
            experiments.append(experiment)
    
    return experiments


def plot_solution_heatmap(experiments):
    """
    Create a heatmap showing solutions for different N and K values.
    X-axis: N from 1 to 16
    Y-axis: K from 2 to 16
    Color gradient based on solution steps.
    Only uses experiments with deduplicate=1
    """
    # Filter experiments with deduplicate=1
    dedup_experiments = [e for e in experiments if e['parameters'].get('deduplicate') == '1']
    
    # Create the heatmap grid (N=1-16 on X, K=2-16 on Y)
    n_values = list(range(1, 17))
    k_values = list(range(2, 17))
    
    # Create a dictionary for quick lookup and collect solution values only from the display range
    exp_dict = {}
    solution_values = []
    
    for exp in dedup_experiments:
        n = int(exp['parameters'].get('n', -1))
        k = int(exp['parameters'].get('k', -1))
        solution = exp['solution'].get('solution', '(not found)')
        exp_dict[(n, k)] = solution
        
        # Collect numerical solution values only from the display range for scaling
        if n in n_values and k in k_values and solution != '(not found)':
            try:
                sol_val = float(solution)
                solution_values.append(sol_val)
            except ValueError:
                pass
    
    # Find min and max for color scaling based on the display range
    if solution_values:
        min_val = min(solution_values)
        max_val = max(solution_values)
    else:
        min_val, max_val = 1, 1
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Create a colormap (viridis: blue for low values, yellow for high values)
    cmap = plt.cm.viridis
    
    # Create cell data and text annotations
    for i, k in enumerate(k_values):
        for j, n in enumerate(n_values):
            solution = exp_dict.get((n, k), '(not found)')
            
            # Determine color based on solution value
            if solution == '(not found)':
                color = '#CCCCCC'  # Gray for no solution
            else:
                try:
                    sol_val = float(solution)
                    # Normalize to [0, 1]
                    if max_val > min_val:
                        normalized = (sol_val - min_val) / (max_val - min_val)
                    else:
                        normalized = 0.5
                    color = cmap(normalized)
                except ValueError:
                    color = '#CCCCCC'
            
            # Draw rectangle
            rect = Rectangle((j, i), 1, 1, linewidth=0.5, edgecolor='black', facecolor=color)
            ax.add_patch(rect)
            
            # Add text
            if solution == '(not found)':
                text_display = 'N'
            else:
                try:
                    text_display = str(int(float(solution)))
                except ValueError:
                    text_display = solution
            ax.text(j + 0.5, i + 0.5, text_display, ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Set axis properties
    ax.set_xlim(0, len(n_values))
    ax.set_ylim(0, len(k_values))
    ax.set_aspect('equal')
    
    # Set ticks and labels
    ax.set_xticks(range(len(n_values)))
    ax.set_yticks(range(len(k_values)))
    ax.set_xticklabels(n_values)
    ax.set_yticklabels(k_values)
    
    # Invert Y axis so K=2 is at the top
    ax.invert_yaxis()
    
    ax.set_xlabel('N', fontsize=12, fontweight='bold')
    ax.set_ylabel('K', fontsize=12, fontweight='bold')
    ax.set_title('Mapa de Calor das Soluções', fontsize=14, fontweight='bold')
    
    # Add colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=min_val, vmax=max_val))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, pad=0.02, label='Número de Passos')
    
    plt.tight_layout()
    plt.savefig('plots/solution_heatmap.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Solution heatmap saved to plots/solution_heatmap.png")


def plot_explored_states_vs_depth(experiments):
    """
    Create a line plot of explored states vs depth for N=4 with K=2, K=3, and K=4.
    X-axis: depth
    Y-axis: number of explored states
    Each K value is a separate line.
    """
    for d in range(2):
        # Filter experiments with N=4, deduplicate=1, and K in [2, 3, 4]
        target_k_values = [4, 5, 6, 7, 8]
        filtered_exp = [e for e in experiments 
                        if int(e['parameters'].get('n', -1)) == 8 and 
                        int(e['parameters'].get('k', -1)) in target_k_values and
                        e['parameters'].get('deduplicate') == str(d)]
        
        # Organize data by K
        data_by_k = {}
        for exp in filtered_exp:
            k = int(exp['parameters'].get('k', -1))
            if k not in data_by_k:
                data_by_k[k] = []
            
            # Extract depth and states explored from metrics (only up to depth 10)
            for metric in exp['metrics'][:-1]:
                depth = int(metric.get('depth', 0))
                states_explored = int(metric.get('states explored', 0))
                
                if depth <= 7:
                    data_by_k[k].append((depth, states_explored))
        
        # Sort by depth for each K
        for k in data_by_k:
            data_by_k[k].sort(key=lambda x: x[0])
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 7))
        
        # Plot lines for each K value
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']  # Distinct colors for each K
        for idx, k in enumerate(sorted(target_k_values)):
            if k in data_by_k and data_by_k[k]:
                depths = [d[0] for d in data_by_k[k]]
                states = [d[1] for d in data_by_k[k]]
                ax.plot(depths, states, marker='o', label=f'N=8, K={k}', color=colors[idx], linewidth=2, markersize=6)
        
        ax.set_xlabel('Profundidade', fontsize=12, fontweight='bold')
        ax.set_ylabel('Número de Estados Explorados', fontsize=12, fontweight='bold')
        if d == 0:
            ax.set_title('Estados explorados por Profundidade (sem deduplicação)', fontsize=14, fontweight='bold')
        else:
            ax.set_title('Estados explorados por Profundidade (com deduplicação)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'plots/explored_states_vs_depth_d{d}.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f"Explored states vs depth plot saved to plots/explored_states_vs_depth_d{d}.png")


def plot_memory_vs_k_by_n(experiments):
    """
    Plot last memory usage vs K for different N values.
    X-axis: K from 2 to 128
    Y-axis: Last memory usage
    Lines: N = 1048576, 2097152, 4194304, 8388608
    Only uses experiments with deduplicate=1
    """
    # Filter experiments with deduplicate=1
    dedup_experiments = [e for e in experiments if e['parameters'].get('deduplicate') == '1']
    
    target_n_values = [1048576, 2097152, 4194304, 8388608]
    
    # Organize data by N
    data_by_n = {}
    for n in target_n_values:
        data_by_n[n] = {}
    
    for exp in dedup_experiments:
        n = int(exp['parameters'].get('n', -1))
        k = int(exp['parameters'].get('k', -1))
        
        if n in target_n_values and exp['metrics']:
            # Get the last metric entry
            last_metric = exp['metrics'][-1]
            memory_usage = int(last_metric.get('memory usage', 0))
            
            if k not in data_by_n[n]:
                data_by_n[n][k] = []
            data_by_n[n][k].append(memory_usage)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Colors for each N value
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # Plot lines for each N value
    for idx, n in enumerate(target_n_values):
        k_values = sorted(data_by_n[n].keys())
        if k_values:
            # Calculate average memory usage for each K (in case of multiple runs)
            memory_values = [np.mean(data_by_n[n][k]) for k in k_values]
            ax.plot(k_values, memory_values, marker='o', label=f'N={n}', 
                   color=colors[idx], linewidth=2, markersize=6)
    
    ax.set_xlabel('K', fontsize=12, fontweight='bold')
    ax.set_ylabel('Memória (bytes)', fontsize=12, fontweight='bold')
    ax.set_title('Memória por K', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/memory_vs_k_by_n.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Memory vs K plot saved to plots/memory_vs_k_by_n.png")


def plot_time_vs_k_by_n(experiments):
    """
    Plot last time elapsed vs K for different N values.
    X-axis: K from 2 to 128
    Y-axis: Last time elapsed
    Lines: N = 1048576, 2097152, 4194304, 8388608
    Only uses experiments with deduplicate=1
    """
    # Filter experiments with deduplicate=1
    dedup_experiments = [e for e in experiments if e['parameters'].get('deduplicate') == '1']
    
    target_n_values = [1048576, 2097152, 4194304, 8388608]
    
    # Organize data by N
    data_by_n = {}
    for n in target_n_values:
        data_by_n[n] = {}
    
    for exp in dedup_experiments:
        n = int(exp['parameters'].get('n', -1))
        k = int(exp['parameters'].get('k', -1))
        
        if n in target_n_values and exp['metrics']:
            # Get the last metric entry
            last_metric = exp['metrics'][-1]
            time_elapsed = int(last_metric.get('time elapsed', 0)) / 1e9
            
            if k not in data_by_n[n]:
                data_by_n[n][k] = []
            data_by_n[n][k].append(time_elapsed)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Colors for each N value
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    
    # Plot lines for each N value
    for idx, n in enumerate(target_n_values):
        k_values = sorted(data_by_n[n].keys())
        if k_values:
            # Calculate average time elapsed for each K (in case of multiple runs)
            time_values = [np.mean(data_by_n[n][k]) for k in k_values]
            ax.plot(k_values, time_values, marker='o', label=f'N={n}', 
                   color=colors[idx], linewidth=2, markersize=6)
    
    ax.set_xlabel('K', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tempo (segundos)', fontsize=12, fontweight='bold')
    ax.set_title('Tempo por K', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/time_vs_k_by_n.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Time vs K plot saved to plots/time_vs_k_by_n.png")


def plot_memory_vs_n_by_k(experiments):
    """
    Plot last memory usage vs N for different K values.
    X-axis: N (all experiments)
    Y-axis: Last memory usage
    Lines: K = 2, 16, 32, 64, 128
    Only uses experiments with deduplicate=1
    """
    # Filter experiments with deduplicate=1
    dedup_experiments = [e for e in experiments if e['parameters'].get('deduplicate') == '1']
    
    target_k_values = [2, 3, 16, 32, 64, 128]
    
    # Organize data by K
    data_by_k = {}
    for k in target_k_values:
        data_by_k[k] = {}
    
    for exp in dedup_experiments:
        n = int(exp['parameters'].get('n', -1))
        k = int(exp['parameters'].get('k', -1))
        
        if k in target_k_values and exp['metrics']:
            # Get the last metric entry
            last_metric = exp['metrics'][-1]
            memory_usage = int(last_metric.get('memory usage', 0))
            
            if n not in data_by_k[k]:
                data_by_k[k][n] = []
            data_by_k[k][n].append(memory_usage)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Colors for each K value
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # Plot lines for each K value
    for idx, k in enumerate(target_k_values):
        n_values = sorted(data_by_k[k].keys())
        n_values = [n for n in n_values if n <= 8388608]
        if n_values:
            # Calculate average memory usage for each N (in case of multiple runs)
            memory_values = [np.mean(data_by_k[k][n]) for n in n_values]
            ax.plot(n_values, memory_values, marker='o', label=f'K={k}', 
                   color=colors[idx], linewidth=2, markersize=6)
    
    ax.set_xlabel('N', fontsize=12, fontweight='bold')
    ax.set_ylabel('Memória (bytes)', fontsize=12, fontweight='bold')
    ax.set_title('Memória por N', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/memory_vs_n_by_k.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Memory vs N plot saved to plots/memory_vs_n_by_k.png")


def plot_time_vs_n_by_k(experiments):
    """
    Plot last time elapsed vs N for different K values.
    X-axis: N (all experiments)
    Y-axis: Last time elapsed
    Lines: K = 2, 16, 32, 64, 128
    Only uses experiments with deduplicate=1
    """
    # Filter experiments with deduplicate=1
    dedup_experiments = [e for e in experiments if e['parameters'].get('deduplicate') == '1']
    
    target_k_values = [2, 3, 16, 32, 64, 128]
    
    # Organize data by K
    data_by_k = {}
    for k in target_k_values:
        data_by_k[k] = {}
    
    for exp in dedup_experiments:
        n = int(exp['parameters'].get('n', -1))
        k = int(exp['parameters'].get('k', -1))
        
        if k in target_k_values and exp['metrics']:
            # Get the last metric entry
            last_metric = exp['metrics'][-1]
            time_elapsed = int(last_metric.get('time elapsed', 0)) / 1e9
            
            if n not in data_by_k[k]:
                data_by_k[k][n] = []
            data_by_k[k][n].append(time_elapsed)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Colors for each K value
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # Plot lines for each K value
    for idx, k in enumerate(target_k_values):
        n_values = sorted(data_by_k[k].keys())
        n_values = [n for n in n_values if n <= 8388608]
        if n_values:
            # Calculate average time elapsed for each N (in case of multiple runs)
            time_values = [np.mean(data_by_k[k][n]) for n in n_values]
            ax.plot(n_values, time_values, marker='o', label=f'K={k}', 
                   color=colors[idx], linewidth=2, markersize=6)
    
    ax.set_xlabel('N', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tempo (segundos)', fontsize=12, fontweight='bold')
    ax.set_title('Tempo por N', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/time_vs_n_by_k.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Time vs N plot saved to plots/time_vs_n_by_k.png")


def plot_stacked_states_per_depth(experiments):
    """
    Create a stacked bar chart showing states explored vs states skipped per depth.
    X-axis: depth
    Y-axis: number of states
    Bottom stack: states explored (valid, new states)
    Top stack: states skipped (duplicates/invalid)
    For N=64, K=32 with deduplicate=1
    """
    # Filter experiments with N=64, K=32, deduplicate=1
    filtered_exp = [e for e in experiments
                    if int(e['parameters'].get('n', -1)) == 64 and
                    int(e['parameters'].get('k', -1)) == 32 and
                    e['parameters'].get('deduplicate') == '1']
    
    if not filtered_exp:
        print("No experiments found for N=64, K=32, deduplicate=1")
        return
    
    # Organize data by depth
    data_by_depth = {}
    
    for exp in filtered_exp:
        for metric in exp['metrics']:
            depth = int(metric.get('depth', 0))
            states_explored = int(metric.get('states explored', 0))
            states_skipped = int(metric.get('states skipped', 0))
            
            if depth not in data_by_depth:
                data_by_depth[depth] = {'explored': [], 'skipped': []}
            
            data_by_depth[depth]['explored'].append(states_explored)
            data_by_depth[depth]['skipped'].append(states_skipped)
    
    # Calculate averages for each depth
    depths = sorted(data_by_depth.keys())
    explored_means = [np.mean(data_by_depth[d]['explored']) for d in depths]
    skipped_means = [np.mean(data_by_depth[d]['skipped']) for d in depths]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Create stacked bar chart
    x_pos = np.arange(len(depths))
    bar_width = 0.6
    
    bars1 = ax.bar(x_pos, explored_means, bar_width, label='Estados Explorados', color='#2ca02c', alpha=0.8)
    bars2 = ax.bar(x_pos, skipped_means, bar_width, bottom=explored_means, label='Estados Ignorados', color='#d62728', alpha=0.8)
    
    # Add value labels on bars
    for i, (explored, skipped) in enumerate(zip(explored_means, skipped_means)):
        if explored > 0:
            ax.text(i, explored/2, str(int(explored)), ha='center', va='center', fontweight='bold', color='white', fontsize=9)
        if skipped > 0:
            ax.text(i, explored + skipped/2, str(int(skipped)), ha='center', va='center', fontweight='bold', color='white', fontsize=9)
    
    # Set axis properties
    ax.set_xlabel('Profundidade', fontsize=12, fontweight='bold')
    ax.set_ylabel('Número de Estados', fontsize=12, fontweight='bold')
    ax.set_title('Número de Estados Explorados e Estados Ignorados por Profundidade (N=64, K=32)', fontsize=14, fontweight='bold')
    ax.set_xticks(x_pos)
    ax.set_xticklabels(depths)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig('plots/stacked_states_per_depth_n64_k32.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Stacked states per depth plot saved to plots/stacked_states_per_depth_n64_k32.png")

def plot_memory_vs_n_by_k_limited(experiments):
    """
    Plot last memory usage vs N for different K values (N limited to 1-256).
    X-axis: N (1 to 256)
    Y-axis: Last memory usage
    Lines: K = 2, 3, 16, 32, 64, 128
    Only uses experiments with deduplicate=1
    """
    # Filter experiments with deduplicate=1
    dedup_experiments = [e for e in experiments if e['parameters'].get('deduplicate') == '1']
    
    target_k_values = [2, 3, 16, 32, 64, 128]
    
    # Organize data by K
    data_by_k = {}
    for k in target_k_values:
        data_by_k[k] = {}
    
    for exp in dedup_experiments:
        n = int(exp['parameters'].get('n', -1))
        k = int(exp['parameters'].get('k', -1))
        
        if k in target_k_values and exp['metrics']:
            # Get the last metric entry
            last_metric = exp['metrics'][-1]
            memory_usage = int(last_metric.get('memory usage', 0))
            
            if n not in data_by_k[k]:
                data_by_k[k][n] = []
            data_by_k[k][n].append(memory_usage)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Colors for each K value
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
    
    # Plot lines for each K value
    for idx, k in enumerate(target_k_values):
        n_values = sorted(data_by_k[k].keys())
        n_values = [n for n in n_values if 1 <= n <= 256]
        if n_values:
            # Calculate average memory usage for each N (in case of multiple runs)
            memory_values = [np.mean(data_by_k[k][n]) for n in n_values]
            ax.plot(n_values, memory_values, marker='o', label=f'K={k}', 
                   color=colors[idx], linewidth=2, markersize=6)
    
    ax.set_xlabel('N', fontsize=12, fontweight='bold')
    ax.set_ylabel('Memória (bytes)', fontsize=12, fontweight='bold')
    ax.set_title('Memória por N', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/memory_vs_n_by_k_limited.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Memory vs N (limited 1-256) plot saved to plots/memory_vs_n_by_k_limited.png")


def plot_effective_branching_factor(experiments):
    """
    Create a line plot of effective branching factor vs depth.
    X-axis: depth
    Y-axis: effective branching factor (states explored at depth D / queue size at depth D−1)
    Lines: (N=3, K=2), (N=32, K=4), (N=32, K=8), (N=32, K=16), (N=64, K=4), (N=64, K=8), (N=64, K=16)
    Only uses experiments with deduplicate=1
    """
    # Filter experiments with deduplicate=1
    dedup_experiments = [e for e in experiments if e['parameters'].get('deduplicate') == '1']
    
    target_configs = [
        (3, 2), (32, 4), (32, 8), (32, 16),
        (64, 4), (64, 8), (64, 16)
    ]
    
    # Organize data by (N, K)
    data_by_config = {}
    for n, k in target_configs:
        data_by_config[(n, k)] = []
    
    for exp in dedup_experiments:
        n = int(exp['parameters'].get('n', -1))
        k = int(exp['parameters'].get('k', -1))
        
        if (n, k) not in target_configs:
            continue
        
        # Extract depth, states explored, and queue size
        metrics = exp['metrics']
        
        # For each depth, calculate EBF = states_explored(D) / queue_size(D-1)
        for i, metric in enumerate(metrics[:-1]):
            depth = int(metric.get('depth', -1))
            states_explored = int(metric.get('states explored', 0))
            
            # Get queue size from previous depth (D-1)
            if i > 0:
                prev_queue_size = int(metrics[i-1].get('queue size', 0))
                prev_states = int(metrics[i-1].get('states explored', 0))
            else:
                # For depth 1, use current queue size as reference
                prev_queue_size = int(metric.get('queue size', 0))
                prev_states = 0
            
            # Calculate EBF, avoid division by zero
            if prev_queue_size > 0:
                ebf = (states_explored - prev_states) / prev_queue_size
                data_by_config[(n, k)].append((depth, ebf))
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Colors for each configuration
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    # Plot lines for each configuration
    for idx, (n, k) in enumerate(target_configs):
        if data_by_config[(n, k)]:
            depths = [d for d, _ in sorted(data_by_config[(n, k)], key=lambda x: x[0])]
            ebfs = [ebf for _, ebf in sorted(data_by_config[(n, k)], key=lambda x: x[0])]
            ax.plot(depths, ebfs, marker='o', label=f'N={n}, K={k}', 
                   color=colors[idx], linewidth=2, markersize=6, alpha=0.8)
    
    ax.set_xlabel('Profundidade', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fator de Ramificação Efetivo', fontsize=12, fontweight='bold')
    ax.set_title('Fator de Ramificação Efetivo por Profundidade', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/effective_branching_factor.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Effective branching factor plot saved to plots/effective_branching_factor.png")


# Generate plots
if __name__ == '__main__':
    experiments = read_experiments('experiments')

    plot_solution_heatmap(experiments)
    plot_explored_states_vs_depth(experiments)
    plot_memory_vs_k_by_n(experiments)
    plot_time_vs_k_by_n(experiments)
    plot_memory_vs_n_by_k(experiments)
    plot_time_vs_n_by_k(experiments)
    plot_stacked_states_per_depth(experiments)
    plot_effective_branching_factor(experiments)
    plot_memory_vs_n_by_k_limited(experiments)