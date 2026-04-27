from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import seaborn as sns

from study import *
from match import *
from player import *
from agent import *

@dataclass(frozen=True, slots=True)
class AgentDescriptor:
    kind: str
    label: str
    slug: str
    evaluator: str | None = None
    depth: int | None = None
    iterations: int | None = None
    c: float | None = None


@dataclass(slots=True)
class AnalysisContext:
    matches: list[Match]
    variant_name: str
    board_size: int
    match_df: pd.DataFrame
    turn_df: pd.DataFrame
    depth_df: pd.DataFrame
    placement_df: pd.DataFrame
    capture_df: pd.DataFrame
    agent_df: pd.DataFrame


def _slugify(text: str) -> str:
    normalized = text.lower().strip()
    normalized = re.sub(r'[^a-z0-9]+', '_', normalized)
    normalized = re.sub(r'_+', '_', normalized)
    normalized = normalized.strip('_')

    return normalized or 'sem_nome'


def _evaluator_label(agent: MinimaxAgent) -> str:
    if agent.evaluator.name is not None and agent.evaluator.name != '':
        return agent.evaluator.name

    return agent.evaluator.__class__.__name__


def _describe_agent(agent: Agent) -> AgentDescriptor:
    kind = agent.__class__.__name__

    if isinstance(agent, MinimaxAgent):
        evaluator = _evaluator_label(agent)
        label = f'Minimax ({evaluator}, profundidade={agent.depth})'
        slug = f'minimax_{_slugify(evaluator)}_d{agent.depth}'

        return AgentDescriptor(
            kind=kind,
            label=label,
            slug=slug,
            evaluator=evaluator,
            depth=agent.depth,
        )

    if isinstance(agent, MCTSAgent):
        c_text = f'{agent.c:g}'
        label = f'MCTS (iterações={agent.iterations}, c={c_text})'
        c_slug = c_text.replace('.', '_')
        slug = f'mcts_i{agent.iterations}_c{c_slug}'

        return AgentDescriptor(
            kind=kind,
            label=label,
            slug=slug,
            iterations=agent.iterations,
            c=agent.c,
        )

    label = kind

    return AgentDescriptor(
        kind=kind,
        label=label,
        slug=_slugify(label),
    )


def _load_matches(path: Path) -> list[Match]:
    loaded = Study.load(path)

    if isinstance(loaded, Study):
        return list(loaded)

    if isinstance(loaded, list):
        return loaded

    if hasattr(loaded, 'matches'):
        return list(loaded.matches)

    return list(loaded)


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _winner_code(player: Player | None) -> str:
    if player == Player.BLACK:
        return 'BLACK'
    if player == Player.WHITE:
        return 'WHITE'
    return 'DRAW'


def _format_seconds(total_seconds: float) -> str:
    total_seconds = float(total_seconds)

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    return f'{hours:02d}:{minutes:02d}:{seconds:06.3f}'


