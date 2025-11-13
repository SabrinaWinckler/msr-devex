#!/usr/bin/env python3
"""
Análise Comparativa de Ferramentas de IA para Desenvolvimento
Claude Code, GitHub Copilot e Cursor

Este script extrai métricas de feedback loop, cognitive load, flow e perfil
de desenvolvedores/projetos das três ferramentas.
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

def load_json_file(filepath):
    """Carrega arquivo JSON, retorna {} se vazio ou inválido"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if data else {}
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Erro ao carregar {filepath}: {e}")
        return {}

def load_tool_data(tool_path):
    """Carrega todos os dados de uma ferramenta"""
    tool_path = Path(tool_path)
    
    data = {
        'prs_json': load_json_file(tool_path / 'prs.json'),
        'pr_commits': load_json_file(tool_path / 'pr_commits.json'),
        'pr_reviews': load_json_file(tool_path / 'pr_reviews.json'),
        'pr_review_comments': load_json_file(tool_path / 'pr_review_comments.json'),
        'pr_comments': load_json_file(tool_path / 'pr_comments.json'),
        'pr_timelines': load_json_file(tool_path / 'pr_timelines.json'),
        'issues': load_json_file(tool_path / 'issues.json'),
        'developer_metadata': load_json_file(tool_path / 'developer_metadata.json'),
        'repo_metadata': load_json_file(tool_path / 'repo_metadata.json'),
    }
    
    # Carrega CSVs
    try:
        data['prs_csv'] = pd.read_csv(tool_path / 'prs.csv')
    except:
        data['prs_csv'] = pd.DataFrame()
    
    try:
        data['conventional_commits'] = pd.read_csv(tool_path / 'gpt_conventional_commits.csv')
    except:
        data['conventional_commits'] = pd.DataFrame()
    
    try:
        data['related_issues'] = pd.read_csv(tool_path / 'related_issues.csv')
    except:
        data['related_issues'] = pd.DataFrame()
    
    return data

def parse_datetime(dt_str):
    """Converte string de data para datetime"""
    if pd.isna(dt_str) or dt_str == '':
        return None
    try:
        return pd.to_datetime(dt_str)
    except:
        return None

def calculate_feedback_loop_metrics(data):
    """Calcula métricas de feedback loop"""
    metrics = {
        'tempo_ate_merge_hours': [],
        'numero_revisoes': [],
        'comentarios_ferramenta': [],
        'tempo_primeira_revisao_hours': [],
        'review_time_hours': []
    }
    
    # Processa cada PR
    prs = data['prs_json']
    if isinstance(prs, list):
        pr_list = prs
    else:
        pr_list = list(prs.values())
    
    for pr in pr_list:
        if not isinstance(pr, dict):
            continue
            
        pr_id = str(pr.get('id', ''))
        
        # Tempo até o merge
        created = parse_datetime(pr.get('created_at'))
        merged = parse_datetime(pr.get('pull_request', {}).get('merged_at')) if 'pull_request' in pr else parse_datetime(pr.get('merged_at'))
        
        if created and merged:
            time_to_merge = (merged - created).total_seconds() / 3600
            metrics['tempo_ate_merge_hours'].append(time_to_merge)
        
        # Número de revisões
        reviews = data['pr_reviews'].get(f"{pr_id}.json", [])
        if isinstance(reviews, list):
            metrics['numero_revisoes'].append(len(reviews))
            
            # Tempo até primeira revisão
            if reviews and created:
                first_review_time = parse_datetime(reviews[0].get('submitted_at'))
                if first_review_time:
                    time_to_first_review = (first_review_time - created).total_seconds() / 3600
                    metrics['tempo_primeira_revisao_hours'].append(time_to_first_review)
        
        # Comentários da ferramenta
        review_comments = data['pr_review_comments'].get(f"{pr_id}.json", [])
        pr_comments = data['pr_comments'].get(f"{pr_id}.json", [])
        
        total_comments = 0
        if isinstance(review_comments, list):
            total_comments += len(review_comments)
        if isinstance(pr_comments, list):
            total_comments += len(pr_comments)
        
        metrics['comentarios_ferramenta'].append(total_comments)
        
        # Review time
        if reviews and isinstance(reviews, list) and created:
            last_review_time = parse_datetime(reviews[-1].get('submitted_at'))
            if last_review_time:
                review_time = (last_review_time - created).total_seconds() / 3600
                metrics['review_time_hours'].append(review_time)
    
    # Calcula estatísticas
    result = {}
    for key, values in metrics.items():
        if values:
            result[f"{key}_mean"] = np.mean(values)
            result[f"{key}_median"] = np.median(values)
            result[f"{key}_std"] = np.std(values)
            result[f"{key}_total"] = len(values)
        else:
            result[f"{key}_mean"] = 0
            result[f"{key}_median"] = 0
            result[f"{key}_std"] = 0
            result[f"{key}_total"] = 0
    
    return result