def _empty_df(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _build_context(matches: list[Match]) -> AnalysisContext:
    variant_name = 'desconhecida'
    board_size = 0

    if len(matches) > 0:
        variant_names = {match.variant.__class__.__name__ for match in matches}

        if len(variant_names) != 1:
            raise ValueError(
                'O estudo informado possui mais de uma variante, mas esta análise '
                'assume apenas uma variante por entrada.'
            )

        variant_name = next(iter(variant_names))
        board_size = matches[0].history[0].state.board.size

    match_rows: list[dict[str, Any]] = []
    turn_rows: list[dict[str, Any]] = []
    depth_rows: list[dict[str, Any]] = []
    placement_rows: list[dict[str, Any]] = []
    capture_rows: list[dict[str, Any]] = []

    unique_agents: dict[str, AgentDescriptor] = {}

    for match_id, match in enumerate(matches):
        black_desc = _describe_agent(match.black_agent)
        white_desc = _describe_agent(match.white_agent)

        unique_agents[black_desc.slug] = black_desc
        unique_agents[white_desc.slug] = white_desc

        total_turns = len(match.history) - 1
        total_time = sum(turn.metrics.get('elapsed_time', 0.0) for turn in match.history[1:])

        match_rows.append({
            'match_id': match_id,
            'winner': _winner_code(match.state.winner),
            'total_turns': total_turns,
            'total_time': total_time,
            'black_kind': black_desc.kind,
            'black_label': black_desc.label,
            'black_slug': black_desc.slug,
            'black_evaluator': black_desc.evaluator,
            'black_depth': black_desc.depth,
            'black_iterations': black_desc.iterations,
            'black_c': black_desc.c,
            'white_kind': white_desc.kind,
            'white_label': white_desc.label,
            'white_slug': white_desc.slug,
            'white_evaluator': white_desc.evaluator,
            'white_depth': white_desc.depth,
            'white_iterations': white_desc.iterations,
            'white_c': white_desc.c,
        })

        for index in range(1, len(match.history)):
            previous_state = match.history[index - 1].state
            turn = match.history[index]

            actor_player = previous_state.player
            actor_player_code = 'BLACK' if actor_player == Player.BLACK else 'WHITE'
            actor_desc = black_desc if actor_player == Player.BLACK else white_desc

            elapsed_time = turn.metrics.get('elapsed_time')
            total_nodes_explored = turn.metrics.get('total_nodes_explored')
            total_nodes_pruned = turn.metrics.get('total_nodes_pruned')

            turn_rows.append({
                'match_id': match_id,
                'turn_number': turn.state.count,
                'actor_player': actor_player_code,
                'actor_kind': actor_desc.kind,
                'actor_label': actor_desc.label,
                'actor_slug': actor_desc.slug,
                'actor_evaluator': actor_desc.evaluator,
                'actor_depth': actor_desc.depth,
                'actor_iterations': actor_desc.iterations,
                'actor_c': actor_desc.c,
                'elapsed_time': elapsed_time,
                'total_nodes_explored': total_nodes_explored,
                'total_nodes_pruned': total_nodes_pruned,
            })

            if turn.move is not None:
                for position in turn.move.placements:
                    placement_rows.append({
                        'match_id': match_id,
                        'turn_number': turn.state.count,
                        'actor_player': actor_player_code,
                        'actor_kind': actor_desc.kind,
                        'actor_label': actor_desc.label,
                        'actor_slug': actor_desc.slug,
                        'row': position.row,
                        'col': position.col,
                    })

                for position in turn.move.captures:
                    capture_rows.append({
                        'match_id': match_id,
                        'turn_number': turn.state.count,
                        'actor_player': actor_player_code,
                        'actor_kind': actor_desc.kind,
                        'actor_label': actor_desc.label,
                        'actor_slug': actor_desc.slug,
                        'row': position.row,
                        'col': position.col,
                    })

            by_depth = turn.metrics.get('by_depth')

            if isinstance(by_depth, dict):
                for search_depth, metrics in by_depth.items():
                    depth_rows.append({
                        'match_id': match_id,
                        'turn_number': turn.state.count,
                        'actor_player': actor_player_code,
                        'actor_kind': actor_desc.kind,
                        'actor_label': actor_desc.label,
                        'actor_slug': actor_desc.slug,
                        'actor_evaluator': actor_desc.evaluator,
                        'actor_depth': actor_desc.depth,
                        'search_depth': int(search_depth),
                        'nodes_explored': metrics.get('nodes_explored', 0),
                        'nodes_pruned': metrics.get('nodes_pruned', 0),
                    })

    match_df = pd.DataFrame(match_rows)
    turn_df = pd.DataFrame(turn_rows)
    depth_df = pd.DataFrame(depth_rows)
    placement_df = pd.DataFrame(placement_rows)
    capture_df = pd.DataFrame(capture_rows)
    agent_df = pd.DataFrame([{
        'kind': desc.kind,
        'label': desc.label,
        'slug': desc.slug,
        'evaluator': desc.evaluator,
        'depth': desc.depth,
        'iterations': desc.iterations,
        'c': desc.c,
    } for desc in unique_agents.values()])

    if match_df.empty:
        match_df = _empty_df([
            'match_id', 'winner', 'total_turns', 'total_time',
            'black_kind', 'black_label', 'black_slug', 'black_evaluator', 'black_depth', 'black_iterations', 'black_c',
            'white_kind', 'white_label', 'white_slug', 'white_evaluator', 'white_depth', 'white_iterations', 'white_c',
        ])

    if turn_df.empty:
        turn_df = _empty_df([
            'match_id', 'turn_number', 'actor_player', 'actor_kind', 'actor_label', 'actor_slug',
            'actor_evaluator', 'actor_depth', 'actor_iterations', 'actor_c',
            'elapsed_time', 'total_nodes_explored', 'total_nodes_pruned',
        ])

    if depth_df.empty:
        depth_df = _empty_df([
            'match_id', 'turn_number', 'actor_player', 'actor_kind', 'actor_label', 'actor_slug',
            'actor_evaluator', 'actor_depth', 'search_depth', 'nodes_explored', 'nodes_pruned',
        ])

    if placement_df.empty:
        placement_df = _empty_df([
            'match_id', 'turn_number', 'actor_player', 'actor_kind', 'actor_label', 'actor_slug', 'row', 'col',
        ])

    if capture_df.empty:
        capture_df = _empty_df([
            'match_id', 'turn_number', 'actor_player', 'actor_kind', 'actor_label', 'actor_slug', 'row', 'col',
        ])

    if agent_df.empty:
        agent_df = _empty_df(['kind', 'label', 'slug', 'evaluator', 'depth', 'iterations', 'c'])

    return AnalysisContext(
        matches=matches,
        variant_name=variant_name,
        board_size=board_size,
        match_df=match_df,
        turn_df=turn_df,
        depth_df=depth_df,
        placement_df=placement_df,
        capture_df=capture_df,
        agent_df=agent_df,
    )


def _save_figure(fig: plt.Figure, path: Path):
    _ensure_dir(path.parent)
    fig.savefig(path, dpi=220, bbox_inches='tight')
    plt.close(fig)


def _save_empty_plot(path: Path, title: str, message: str):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.axis('off')
    ax.set_title(title)
    ax.text(0.5, 0.5, message, ha='center', va='center')
    _save_figure(fig, path)


def _to_matrix(df: pd.DataFrame, size: int) -> np.ndarray:
    matrix = np.zeros((size, size), dtype=int)

    for row in df.itertuples():
        matrix[int(row.row), int(row.col)] += 1

    return matrix


def len_pipeline(args: Any, context: AnalysisContext):
    print(f'Length: {len(context.matches)}')


def summary_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'summary')

    total_matches = len(context.match_df)
    total_turns = int(context.match_df['total_turns'].sum()) if total_matches > 0 else 0
    total_move_time = float(context.match_df['total_time'].sum()) if total_matches > 0 else 0.0

    lines = [
        'Resumo do estudo',
        f'Variante analisada: {context.variant_name}',
        f'Total de partidas: {total_matches}',
        f'Total de turnos: {total_turns}',
        f'Tempo total gasto em jogadas: {_format_seconds(total_move_time)} ({total_move_time:.3f} s)',
        '',
        'Resultado por confronto (perspectiva do agente preto):',
    ]

    if total_matches == 0:
        lines.append('- Nenhuma partida encontrada.')
    else:
        grouped = (
            context.match_df
            .groupby(['black_slug', 'white_slug', 'black_label', 'white_label'], as_index=False)
            .agg(
                total_partidas=('winner', 'size'),
                vitorias_preto=('winner', lambda values: int((values == 'BLACK').sum())),
                derrotas_preto=('winner', lambda values: int((values == 'WHITE').sum())),
                empates=('winner', lambda values: int((values == 'DRAW').sum())),
            )
            .sort_values(['black_label', 'white_label'])
        )

        grouped['taxa_vitoria_preto'] = 100.0 * grouped['vitorias_preto'] / grouped['total_partidas']

        for row in grouped.itertuples():
            lines.append(
                f'- Preto={row.black_label} | Branco={row.white_label}: '
                f'vitórias={row.vitorias_preto}, derrotas={row.derrotas_preto}, '
                f'empates={row.empates}, taxa de vitória={row.taxa_vitoria_preto:.2f}%'
            )

    summary_text = '\n'.join(lines)

    print(summary_text)

    with open(pipeline_dir / 'resumo.txt', 'w', encoding='utf-8') as file:
        file.write(summary_text)


def _build_minimax_vs_mcts_df(match_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for row in match_df.itertuples():
        black_is_minimax = row.black_kind == 'MinimaxAgent'
        white_is_minimax = row.white_kind == 'MinimaxAgent'
        black_is_mcts = row.black_kind == 'MCTSAgent'
        white_is_mcts = row.white_kind == 'MCTSAgent'

        if black_is_minimax and white_is_mcts:
            if row.black_depth is None or row.white_iterations is None:
                continue

            rows.append({
                'evaluator': row.black_evaluator,
                'depth': int(row.black_depth),
                'iterations': int(row.white_iterations),
                'minimax_color': 'BLACK',
                'minimax_win': row.winner == 'BLACK',
            })

        if black_is_mcts and white_is_minimax:
            if row.white_depth is None or row.black_iterations is None:
                continue

            rows.append({
                'evaluator': row.white_evaluator,
                'depth': int(row.white_depth),
                'iterations': int(row.black_iterations),
                'minimax_color': 'WHITE',
                'minimax_win': row.winner == 'WHITE',
            })

    return pd.DataFrame(rows, columns=['evaluator', 'depth', 'iterations', 'minimax_color', 'minimax_win'])


def _plot_win_heatmap(df: pd.DataFrame, title: str, output_path: Path):
    if df.empty:
        _save_empty_plot(
            output_path,
            title,
            'Sem dados para este recorte.',
        )
        return

    grouped = (
        df
        .groupby(['depth', 'iterations'], as_index=False)['minimax_win']
        .mean()
        .rename(columns={'minimax_win': 'win_rate'})
    )

    matrix = grouped.pivot(index='depth', columns='iterations', values='win_rate')
    matrix = matrix.sort_index(axis=0).sort_index(axis=1)

    if matrix.empty:
        _save_empty_plot(
            output_path,
            title,
            'Sem dados para este recorte.',
        )
        return

    matrix_percent = 100.0 * matrix

    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        matrix_percent,
        ax=ax,
        annot=True,
        fmt='.1f',
        cmap='YlGnBu',
        linewidths=0.5,
        linecolor='white',
        vmin=0,
        vmax=100,
        cbar_kws={'label': 'Taxa de vitória do Minimax (%)'},
    )

    ax.set_xlabel('Iterações do MCTS')
    ax.set_ylabel('Profundidade do Minimax')
    ax.set_title(title)

    _save_figure(fig, output_path)