def calculate_cognitive_load_metrics(data):
    """Calcula métricas de carga cognitiva"""
    metrics = {
        'conventional_commits': 0,
        'total_comments': 0,
        'issues_antes': 0,
        'issues_depois': 0,
        'frequencia_interrupcoes': [],
        'arquivos_modificados': [],
        'code_churn': []
    }
    
    # Conventional commits
    if not data['conventional_commits'].empty:
        metrics['conventional_commits'] = len(data['conventional_commits'])
    
    # Total de comentários
    for pr_comments in data['pr_comments'].values():
        if isinstance(pr_comments, list):
            metrics['total_comments'] += len(pr_comments)
    
    for review_comments in data['pr_review_comments'].values():
        if isinstance(review_comments, list):
            metrics['total_comments'] += len(review_comments)
    
    # Issues
    issues = data['issues']
    if issues:
        for issue in issues.values():
            if isinstance(issue, dict):
                closed = parse_datetime(issue.get('closed_at'))
                
                if issue.get('state') == 'open':
                    metrics['issues_antes'] += 1
                elif closed:
                    metrics['issues_depois'] += 1
    
    # Frequência de interrupções e arquivos modificados
    for pr_id, commits in data['pr_commits'].items():
        if isinstance(commits, list):
            commit_times = []
            files_in_pr = set()
            
            for commit in commits:
                if isinstance(commit, dict):
                    commit_info = commit.get('commit', {})
                    author_info = commit_info.get('author', {})
                    commit_time = parse_datetime(author_info.get('date'))
                    
                    if commit_time:
                        commit_times.append(commit_time)
                    
                    message = commit_info.get('message', '')
                    files_mentioned = message.count('/')
                    if files_mentioned > 0:
                        files_in_pr.add(files_mentioned)
            
            # Intervalo entre commits
            if len(commit_times) > 1:
                commit_times.sort()
                intervals = []
                for i in range(1, len(commit_times)):
                    interval = (commit_times[i] - commit_times[i-1]).total_seconds() / 3600
                    intervals.append(interval)
                if intervals:
                    metrics['frequencia_interrupcoes'].append(np.mean(intervals))
            
            if files_in_pr:
                metrics['arquivos_modificados'].append(len(files_in_pr))
            
            metrics['code_churn'].append(len(commits))
    
    # Estatísticas
    result = {
        'conventional_commits_total': metrics['conventional_commits'],
        'total_comments': metrics['total_comments'],
        'issues_antes': metrics['issues_antes'],
        'issues_depois': metrics['issues_depois'],
        'issues_delta': metrics['issues_depois'] - metrics['issues_antes'],
    }
    
    if metrics['frequencia_interrupcoes']:
        result['frequencia_interrupcoes_mean_hours'] = np.mean(metrics['frequencia_interrupcoes'])
        result['frequencia_interrupcoes_median_hours'] = np.median(metrics['frequencia_interrupcoes'])
    else:
        result['frequencia_interrupcoes_mean_hours'] = 0
        result['frequencia_interrupcoes_median_hours'] = 0
    
    if metrics['arquivos_modificados']:
        result['arquivos_modificados_mean'] = np.mean(metrics['arquivos_modificados'])
        result['arquivos_modificados_median'] = np.median(metrics['arquivos_modificados'])
    else:
        result['arquivos_modificados_mean'] = 0
        result['arquivos_modificados_median'] = 0
    
    if metrics['code_churn']:
        result['code_churn_mean'] = np.mean(metrics['code_churn'])
        result['code_churn_median'] = np.median(metrics['code_churn'])
    else:
        result['code_churn_mean'] = 0
        result['code_churn_median'] = 0
    
    return result