def win_heatmap_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'win_heatmap')
    minimax_vs_mcts = _build_minimax_vs_mcts_df(context.match_df)

    if minimax_vs_mcts.empty:
        _save_empty_plot(
            pipeline_dir / 'sem_dados.png',
            'Taxa de vitória Minimax x MCTS',
            'Não foram encontrados confrontos Minimax x MCTS no estudo.',
        )
        return

    evaluators = sorted(str(name) for name in minimax_vs_mcts['evaluator'].dropna().unique())

    perspectives = [
        ('WHITE', 'como_brancas.png', 'quando joga de Brancas'),
        ('BLACK', 'como_pretas.png', 'quando joga de Pretas'),
        ('ANY', 'qualquer_cor.png', 'em qualquer cor'),
    ]

    for evaluator in evaluators:
        evaluator_dir = _ensure_dir(pipeline_dir / _slugify(evaluator))
        evaluator_df = minimax_vs_mcts[minimax_vs_mcts['evaluator'] == evaluator]

        for perspective, file_name, description in perspectives:
            if perspective == 'ANY':
                slice_df = evaluator_df
            else:
                slice_df = evaluator_df[evaluator_df['minimax_color'] == perspective]

            title = f'Taxa de vitória do Minimax ({evaluator}) {description}'
            _plot_win_heatmap(slice_df, title, evaluator_dir / file_name)


def average_time_minimax_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'average_time_minimax')
    output_path = pipeline_dir / 'tempo_medio_minimax.png'

    df = context.turn_df[
        (context.turn_df['actor_kind'] == 'MinimaxAgent')
        & context.turn_df['elapsed_time'].notna()
    ]

    if df.empty:
        _save_empty_plot(output_path, 'Tempo médio por jogada do Minimax', 'Sem jogadas de Minimax no estudo.')
        return

    grouped = (
        df.groupby(['actor_evaluator', 'actor_depth'], as_index=False)['elapsed_time']
        .mean()
        .sort_values(['actor_evaluator', 'actor_depth'])
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    for evaluator, evaluator_df in grouped.groupby('actor_evaluator'):
        evaluator_df = evaluator_df.sort_values('actor_depth')

        ax.plot(
            evaluator_df['actor_depth'],
            evaluator_df['elapsed_time'],
            marker='o',
            label=str(evaluator),
        )

    ax.set_xlabel('Profundidade do Minimax')
    ax.set_ylabel('Tempo médio por jogada (s)')
    ax.set_title('Tempo médio por jogada do Minimax')
    ax.legend(title='Avaliador')
    ax.grid(True, alpha=0.25)

    _save_figure(fig, output_path)


def average_time_mcts_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'average_time_mcts')
    output_path = pipeline_dir / 'tempo_medio_mcts.png'

    df = context.turn_df[
        (context.turn_df['actor_kind'] == 'MCTSAgent')
        & context.turn_df['elapsed_time'].notna()
    ]

    if df.empty:
        _save_empty_plot(output_path, 'Tempo médio por jogada do MCTS', 'Sem jogadas de MCTS no estudo.')
        return

    grouped = (
        df.groupby('actor_iterations', as_index=False)['elapsed_time']
        .mean()
        .sort_values('actor_iterations')
    )

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(grouped['actor_iterations'], grouped['elapsed_time'], marker='o')

    ax.set_xlabel('Iterações do MCTS')
    ax.set_ylabel('Tempo médio por jogada (s)')
    ax.set_title('Tempo médio por jogada do MCTS')
    ax.grid(True, alpha=0.25)

    _save_figure(fig, output_path)


def average_time_per_turn_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'average_time_per_turn')
    output_path = pipeline_dir / 'tempo_medio_por_turno.png'

    df = context.turn_df[context.turn_df['elapsed_time'].notna()].copy()

    if df.empty:
        _save_empty_plot(output_path, 'Tempo médio por turno', 'Sem métricas de tempo no estudo.')
        return

    df['series_label'] = df['actor_label']

    minimax_mask = df['actor_kind'] == 'MinimaxAgent'
    minimax_depth = pd.to_numeric(df.loc[minimax_mask, 'actor_depth'], errors='coerce')

    df.loc[minimax_mask, 'series_label'] = np.where(
        minimax_depth.notna(),
        'Minimax (profundidade=' + minimax_depth.astype(int).astype(str) + ')',
        'Minimax (profundidade desconhecida)',
    )

    grouped = (
        df.groupby(['series_label', 'turn_number'], as_index=False)['elapsed_time']
        .mean()
        .sort_values(['series_label', 'turn_number'])
    )

    fig, ax = plt.subplots(figsize=(12, 7))

    for series_label, agent_df in grouped.groupby('series_label'):
        ax.plot(
            agent_df['turn_number'],
            agent_df['elapsed_time'],
            label=series_label,
        )

    ax.set_xlabel('Número do turno')
    ax.set_ylabel('Tempo médio por jogada (s)')
    ax.set_title('Tempo médio por jogada em cada turno')
    ax.grid(True, alpha=0.25)

    ax.legend(
        title='Configuração do agente',
        bbox_to_anchor=(1.02, 1),
        loc='upper left',
        borderaxespad=0,
    )

    _save_figure(fig, output_path)