def calculate_flow_metrics(data):
    """Calcula métricas de flow"""
    metrics = {
        'total_prs': 0,
        'prs_merged': 0,
        'prs_closed': 0,
        'prs_open': 0,
        'tempo_entre_commits': [],
        'tempo_ate_merge': []
    }
    
    prs = data['prs_json']
    if isinstance(prs, list):
        pr_list = prs
    else:
        pr_list = list(prs.values())
    
    metrics['total_prs'] = len(pr_list)
    
    for pr in pr_list:
        if not isinstance(pr, dict):
            continue
        
        state = pr.get('state', '')
        if state == 'open':
            metrics['prs_open'] += 1
        elif state == 'closed':
            metrics['prs_closed'] += 1
            
            merged_at = None
            if 'pull_request' in pr:
                merged_at = pr['pull_request'].get('merged_at')
            else:
                merged_at = pr.get('merged_at')
            
            if merged_at:
                metrics['prs_merged'] += 1
                
                created = parse_datetime(pr.get('created_at'))
                merged = parse_datetime(merged_at)
                if created and merged:
                    time_to_merge = (merged - created).total_seconds() / 3600
                    metrics['tempo_ate_merge'].append(time_to_merge)
    
    # Tempo entre commits
    all_commit_times = []
    for commits in data['pr_commits'].values():
        if isinstance(commits, list):
            for commit in commits:
                if isinstance(commit, dict):
                    commit_info = commit.get('commit', {})
                    author_info = commit_info.get('author', {})
                    commit_time = parse_datetime(author_info.get('date'))
                    if commit_time:
                        all_commit_times.append(commit_time)
    
    if len(all_commit_times) > 1:
        all_commit_times.sort()
        for i in range(1, len(all_commit_times)):
            interval = (all_commit_times[i] - all_commit_times[i-1]).total_seconds() / 3600
            metrics['tempo_entre_commits'].append(interval)
    
    result = {
        'total_prs': metrics['total_prs'],
        'prs_open': metrics['prs_open'],
        'prs_closed': metrics['prs_closed'],
        'prs_merged': metrics['prs_merged'],
        'merge_rate': metrics['prs_merged'] / metrics['total_prs'] if metrics['total_prs'] > 0 else 0,
    }
    
    if metrics['tempo_entre_commits']:
        result['tempo_entre_commits_mean_hours'] = np.mean(metrics['tempo_entre_commits'])
        result['tempo_entre_commits_median_hours'] = np.median(metrics['tempo_entre_commits'])
    else:
        result['tempo_entre_commits_mean_hours'] = 0
        result['tempo_entre_commits_median_hours'] = 0
    
    if metrics['tempo_ate_merge']:
        result['tempo_ate_merge_mean_hours'] = np.mean(metrics['tempo_ate_merge'])
        result['tempo_ate_merge_median_hours'] = np.median(metrics['tempo_ate_merge'])
    else:
        result['tempo_ate_merge_mean_hours'] = 0
        result['tempo_ate_merge_median_hours'] = 0
    
    return result

def get_profile_metrics(data):
    """Extrai perfil de desenvolvedores e projetos"""
    profile = {
        'num_developers': 0,
        'num_repos': 0,
        'languages': [],
        'total_stars': 0,
        'total_forks': 0,
    }
    
    if data['developer_metadata']:
        profile['num_developers'] = len(data['developer_metadata'])
    
    if data['repo_metadata']:
        profile['num_repos'] = len(data['repo_metadata'])
        
        for repo in data['repo_metadata'].values():
            if isinstance(repo, dict):
                lang = repo.get('language')
                if lang:
                    profile['languages'].append(lang)
                
                stars = repo.get('stargazers_count', 0)
                forks = repo.get('forks_count', 0)
                profile['total_stars'] += stars
                profile['total_forks'] += forks
    
    profile['unique_languages'] = len(set(profile['languages']))
    profile['primary_language'] = max(set(profile['languages']), key=profile['languages'].count) if profile['languages'] else 'N/A'
    
    return profile