def total_states_explored_minimax_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'total_states_explored_minimax')
    output_path = pipeline_dir / 'total_estados_explorados_minimax.png'

    df = context.turn_df[
        (context.turn_df['actor_kind'] == 'MinimaxAgent')
        & context.turn_df['total_nodes_explored'].notna()
    ]

    if df.empty:
        _save_empty_plot(
            output_path,
            'Total de estados explorados com Minimax',
            'Sem métricas de nós explorados para Minimax no estudo.',
        )
        return

    grouped = (
        df.groupby(['actor_evaluator', 'actor_depth'], as_index=False)['total_nodes_explored']
        .sum()
        .sort_values(['actor_evaluator', 'actor_depth'])
    )

    fig, ax = plt.subplots(figsize=(9, 6))

    for evaluator, evaluator_df in grouped.groupby('actor_evaluator'):
        evaluator_df = evaluator_df.sort_values('actor_depth')

        ax.plot(
            evaluator_df['actor_depth'],
            evaluator_df['total_nodes_explored'],
            marker='o',
            label=str(evaluator),
        )

    ax.set_xlabel('Profundidade do Minimax')
    ax.set_ylabel('Total de estados explorados')
    ax.set_title('Total de estados explorados com Minimax')
    ax.grid(True, alpha=0.25)
    ax.legend(title='Avaliador')

    _save_figure(fig, output_path)


def average_states_explored_pruned_minimax_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'average_states_explored_pruned_minimax')

    df = context.depth_df[context.depth_df['actor_kind'] == 'MinimaxAgent']

    if df.empty:
        _save_empty_plot(
            pipeline_dir / 'sem_dados.png',
            'Estados explorados/podados por profundidade',
            'Sem métricas por profundidade para Minimax no estudo.',
        )
        return

    for (agent_slug, agent_label), agent_df in df.groupby(['actor_slug', 'actor_label']):
        grouped = (
            agent_df.groupby('search_depth', as_index=False)[['nodes_explored', 'nodes_pruned']]
            .mean()
            .sort_values('search_depth')
        )

        grouped['search_depth'] = grouped['search_depth'].astype(int) + 1
        totals = grouped['nodes_explored'] + grouped['nodes_pruned']

        grouped['explored_norm'] = np.where(totals > 0, grouped['nodes_explored'] / totals, 0.0)
        grouped['pruned_norm'] = np.where(totals > 0, grouped['nodes_pruned'] / totals, 0.0)

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.bar(
            grouped['search_depth'],
            grouped['explored_norm'],
            label='Estados explorados (média)',
            color='#4c72b0',
        )
        ax.bar(
            grouped['search_depth'],
            grouped['pruned_norm'],
            bottom=grouped['explored_norm'],
            label='Estados podados (média)',
            color='#dd8452',
        )

        ax.set_ylim(0, 1.05)
        ax.set_xlabel('Profundidade da árvore')
        ax.set_ylabel('Proporção normalizada por profundidade')
        ax.set_title(f'Média de estados explorados/podados por profundidade\n{agent_label}')
        ax.legend()
        ax.grid(True, axis='y', alpha=0.2)

        _save_figure(fig, pipeline_dir / f'{agent_slug}.png')


def _plot_board_heatmap(
    matrix: np.ndarray,
    title: str,
    colorbar_label: str,
    output_path: Path,
):
    matrix = matrix.astype(dtype=np.float64)
    matrix /= matrix.sum()

    fig, ax = plt.subplots(figsize=(6, 5.8))
    sns.heatmap(
        matrix,
        ax=ax,
        annot=True,
        fmt='.1%',
        cmap='YlOrRd',
        square=True,
        linewidths=0.5,
        linecolor='white',
        vmin=0,
        vmax=0.1,
        cbar_kws={'label': colorbar_label},
    )

    ax.set_xlabel('Coluna')
    ax.set_ylabel('Linha')
    ax.set_title(title)

    _save_figure(fig, output_path)


def _piece_heatmaps_pipeline(
    context: AnalysisContext,
    output_dir: Path,
    source_df: pd.DataFrame,
    title_prefix: str,
    colorbar_label: str,
):
    if context.board_size == 0 or context.agent_df.empty:
        _save_empty_plot(
            output_dir / 'sem_dados.png',
            title_prefix,
            'Sem dados de agentes ou tabuleiro para gerar o mapa de calor.',
        )
        return

    perspectives = [
        ('WHITE', 'como_brancas.png', 'como Brancas'),
        ('BLACK', 'como_pretas.png', 'como Pretas'),
        ('ANY', 'qualquer_cor.png', 'em qualquer cor'),
    ]

    sorted_agents = context.agent_df.sort_values('label')

    for agent in sorted_agents.itertuples():
        agent_dir = _ensure_dir(output_dir / agent.slug)
        agent_source = source_df[source_df['actor_slug'] == agent.slug]

        for perspective, file_name, perspective_title in perspectives:
            if perspective == 'ANY':
                filtered = agent_source
            else:
                filtered = agent_source[agent_source['actor_player'] == perspective]

            matrix = _to_matrix(filtered, context.board_size)
            title = f'{title_prefix}\n{agent.label} {perspective_title}'
            _plot_board_heatmap(matrix, title, colorbar_label, agent_dir / file_name)


def piece_placement_heatmap_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'piece_placement_heatmap')

    _piece_heatmaps_pipeline(
        context=context,
        output_dir=pipeline_dir,
        source_df=context.placement_df,
        title_prefix='Mapa de calor de posicionamento de peças',
        colorbar_label='Porcentagem de jogadas',
    )


def piece_capture_heatmap_pipeline(args: Any, context: AnalysisContext):
    pipeline_dir = _ensure_dir(args.output / 'piece_capture_heatmap')

    _piece_heatmaps_pipeline(
        context=context,
        output_dir=pipeline_dir,
        source_df=context.capture_df,
        title_prefix='Mapa de calor de capturas',
        colorbar_label='Porcentagem de peças capturadas',
    )


def all_pipeline(args: Any, context: AnalysisContext):
    summary_pipeline(args, context)
    win_heatmap_pipeline(args, context)
    average_time_minimax_pipeline(args, context)
    average_time_mcts_pipeline(args, context)
    average_time_per_turn_pipeline(args, context)
    total_states_explored_minimax_pipeline(args, context)
    average_states_explored_pruned_minimax_pipeline(args, context)
    piece_placement_heatmap_pipeline(args, context)
    piece_capture_heatmap_pipeline(args, context)


ANALYZE_PIPELINES = {
    'len': len_pipeline,
    'summary': summary_pipeline,
    'win_heatmap': win_heatmap_pipeline,
    'average_time_minimax': average_time_minimax_pipeline,
    'average_time_mcts': average_time_mcts_pipeline,
    'average_time_per_turn': average_time_per_turn_pipeline,
    'total_states_explored_minimax': total_states_explored_minimax_pipeline,
    'average_states_explored_pruned_minimax': average_states_explored_pruned_minimax_pipeline,
    'piece_placement_heatmap': piece_placement_heatmap_pipeline,
    'piece_capture_heatmap': piece_capture_heatmap_pipeline,
    'all': all_pipeline,
}


def analyze(args: Any):
    input_path = args.input
    output_path = args.output

    _ensure_dir(output_path)

    matches = _load_matches(input_path)
    context = _build_context(matches)

    sns.set_theme(style='whitegrid', context='notebook')

    ANALYZE_PIPELINES[args.pipeline](args, context)