def main():
    """Função principal"""
    print("="*80)
    print("ANÁLISE COMPARATIVA DE FERRAMENTAS DE IA PARA DESENVOLVIMENTO")
    print("="*80)
    
    # Caminhos das ferramentas
    tools = {
        'Claude_Code': './claude_code',
        'Copilot': './copilot',
        'Cursor': './cursor'
    }
    
    # Carrega dados
    print("\n1. Carregando dados...")
    all_data = {}
    for tool_name, tool_path in tools.items():
        print(f"   - Carregando {tool_name}...")
        all_data[tool_name] = load_tool_data(tool_path)
    
    # Calcula métricas
    print("\n2. Calculando métricas...")
    results = {}
    for tool_name, data in all_data.items():
        print(f"   - Calculando para {tool_name}...")
        results[tool_name] = {
            'feedback_loop': calculate_feedback_loop_metrics(data),
            'cognitive_load': calculate_cognitive_load_metrics(data),
            'flow': calculate_flow_metrics(data),
            'profile': get_profile_metrics(data)
        }
    
    # Cria DataFrames
    print("\n3. Consolidando resultados...")
    feedback_loop_df = pd.DataFrame({tool: results[tool]['feedback_loop'] for tool in results}).T
    cognitive_load_df = pd.DataFrame({tool: results[tool]['cognitive_load'] for tool in results}).T
    flow_df = pd.DataFrame({tool: results[tool]['flow'] for tool in results}).T
    profile_df = pd.DataFrame({tool: results[tool]['profile'] for tool in results}).T
    
    # Exibe resultados
    print("\n" + "="*80)
    print("MÉTRICAS DE FEEDBACK LOOP")
    print("="*80)
    print(feedback_loop_df)
    
    print("\n" + "="*80)
    print("MÉTRICAS DE COGNITIVE LOAD")
    print("="*80)
    print(cognitive_load_df)
    
    print("\n" + "="*80)
    print("MÉTRICAS DE FLOW")
    print("="*80)
    print(flow_df)
    
    print("\n" + "="*80)
    print("PERFIL DE PROJETOS E DESENVOLVEDORES")
    print("="*80)
    print(profile_df)
    
    # Exporta para CSV
    print("\n4. Exportando resultados...")
    feedback_loop_df.to_csv('feedback_loop_metrics.csv')
    cognitive_load_df.to_csv('cognitive_load_metrics.csv')
    flow_df.to_csv('flow_metrics.csv')
    profile_df.to_csv('profile_metrics.csv')
    
    # Cria resumo consolidado
    summary_df = pd.DataFrame()
    for tool in results.keys():
        tool_summary = {
            'Ferramenta': tool,
            'Total_PRs': results[tool]['flow']['total_prs'],
            'Taxa_Merge': results[tool]['flow']['merge_rate'],
            'Tempo_Medio_Merge_h': results[tool]['feedback_loop']['tempo_ate_merge_hours_mean'],
            'Num_Revisoes_Media': results[tool]['feedback_loop']['numero_revisoes_mean'],
            'Comentarios_Media': results[tool]['feedback_loop']['comentarios_ferramenta_mean'],
            'Conventional_Commits': results[tool]['cognitive_load']['conventional_commits_total'],
            'Code_Churn_Media': results[tool]['cognitive_load']['code_churn_mean'],
            'Num_Desenvolvedores': results[tool]['profile']['num_developers'],
            'Num_Repositorios': results[tool]['profile']['num_repos'],
            'Linguagem_Principal': results[tool]['profile']['primary_language'],
        }
        summary_df = pd.concat([summary_df, pd.DataFrame([tool_summary])], ignore_index=True)
    
    summary_df.to_csv('summary_comparison.csv', index=False)
    
    print("\n" + "="*80)
    print("RESUMO COMPARATIVO")
    print("="*80)
    print(summary_df.to_string(index=False))
    
    # Gera visualizações
    print("\n5. Gerando visualizações...")
    
    # Feedback Loop
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Métricas de Feedback Loop por Ferramenta', fontsize=16)
    
    feedback_loop_df['tempo_ate_merge_hours_mean'].plot(kind='bar', ax=axes[0,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,0].set_title('Tempo Médio até Merge (horas)')
    axes[0,0].set_ylabel('Horas')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    feedback_loop_df['numero_revisoes_mean'].plot(kind='bar', ax=axes[0,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,1].set_title('Número Médio de Revisões')
    axes[0,1].set_ylabel('Revisões')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    feedback_loop_df['comentarios_ferramenta_mean'].plot(kind='bar', ax=axes[1,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,0].set_title('Média de Comentários por PR')
    axes[1,0].set_ylabel('Comentários')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    feedback_loop_df['tempo_primeira_revisao_hours_mean'].plot(kind='bar', ax=axes[1,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,1].set_title('Tempo Médio até Primeira Revisão (horas)')
    axes[1,1].set_ylabel('Horas')
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('feedback_loop_metrics.png', dpi=300, bbox_inches='tight')
    print("   - feedback_loop_metrics.png gerado")
    
    # Cognitive Load
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Métricas de Cognitive Load por Ferramenta', fontsize=16)
    
    cognitive_load_df['conventional_commits_total'].plot(kind='bar', ax=axes[0,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,0].set_title('Total de Conventional Commits')
    axes[0,0].set_ylabel('Commits')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    cognitive_load_df['arquivos_modificados_mean'].plot(kind='bar', ax=axes[0,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,1].set_title('Média de Arquivos Modificados por PR')
    axes[0,1].set_ylabel('Arquivos')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    cognitive_load_df['code_churn_mean'].plot(kind='bar', ax=axes[1,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,0].set_title('Média de Code Churn (commits por PR)')
    axes[1,0].set_ylabel('Commits')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    cognitive_load_df['issues_delta'].plot(kind='bar', ax=axes[1,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,1].set_title('Delta de Issues (Fechadas - Abertas)')
    axes[1,1].set_ylabel('Issues')
    axes[1,1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('cognitive_load_metrics.png', dpi=300, bbox_inches='tight')
    print("   - cognitive_load_metrics.png gerado")
    
    # Flow
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Métricas de Flow por Ferramenta', fontsize=16)
    
    flow_df['total_prs'].plot(kind='bar', ax=axes[0,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,0].set_title('Total de PRs')
    axes[0,0].set_ylabel('PRs')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    flow_df['merge_rate'].plot(kind='bar', ax=axes[0,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,1].set_title('Taxa de Merge')
    axes[0,1].set_ylabel('Taxa (0-1)')
    axes[0,1].set_ylim([0, 1])
    axes[0,1].tick_params(axis='x', rotation=45)
    
    flow_df['tempo_entre_commits_mean_hours'].plot(kind='bar', ax=axes[1,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,0].set_title('Tempo Médio entre Commits (horas)')
    axes[1,0].set_ylabel('Horas')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    flow_df['tempo_ate_merge_mean_hours'].plot(kind='bar', ax=axes[1,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,1].set_title('Tempo Médio até Merge (horas)')
    axes[1,1].set_ylabel('Horas')
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('flow_metrics.png', dpi=300, bbox_inches='tight')
    print("   - flow_metrics.png gerado")
    
    print("\n" + "="*80)
    print("ANÁLISE CONCLUÍDA!")
    print("="*80)
    print("\nArquivos gerados:")
    print("  - feedback_loop_metrics.csv")
    print("  - cognitive_load_metrics.csv")
    print("  - flow_metrics.csv")
    print("  - profile_metrics.csv")
    print("  - summary_comparison.csv")
    print("  - feedback_loop_metrics.png")
    print("  - cognitive_load_metrics.png")
    print("  - flow_metrics.png")
    print("="*80)

if __name__ == '__main__':
    main()
