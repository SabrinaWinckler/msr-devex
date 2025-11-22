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
import re
from collections import Counter, defaultdict
from scipy import stats
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

def analyze_text_patterns(data):
    """
    Analisa padrões textuais em commits, conventional commits e review comments
    Categoriza por tipo: fix, feat, refactor, docs, test, style, chore, build, ci, perf
    """
    patterns = {
        'fix': [],
        'feat': [],
        'refactor': [],
        'docs': [],
        'test': [],
        'style': [],
        'chore': [],
        'build': [],
        'ci': [],
        'perf': []
    }
    
    # Palavras-chave para cada categoria
    keywords = {
        'fix': [r'\bfix\b', r'\bbug\b', r'\berror\b', r'\bissue\b', r'\bproblem\b', r'\bresolve\b', r'\bcorrect\b'],
        'feat': [r'\bfeat\b', r'\bfeature\b', r'\badd\b', r'\bnew\b', r'\bimplement\b', r'\bintroduce\b'],
        'refactor': [r'\brefactor\b', r'\brestructure\b', r'\bclean\b', r'\bimprove\b', r'\boptimize\b', r'\bsimplify\b'],
        'docs': [r'\bdoc\b', r'\bdocument\b', r'\breadme\b', r'\bcomment\b', r'\bguide\b'],
        'test': [r'\btest\b', r'\bspec\b', r'\bunit\b', r'\bcoverage\b', r'\bmock\b'],
        'style': [r'\bstyle\b', r'\bformat\b', r'\blint\b', r'\bwhitespace\b', r'\bindent\b'],
        'chore': [r'\bchore\b', r'\bmaintenance\b', r'\bdependenc\b', r'\bupdate\b', r'\bversion\b'],
        'build': [r'\bbuild\b', r'\bcompile\b', r'\bpackage\b', r'\bdeploy\b', r'\brelease\b'],
        'ci': [r'\bci\b', r'\btravis\b', r'\bjenkins\b', r'\bpipeline\b', r'\bworkflow\b', r'\baction\b'],
        'perf': [r'\bperf\b', r'\bperformance\b', r'\boptimiz\b', r'\bspeed\b', r'\bfast\b']
    }
    
    # Analisa conventional commits (já categorizados)
    if not data['conventional_commits'].empty:
        for _, row in data['conventional_commits'].iterrows():
            commit_type = row.get('type', '').lower()
            if commit_type in patterns:
                patterns[commit_type].append(row.get('title', ''))
    
    # Analisa mensagens de commits
    for pr_id, commits in data['pr_commits'].items():
        if isinstance(commits, list):
            for commit in commits:
                if isinstance(commit, dict):
                    commit_info = commit.get('commit', {})
                    message = commit_info.get('message', '').lower()
                    
                    # Classifica por padrão de palavras-chave
                    categorized = False
                    for category, patterns_list in keywords.items():
                        for pattern in patterns_list:
                            if re.search(pattern, message, re.IGNORECASE):
                                patterns[category].append(message[:100])  # Primeiros 100 chars
                                categorized = True
                                break
                        if categorized:
                            break
    
    # Analisa review comments
    for pr_id, comments in data['pr_review_comments'].items():
        if isinstance(comments, list):
            for comment in comments:
                if isinstance(comment, dict):
                    body = comment.get('body', '').lower()
                    
                    # Classifica comentários por padrão
                    for category, patterns_list in keywords.items():
                        for pattern in patterns_list:
                            if re.search(pattern, body, re.IGNORECASE):
                                patterns[category].append(body[:100])
                                break
    
    # Calcula estatísticas
    result = {}
    total = sum(len(v) for v in patterns.values())
    
    for category, items in patterns.items():
        count = len(items)
        percentage = (count / total * 100) if total > 0 else 0
        result[category] = {
            'count': count,
            'percentage': percentage,
            'items': items[:10]  # Primeiros 10 exemplos
        }
    
    return result

def create_radar_chart(data_dict, title, filename):
    """
    Cria gráfico radar comparando padrões entre ferramentas
    Similar ao gráfico da imagem fornecida
    """
    categories = ['fix', 'feat', 'refactor', 'docs', 'test', 'style', 'chore', 'build', 'ci', 'perf']
    
    # Prepara dados para o gráfico
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Ângulos para cada categoria
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]  # Fecha o círculo
    
    # Cores para cada ferramenta
    colors = {
        'Claude_Code': '#1f77b4',
        'Copilot': '#ff7f0e', 
        'Cursor': '#2ca02c'
    }
    
    # Plota cada ferramenta
    for tool_name, tool_data in data_dict.items():
        values = [tool_data.get(cat, {}).get('percentage', 0) for cat in categories]
        values += values[:1]  # Fecha o círculo
        
        ax.plot(angles, values, 'o-', linewidth=2, label=tool_name, color=colors.get(tool_name, '#000000'))
        ax.fill(angles, values, alpha=0.15, color=colors.get(tool_name, '#000000'))
    
    # Configurações do gráfico
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 50)
    ax.set_yticks([10, 25, 50])
    ax.set_yticklabels(['10%','25%', '50%'])
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Título e legenda
    ax.set_title(title, size=16, pad=20, weight='bold')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"   - {filename} gerado")
    plt.close()

def create_comparison_table(data_dict):
    """
    Cria tabela de comparação entre ferramentas
    """
    categories = ['fix', 'feat', 'refactor', 'docs', 'test', 'style', 'chore', 'build', 'ci', 'perf']
    
    comparison_data = []
    for tool_name, tool_data in data_dict.items():
        row = {'Ferramenta': tool_name}
        for cat in categories:
            row[cat] = tool_data.get(cat, {}).get('count', 0)
        comparison_data.append(row)
    
    df = pd.DataFrame(comparison_data)
    return df

def is_ai_bot(login):
    """Identifica se um usuário é um bot de IA"""
    if not login:
        return False
    
    login_lower = login.lower()
    
    # Bots conhecidos de IA
    ai_bots = [
        'copilot', 'claude', 'cursor', 'codecov', 'changeset-bot',
        'dependabot', 'renovate', 'github-actions', 'greenkeeper',
        'imgbot', 'stale', 'semantic-release-bot', 'allcontributors',
        'gitguardian', 'snyk-bot', 'codefactor-io', 'codacy',
        'deepsource-io', 'sonarcloud', 'lgtm-com', 'circleci',
        'travis-ci', 'netlify', 'vercel', 'heroku', 'gitlab-bot',
        'bitbucket-pipelines', 'azure-pipelines', 'jenkins',
        'bugbot', 'greptile', 'ellipsis', 'cubic', 'gemini'
    ]
    
    # Verifica se contém [bot] ou é um bot conhecido
    if '[bot]' in login_lower:
        return True
    
    for bot_name in ai_bots:
        if bot_name in login_lower:
            return True
    
    # Verifica padrões comuns de bots
    bot_patterns = [
        r'.*\[bot\].*',
        r'.*-bot$',
        r'.*bot-.*',
        r'.*-agent$',
        r'.*-ci$'
    ]
    
    for pattern in bot_patterns:
        if re.match(pattern, login_lower):
            return True
    
    return False

def analyze_ai_vs_human_commits(data):
    """Analisa commits separando contribuições de IA vs Humanos"""
    ai_commits = 0
    human_commits = 0
    ai_authors = set()
    human_authors = set()
    human_commit_details = defaultdict(int)
    
    for pr_id, commits in data['pr_commits'].items():
        if isinstance(commits, list):
            for commit in commits:
                if isinstance(commit, dict):
                    # Verifica autor do commit com proteção contra None
                    author = commit.get('author')
                    author_login = author.get('login', '') if author and isinstance(author, dict) else ''
                    
                    commit_info = commit.get('commit', {})
                    if commit_info and isinstance(commit_info, dict):
                        commit_author = commit_info.get('author', {})
                        commit_author_name = commit_author.get('name', '') if commit_author and isinstance(commit_author, dict) else ''
                    else:
                        commit_author_name = ''
                    
                    # Usa login se disponível, senão usa name
                    author_id = author_login if author_login else commit_author_name
                    
                    if is_ai_bot(author_id):
                        ai_commits += 1
                        ai_authors.add(author_id)
                    else:
                        human_commits += 1
                        human_authors.add(author_id)
                        if author_id:
                            human_commit_details[author_id] += 1
    
    # Top 10 colaboradores humanos por commits
    top_human_contributors = sorted(human_commit_details.items(), 
                                   key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'ai_commits': ai_commits,
        'human_commits': human_commits,
        'total_commits': ai_commits + human_commits,
        'ai_percentage': (ai_commits / (ai_commits + human_commits) * 100) if (ai_commits + human_commits) > 0 else 0,
        'ai_authors_count': len(ai_authors),
        'human_authors_count': len(human_authors),
        'top_human_contributors': top_human_contributors,
        'ai_authors_list': list(ai_authors),
        'human_authors_sample': list(human_authors)[:20]
    }

def analyze_ai_vs_human_comments(data):
    """Analisa comentários em PRs separando IA vs Humanos"""
    ai_comments = 0
    human_comments = 0
    ai_reviewers = set()
    human_reviewers = set()
    human_comment_details = defaultdict(int)
    
    # Analisa pr_comments
    for pr_id, comments in data['pr_comments'].items():
        if isinstance(comments, list):
            for comment in comments:
                if isinstance(comment, dict):
                    user_login = comment.get('user', {}).get('login', '')
                    
                    if is_ai_bot(user_login):
                        ai_comments += 1
                        ai_reviewers.add(user_login)
                    else:
                        human_comments += 1
                        human_reviewers.add(user_login)
                        if user_login:
                            human_comment_details[user_login] += 1
    
    # Analisa pr_review_comments
    for pr_id, comments in data['pr_review_comments'].items():
        if isinstance(comments, list):
            for comment in comments:
                if isinstance(comment, dict):
                    user_login = comment.get('user', {}).get('login', '')
                    
                    if is_ai_bot(user_login):
                        ai_comments += 1
                        ai_reviewers.add(user_login)
                    else:
                        human_comments += 1
                        human_reviewers.add(user_login)
                        if user_login:
                            human_comment_details[user_login] += 1
    
    # Analisa pr_reviews
    for pr_id, reviews in data['pr_reviews'].items():
        if isinstance(reviews, list):
            for review in reviews:
                if isinstance(review, dict):
                    user_login = review.get('user', {}).get('login', '')
                    
                    if is_ai_bot(user_login):
                        ai_reviewers.add(user_login)
                    else:
                        human_reviewers.add(user_login)
    
    # Top 10 colaboradores humanos por comentários
    top_human_commenters = sorted(human_comment_details.items(), 
                                  key=lambda x: x[1], reverse=True)[:10]
    
    return {
        'ai_comments': ai_comments,
        'human_comments': human_comments,
        'total_comments': ai_comments + human_comments,
        'ai_percentage': (ai_comments / (ai_comments + human_comments) * 100) if (ai_comments + human_comments) > 0 else 0,
        'ai_reviewers_count': len(ai_reviewers),
        'human_reviewers_count': len(human_reviewers),
        'top_human_commenters': top_human_commenters,
        'ai_reviewers_list': list(ai_reviewers),
        'human_reviewers_sample': list(human_reviewers)[:20]
    }

def analyze_issues_with_prs(data):
    """Cruza issues com PRs relacionados para análise detalhada"""
    issue_pr_analysis = []
    
    if data['related_issues'].empty:
        return pd.DataFrame()
    
    for _, row in data['related_issues'].iterrows():
        pr_id = str(row.get('pr_id', ''))
        issue_number = str(row.get('issue_number', ''))
        
        # Busca a issue
        issue_data = None
        for issue_key, issue in data['issues'].items():
            if isinstance(issue, dict) and str(issue.get('number', '')) == issue_number:
                issue_data = issue
                break
        
        if not issue_data:
            continue
        
        # Informações da issue
        issue_title = issue_data.get('title', 'N/A')
        issue_reporter = issue_data.get('user', {}).get('login', 'Unknown')
        issue_state = issue_data.get('state', 'N/A')
        
        # Busca commits do PR
        pr_commits_key = f"{pr_id}.json"
        pr_commits = data['pr_commits'].get(pr_commits_key, [])
        
        ai_commits_in_pr = 0
        human_commits_in_pr = 0
        commit_authors = []
        
        if isinstance(pr_commits, list):
            for commit in pr_commits:
                if isinstance(commit, dict):
                    author = commit.get('author')
                    author_login = author.get('login', '') if author and isinstance(author, dict) else ''
                    
                    commit_info = commit.get('commit', {})
                    if commit_info and isinstance(commit_info, dict):
                        commit_author = commit_info.get('author', {})
                        commit_author_name = commit_author.get('name', '') if commit_author and isinstance(commit_author, dict) else ''
                    else:
                        commit_author_name = ''
                    
                    author_id = author_login if author_login else commit_author_name
                    
                    if is_ai_bot(author_id):
                        ai_commits_in_pr += 1
                    else:
                        human_commits_in_pr += 1
        
        # Busca comentários do PR
        pr_comments = data['pr_comments'].get(pr_commits_key, [])
        pr_review_comments = data['pr_review_comments'].get(pr_commits_key, [])
        
        ai_comments_in_pr = 0
        ai_tool_names = set()
        
        for comments_list in [pr_comments, pr_review_comments]:
            if isinstance(comments_list, list):
                for comment in comments_list:
                    if isinstance(comment, dict):
                        user = comment.get('user')
                        user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                        if is_ai_bot(user_login):
                            ai_comments_in_pr += 1
                            ai_tool_names.add(user_login)
        
        # Busca reviews do PR
        pr_reviews = data['pr_reviews'].get(pr_commits_key, [])
        has_ai_review = False
        
        if isinstance(pr_reviews, list):
            for review in pr_reviews:
                if isinstance(review, dict):
                    user = review.get('user')
                    user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                    if is_ai_bot(user_login):
                        has_ai_review = True
                        ai_tool_names.add(user_login)
        
        # Converte set para list antes de fazer slice
        unique_authors = list(set(commit_authors))[:5]
        
        issue_pr_analysis.append({
            'pr_id': pr_id,
            'issue_number': issue_number,
            'issue_title': issue_title,
            'issue_reporter': issue_reporter,
            'issue_state': issue_state,
            'is_reporter_human': not is_ai_bot(issue_reporter),
            'ai_commits': ai_commits_in_pr,
            'human_commits': human_commits_in_pr,
            'total_commits': ai_commits_in_pr + human_commits_in_pr,
            'ai_comments': ai_comments_in_pr,
            'has_ai_review': has_ai_review,
            'ai_tools_involved': ', '.join(ai_tool_names) if ai_tool_names else 'None',
            'commit_authors': ', '.join(unique_authors)
        })
    
    return pd.DataFrame(issue_pr_analysis)

def analyze_cognitive_load_with_ai(data):
    """Analisa carga cognitiva comparando PRs com e sem ferramentas de IA"""
    prs_with_ai = []
    prs_without_ai = []
    
    prs = data['prs_json']
    if isinstance(prs, list):
        pr_list = prs
    else:
        pr_list = list(prs.values())
    
    for pr in pr_list:
        if not isinstance(pr, dict):
            continue
        
        pr_id = str(pr.get('id', ''))
        pr_key = f"{pr_id}.json"
        
        # Verifica se há envolvimento de IA
        has_ai = False
        
        # Checa commits com proteção contra None
        commits = data['pr_commits'].get(pr_key, [])
        if isinstance(commits, list):
            for commit in commits:
                if isinstance(commit, dict):
                    author = commit.get('author')
                    author_login = author.get('login', '') if author and isinstance(author, dict) else ''
                    if is_ai_bot(author_login):
                        has_ai = True
                        break
        
        # Checa comentários
        if not has_ai:
            for comments_list in [data['pr_comments'].get(pr_key, []), 
                                 data['pr_review_comments'].get(pr_key, [])]:
                if isinstance(comments_list, list):
                    for comment in comments_list:
                        if isinstance(comment, dict):
                            user = comment.get('user')
                            user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                            if is_ai_bot(user_login):
                                has_ai = True
                                break
                if has_ai:
                    break
        
        # Checa reviews
        if not has_ai:
            reviews = data['pr_reviews'].get(pr_key, [])
            if isinstance(reviews, list):
                for review in reviews:
                    if isinstance(review, dict):
                        user = review.get('user')
                        user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                        if is_ai_bot(user_login):
                            has_ai = True
                            break
        
        # Coleta métricas do PR
        created = parse_datetime(pr.get('created_at'))
        merged = parse_datetime(pr.get('merged_at'))
        
        num_comments = 0
        num_reviews = 0
        num_commits = 0
        
        if isinstance(data['pr_comments'].get(pr_key, []), list):
            num_comments += len(data['pr_comments'].get(pr_key, []))
        if isinstance(data['pr_review_comments'].get(pr_key, []), list):
            num_comments += len(data['pr_review_comments'].get(pr_key, []))
        if isinstance(data['pr_reviews'].get(pr_key, []), list):
            num_reviews = len(data['pr_reviews'].get(pr_key, []))
        if isinstance(data['pr_commits'].get(pr_key, []), list):
            num_commits = len(data['pr_commits'].get(pr_key, []))
        
        time_to_merge = None
        if created and merged:
            time_to_merge = (merged - created).total_seconds() / 3600
        
        pr_metrics = {
            'pr_id': pr_id,
            'num_comments': num_comments,
            'num_reviews': num_reviews,
            'num_commits': num_commits,
            'time_to_merge_hours': time_to_merge
        }
        
        if has_ai:
            prs_with_ai.append(pr_metrics)
        else:
            prs_without_ai.append(pr_metrics)
    
    # Calcula estatísticas
    def calc_stats(pr_list):
        if not pr_list:
            return {
                'count': 0,
                'avg_comments': 0,
                'avg_reviews': 0,
                'avg_commits': 0,
                'avg_time_to_merge': 0
            }
        
        valid_times = [p['time_to_merge_hours'] for p in pr_list if p['time_to_merge_hours'] is not None]
        
        return {
            'count': len(pr_list),
            'avg_comments': np.mean([p['num_comments'] for p in pr_list]),
            'avg_reviews': np.mean([p['num_reviews'] for p in pr_list]),
            'avg_commits': np.mean([p['num_commits'] for p in pr_list]),
            'avg_time_to_merge': np.mean(valid_times) if valid_times else 0
        }
    
    return {
        'with_ai': calc_stats(prs_with_ai),
        'without_ai': calc_stats(prs_without_ai)
    }

def analyze_issue_reporters(data):
    """Analisa reporters de issues separando humanos de bots"""
    human_reporters = defaultdict(int)
    ai_reporters = defaultdict(int)
    
    for issue_key, issue in data['issues'].items():
        if isinstance(issue, dict):
            reporter = issue.get('user', {}).get('login', '')
            if reporter:
                if is_ai_bot(reporter):
                    ai_reporters[reporter] += 1
                else:
                    human_reporters[reporter] += 1
    
    return {
        'human_reporters_count': len(human_reporters),
        'ai_reporters_count': len(ai_reporters),
        'total_issues_by_humans': sum(human_reporters.values()),
        'total_issues_by_ai': sum(ai_reporters.values()),
        'top_human_reporters': sorted(human_reporters.items(), key=lambda x: x[1], reverse=True)[:10],
        'top_ai_reporters': sorted(ai_reporters.items(), key=lambda x: x[1], reverse=True)[:5]
    }

def analyze_issues_bot_correlation(data):
    """
    Analisa issues abertas e sua correlação com PRs que têm bots envolvidos
    Calcula % de commits e comentários de bots nos PRs relacionados
    """
    issue_bot_correlation = []
    
    if data['related_issues'].empty:
        return pd.DataFrame()
    
    for _, row in data['related_issues'].iterrows():
        pr_id = str(row.get('pr_id', ''))
        issue_number = str(row.get('issue_number', ''))
        
        # Busca a issue
        issue_data = None
        for issue_key, issue in data['issues'].items():
            if isinstance(issue, dict) and str(issue.get('number', '')) == issue_number:
                issue_data = issue
                break
        
        if not issue_data:
            continue
        
        # Informações da issue
        issue_title = issue_data.get('title', 'N/A')
        issue_reporter = issue_data.get('user', {}).get('login', 'Unknown')
        issue_state = issue_data.get('state', 'N/A')
        issue_created = issue_data.get('created_at', 'N/A')
        issue_closed = issue_data.get('closed_at', 'N/A')
        
        # Busca commits do PR
        pr_commits_key = f"{pr_id}.json"
        pr_commits = data['pr_commits'].get(pr_commits_key, [])
        
        ai_commits_count = 0
        human_commits_count = 0
        
        if isinstance(pr_commits, list):
            for commit in pr_commits:
                if isinstance(commit, dict):
                    author = commit.get('author')
                    author_login = author.get('login', '') if author and isinstance(author, dict) else ''
                    
                    commit_info = commit.get('commit', {})
                    if commit_info and isinstance(commit_info, dict):
                        commit_author = commit_info.get('author', {})
                        commit_author_name = commit_author.get('name', '') if commit_author and isinstance(commit_author, dict) else ''
                    else:
                        commit_author_name = ''
                    
                    author_id = author_login if author_login else commit_author_name
                    
                    if is_ai_bot(author_id):
                        ai_commits_count += 1
                    else:
                        human_commits_count += 1
        
        total_commits = ai_commits_count + human_commits_count
        bot_commits_percentage = (ai_commits_count / total_commits * 100) if total_commits > 0 else 0
        
        # Busca comentários e reviews do PR
        pr_comments = data['pr_comments'].get(pr_commits_key, [])
        pr_review_comments = data['pr_review_comments'].get(pr_commits_key, [])
        pr_reviews = data['pr_reviews'].get(pr_commits_key, [])
        
        ai_comments_count = 0
        human_comments_count = 0
        bot_names = set()
        
        for comments_list in [pr_comments, pr_review_comments]:
            if isinstance(comments_list, list):
                for comment in comments_list:
                    if isinstance(comment, dict):
                        user = comment.get('user')
                        user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                        if is_ai_bot(user_login):
                            ai_comments_count += 1
                            bot_names.add(user_login)
                        else:
                            human_comments_count += 1
        
        # Analisa reviews
        ai_reviews_count = 0
        human_reviews_count = 0
        
        if isinstance(pr_reviews, list):
            for review in pr_reviews:
                if isinstance(review, dict):
                    user = review.get('user')
                    user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                    if is_ai_bot(user_login):
                        ai_reviews_count += 1
                        bot_names.add(user_login)
                    else:
                        human_reviews_count += 1
        
        total_comments = ai_comments_count + human_comments_count
        total_reviews = ai_reviews_count + human_reviews_count
        bot_comments_percentage = (ai_comments_count / total_comments * 100) if total_comments > 0 else 0
        bot_reviews_percentage = (ai_reviews_count / total_reviews * 100) if total_reviews > 0 else 0
        
        has_bot_involvement = (ai_commits_count > 0 or ai_comments_count > 0 or ai_reviews_count > 0)
        
        issue_bot_correlation.append({
            'issue_number': issue_number,
            'issue_title': issue_title,
            'issue_reporter': issue_reporter,
            'issue_state': issue_state,
            'issue_created_at': issue_created,
            'issue_closed_at': issue_closed,
            'pr_id': pr_id,
            'has_bot_involvement': has_bot_involvement,
            'bot_names': ', '.join(bot_names) if bot_names else 'None',
            'total_commits': total_commits,
            'ai_commits': ai_commits_count,
            'human_commits': human_commits_count,
            'bot_commits_percentage': round(bot_commits_percentage, 2),
            'total_comments': total_comments,
            'ai_comments': ai_comments_count,
            'human_comments': human_comments_count,
            'bot_comments_percentage': round(bot_comments_percentage, 2),
            'total_reviews': total_reviews,
            'ai_reviews': ai_reviews_count,
            'human_reviews': human_reviews_count,
            'bot_reviews_percentage': round(bot_reviews_percentage, 2),
        })
    
    return pd.DataFrame(issue_bot_correlation)

def calculate_review_cycle_time(data):
    """
    Calcula o review cycle time - tempo entre submissão do PR e aprovação/merge
    Separa por PRs com e sem bot
    """
    cycle_times_with_bot = []
    cycle_times_without_bot = []
    
    prs = data['prs_json']
    if isinstance(prs, list):
        pr_list = prs
    else:
        pr_list = list(prs.values())
    
    for pr in pr_list:
        if not isinstance(pr, dict):
            continue
        
        pr_id = str(pr.get('id', ''))
        pr_key = f"{pr_id}.json"
        
        # Verifica se há bot envolvido
        has_bot = False
        
        # Checa commits
        commits = data['pr_commits'].get(pr_key, [])
        if isinstance(commits, list):
            for commit in commits:
                if isinstance(commit, dict):
                    author = commit.get('author')
                    author_login = author.get('login', '') if author and isinstance(author, dict) else ''
                    if is_ai_bot(author_login):
                        has_bot = True
                        break
        
        # Checa comentários e reviews
        if not has_bot:
            for comments_list in [data['pr_comments'].get(pr_key, []), 
                                 data['pr_review_comments'].get(pr_key, [])]:
                if isinstance(comments_list, list):
                    for comment in comments_list:
                        if isinstance(comment, dict):
                            user = comment.get('user')
                            user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                            if is_ai_bot(user_login):
                                has_bot = True
                                break
                if has_bot:
                    break
        
        # Calcula cycle time
        created = parse_datetime(pr.get('created_at'))
        
        # Busca tempo da primeira aprovação ou merge
        reviews = data['pr_reviews'].get(pr_key, [])
        first_approval_time = None
        
        if isinstance(reviews, list):
            for review in reviews:
                if isinstance(review, dict) and review.get('state') == 'APPROVED':
                    review_time = parse_datetime(review.get('submitted_at'))
                    if review_time:
                        if not first_approval_time or review_time < first_approval_time:
                            first_approval_time = review_time
        
        # Se não há aprovação, usa merge time
        merged = parse_datetime(pr.get('merged_at'))
        end_time = first_approval_time if first_approval_time else merged
        
        if created and end_time:
            cycle_time = (end_time - created).total_seconds() / 3600  # em horas
            
            if has_bot:
                cycle_times_with_bot.append(cycle_time)
            else:
                cycle_times_without_bot.append(cycle_time)
    
    return {
        'with_bot': {
            'count': len(cycle_times_with_bot),
            'mean_hours': np.mean(cycle_times_with_bot) if cycle_times_with_bot else 0,
            'median_hours': np.median(cycle_times_with_bot) if cycle_times_with_bot else 0,
            'std_hours': np.std(cycle_times_with_bot) if cycle_times_with_bot else 0,
            'min_hours': np.min(cycle_times_with_bot) if cycle_times_with_bot else 0,
            'max_hours': np.max(cycle_times_with_bot) if cycle_times_with_bot else 0,
        },
        'without_bot': {
            'count': len(cycle_times_without_bot),
            'mean_hours': np.mean(cycle_times_without_bot) if cycle_times_without_bot else 0,
            'median_hours': np.median(cycle_times_without_bot) if cycle_times_without_bot else 0,
            'std_hours': np.std(cycle_times_without_bot) if cycle_times_without_bot else 0,
            'min_hours': np.min(cycle_times_without_bot) if cycle_times_without_bot else 0,
            'max_hours': np.max(cycle_times_without_bot) if cycle_times_without_bot else 0,
        }
    }

def calculate_intervention_frequency(data):
    """
    Calcula frequência de intervenção: interseção entre comentários de bot e commits de desenvolvedores
    Mede quantas vezes bots comentam seguidos de commits humanos (indicando correções)
    """
    interventions = []
    
    prs = data['prs_json']
    if isinstance(prs, list):
        pr_list = prs
    else:
        pr_list = list(prs.values())
    
    for pr in pr_list:
        if not isinstance(pr, dict):
            continue
        
        pr_id = str(pr.get('id', ''))
        pr_key = f"{pr_id}.json"
        
        # Coleta eventos temporais (commits e comentários)
        events = []
        
        # Adiciona commits
        commits = data['pr_commits'].get(pr_key, [])
        if isinstance(commits, list):
            for commit in commits:
                if isinstance(commit, dict):
                    commit_info = commit.get('commit', {})
                    author_info = commit_info.get('author', {})
                    commit_time = parse_datetime(author_info.get('date'))
                    
                    author = commit.get('author')
                    author_login = author.get('login', '') if author and isinstance(author, dict) else ''
                    
                    if commit_time:
                        events.append({
                            'time': commit_time,
                            'type': 'commit',
                            'is_bot': is_ai_bot(author_login),
                            'actor': author_login
                        })
        
        # Adiciona comentários
        for comments_list in [data['pr_comments'].get(pr_key, []), 
                             data['pr_review_comments'].get(pr_key, [])]:
            if isinstance(comments_list, list):
                for comment in comments_list:
                    if isinstance(comment, dict):
                        comment_time = parse_datetime(comment.get('created_at'))
                        user = comment.get('user')
                        user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                        
                        if comment_time:
                            events.append({
                                'time': comment_time,
                                'type': 'comment',
                                'is_bot': is_ai_bot(user_login),
                                'actor': user_login
                            })
        
        # Ordena eventos por tempo
        events.sort(key=lambda x: x['time'])
        
        # Detecta padrão: comentário de bot seguido de commit humano
        bot_comment_followed_by_human_commit = 0
        
        for i in range(len(events) - 1):
            current = events[i]
            next_event = events[i + 1]
            
            # Bot comenta -> Humano commita (possível correção)
            if (current['type'] == 'comment' and current['is_bot'] and 
                next_event['type'] == 'commit' and not next_event['is_bot']):
                
                time_diff = (next_event['time'] - current['time']).total_seconds() / 3600
                
                # Considera intervenção se commit acontece em até 72h
                if time_diff <= 72:
                    bot_comment_followed_by_human_commit += 1
        
        if events:
            interventions.append({
                'pr_id': pr_id,
                'total_events': len(events),
                'interventions': bot_comment_followed_by_human_commit,
                'intervention_rate': bot_comment_followed_by_human_commit / len(events) if len(events) > 0 else 0
            })
    
    intervention_df = pd.DataFrame(interventions)
    
    return {
        'total_prs_analyzed': len(interventions),
        'total_interventions': intervention_df['interventions'].sum() if not intervention_df.empty else 0,
        'mean_interventions_per_pr': intervention_df['interventions'].mean() if not intervention_df.empty else 0,
        'median_interventions_per_pr': intervention_df['interventions'].median() if not intervention_df.empty else 0,
        'mean_intervention_rate': intervention_df['intervention_rate'].mean() if not intervention_df.empty else 0,
        'prs_with_interventions': len(intervention_df[intervention_df['interventions'] > 0]) if not intervention_df.empty else 0,
        'intervention_details': intervention_df
    }

def collect_pr_level_data(data):
    """
    Coleta dados em nível de PR para análise de correlação
    Retorna DataFrame com métricas por PR
    """
    pr_data = []
    
    prs = data['prs_json']
    if isinstance(prs, list):
        pr_list = prs
    else:
        pr_list = list(prs.values())
    
    for pr in pr_list:
        if not isinstance(pr, dict):
            continue
        
        pr_id = str(pr.get('id', ''))
        pr_key = f"{pr_id}.json"
        
        # Coleta métricas básicas do PR
        created = parse_datetime(pr.get('created_at'))
        merged = parse_datetime(pr.get('merged_at'))
        
        # Conta commits
        commits = data['pr_commits'].get(pr_key, [])
        num_commits = len(commits) if isinstance(commits, list) else 0
        
        # Separa commits AI vs Humanos
        ai_commits = 0
        human_commits = 0
        if isinstance(commits, list):
            for commit in commits:
                if isinstance(commit, dict):
                    author = commit.get('author')
                    author_login = author.get('login', '') if author and isinstance(author, dict) else ''
                    if is_ai_bot(author_login):
                        ai_commits += 1
                    else:
                        human_commits += 1
        
        # Conta comentários totais
        pr_comments = data['pr_comments'].get(pr_key, [])
        pr_review_comments = data['pr_review_comments'].get(pr_key, [])
        num_comments = 0
        ai_comments = 0
        human_comments = 0
        
        for comments_list in [pr_comments, pr_review_comments]:
            if isinstance(comments_list, list):
                num_comments += len(comments_list)
                for comment in comments_list:
                    if isinstance(comment, dict):
                        user = comment.get('user')
                        user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                        if is_ai_bot(user_login):
                            ai_comments += 1
                        else:
                            human_comments += 1
        
        # Conta reviews
        reviews = data['pr_reviews'].get(pr_key, [])
        num_reviews = len(reviews) if isinstance(reviews, list) else 0
        
        ai_reviews = 0
        human_reviews = 0
        if isinstance(reviews, list):
            for review in reviews:
                if isinstance(review, dict):
                    user = review.get('user')
                    user_login = user.get('login', '') if user and isinstance(user, dict) else ''
                    if is_ai_bot(user_login):
                        ai_reviews += 1
                    else:
                        human_reviews += 1
        
        # Calcula tempo até merge
        time_to_merge = None
        if created and merged:
            time_to_merge = (merged - created).total_seconds() / 3600  # em horas
        
        # Verifica se PR tem issues relacionadas
        has_related_issue = False
        if not data['related_issues'].empty:
            has_related_issue = pr_id in data['related_issues']['pr_id'].astype(str).values
        
        # Determina se tem envolvimento de AI
        has_ai_involvement = (ai_commits > 0 or ai_comments > 0 or ai_reviews > 0)
        
        pr_data.append({
            'pr_id': pr_id,
            'total_commits': num_commits,
            'ai_commits': ai_commits,
            'human_commits': human_commits,
            'ai_commits_percentage': (ai_commits / num_commits * 100) if num_commits > 0 else 0,
            'total_comments': num_comments,
            'ai_comments': ai_comments,
            'human_comments': human_comments,
            'ai_comments_percentage': (ai_comments / num_comments * 100) if num_comments > 0 else 0,
            'total_reviews': num_reviews,
            'ai_reviews': ai_reviews,
            'human_reviews': human_reviews,
            'ai_reviews_percentage': (ai_reviews / num_reviews * 100) if num_reviews > 0 else 0,
            'time_to_merge_hours': time_to_merge,
            'has_related_issue': has_related_issue,
            'has_ai_involvement': has_ai_involvement,
            'is_merged': merged is not None
        })
    
    return pd.DataFrame(pr_data)


def calculate_spearman_correlations(all_data):
    """
    Calcula correlações de Spearman entre métricas de interação com ferramentas e resultados
    
    Hipóteses testadas:
    1. Mais interações com AI → Mais commits?
    2. Mais comentários de AI → Menos tempo para merge?
    3. Mais reviews de AI → Mais issues relacionadas?
    4. Mais commits de AI → Mais comentários humanos (necessidade de correção)?
    """
    
    print("\n" + "="*80)
    print("ANÁLISE DE CORRELAÇÃO DE SPEARMAN")
    print("="*80)
    print("\nTestando hipóteses sobre relação entre interações com ferramentas e resultados...")
    
    correlation_results = {}
    
    for tool_name, data in all_data.items():
        print(f"\n### {tool_name} ###")
        
        # Coleta dados em nível de PR
        pr_df = collect_pr_level_data(data)
        
        if pr_df.empty or len(pr_df) < 3:
            print(f"  Dados insuficientes para análise de correlação (n={len(pr_df)})")
            continue
        
        # Remove PRs sem tempo de merge para algumas análises
        pr_df_merged = pr_df[pr_df['time_to_merge_hours'].notna()].copy()
        
        correlations = {}
        
        # Hipótese 1: Mais comentários de AI → Mais commits totais?
        if len(pr_df) >= 3:
            try:
                corr, p_value = stats.spearmanr(pr_df['ai_comments'], pr_df['total_commits'])
                correlations['ai_comments_vs_total_commits'] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n': len(pr_df)
                }
                sig = "✓ SIGNIFICANTE" if p_value < 0.05 else "✗ Não significante"
                print(f"  H1: AI Comments → Total Commits: ρ={corr:.3f}, p={p_value:.4f} {sig}")
            except:
                pass
        
        # Hipótese 2: Mais comentários de AI → Mais commits humanos (correções)?
        if len(pr_df) >= 3:
            try:
                corr, p_value = stats.spearmanr(pr_df['ai_comments'], pr_df['human_commits'])
                correlations['ai_comments_vs_human_commits'] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n': len(pr_df)
                }
                sig = "✓ SIGNIFICANTE" if p_value < 0.05 else "✗ Não significante"
                print(f"  H2: AI Comments → Human Commits: ρ={corr:.3f}, p={p_value:.4f} {sig}")
            except:
                pass
        
        # Hipótese 3: Mais reviews de AI → Menos tempo para merge?
        if len(pr_df_merged) >= 3:
            try:
                corr, p_value = stats.spearmanr(pr_df_merged['ai_reviews'], pr_df_merged['time_to_merge_hours'])
                correlations['ai_reviews_vs_time_to_merge'] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n': len(pr_df_merged)
                }
                sig = "✓ SIGNIFICANTE" if p_value < 0.05 else "✗ Não significante"
                print(f"  H3: AI Reviews → Time to Merge: ρ={corr:.3f}, p={p_value:.4f} {sig}")
            except:
                pass
        
        # Hipótese 4: Mais comentários totais → Mais tempo para merge?
        if len(pr_df_merged) >= 3:
            try:
                corr, p_value = stats.spearmanr(pr_df_merged['total_comments'], pr_df_merged['time_to_merge_hours'])
                correlations['total_comments_vs_time_to_merge'] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n': len(pr_df_merged)
                }
                sig = "✓ SIGNIFICANTE" if p_value < 0.05 else "✗ Não significante"
                print(f"  H4: Total Comments → Time to Merge: ρ={corr:.3f}, p={p_value:.4f} {sig}")
            except:
                pass
        
        # Hipótese 5: Mais reviews totais → Mais commits?
        if len(pr_df) >= 3:
            try:
                corr, p_value = stats.spearmanr(pr_df['total_reviews'], pr_df['total_commits'])
                correlations['total_reviews_vs_total_commits'] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n': len(pr_df)
                }
                sig = "✓ SIGNIFICANTE" if p_value < 0.05 else "✗ Não significante"
                print(f"  H5: Total Reviews → Total Commits: ρ={corr:.3f}, p={p_value:.4f} {sig}")
            except:
                pass
        
        # Hipótese 6: Mais commits de AI → Mais comentários humanos?
        if len(pr_df) >= 3:
            try:
                corr, p_value = stats.spearmanr(pr_df['ai_commits'], pr_df['human_comments'])
                correlations['ai_commits_vs_human_comments'] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n': len(pr_df)
                }
                sig = "✓ SIGNIFICANTE" if p_value < 0.05 else "✗ Não significante"
                print(f"  H6: AI Commits → Human Comments: ρ={corr:.3f}, p={p_value:.4f} {sig}")
            except:
                pass
        
        # Hipótese 7: Mais % de AI → Menos tempo para merge?
        if len(pr_df_merged) >= 3:
            try:
                # Calcula % total de AI (média de commits e comments)
                pr_df_merged['ai_percentage'] = (pr_df_merged['ai_commits_percentage'] + pr_df_merged['ai_comments_percentage']) / 2
                corr, p_value = stats.spearmanr(pr_df_merged['ai_percentage'], pr_df_merged['time_to_merge_hours'])
                correlations['ai_percentage_vs_time_to_merge'] = {
                    'correlation': corr,
                    'p_value': p_value,
                    'significant': p_value < 0.05,
                    'n': len(pr_df_merged)
                }
                sig = "✓ SIGNIFICANTE" if p_value < 0.05 else "✗ Não significante"
                print(f"  H7: AI Percentage → Time to Merge: ρ={corr:.3f}, p={p_value:.4f} {sig}")
            except:
                pass
        
        correlation_results[tool_name] = {
            'correlations': correlations,
            'pr_data': pr_df
        }
    
    return correlation_results


def create_correlation_heatmaps(correlation_results):
    """Cria heatmaps de correlação para cada ferramenta"""
    
    print("\n13. Gerando heatmaps de correlação...")
    
    for tool_name, results in correlation_results.items():
        pr_df = results['pr_data']
        
        if pr_df.empty or len(pr_df) < 3:
            continue
        
        # Seleciona colunas numéricas para correlação
        numeric_cols = [
            'total_commits', 'ai_commits', 'human_commits',
            'total_comments', 'ai_comments', 'human_comments',
            'total_reviews', 'ai_reviews', 'human_reviews',
            'time_to_merge_hours'
        ]
        
        # Filtra colunas que existem no DataFrame
        available_cols = [col for col in numeric_cols if col in pr_df.columns]
        
        # Remove linhas com NaN na coluna time_to_merge_hours
        correlation_df = pr_df[available_cols].dropna()
        
        if len(correlation_df) < 3:
            print(f"   - Dados insuficientes para {tool_name}")
            continue
        
        # Calcula matriz de correlação de Spearman
        corr_matrix = correlation_df.corr(method='spearman')
        
        # Cria heatmap
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # Cria máscara para triângulo superior
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        
        # Plota heatmap
        sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', 
                   cmap='coolwarm', center=0, vmin=-1, vmax=1,
                   square=True, linewidths=1, cbar_kws={"shrink": 0.8},
                   ax=ax)
        
        ax.set_title(f'Spearman Correlation Matrix - {tool_name}\n(n={len(correlation_df)} PRs)',
                    fontsize=14, weight='bold', pad=20)
        
        # Ajusta labels
        labels = [col.replace('_', ' ').title() for col in available_cols]
        ax.set_xticklabels(labels, rotation=45, ha='right')
        ax.set_yticklabels(labels, rotation=0)
        
        plt.tight_layout()
        plt.savefig(f'spearman_correlation_{tool_name.lower()}.png', dpi=300, bbox_inches='tight')
        print(f"   - spearman_correlation_{tool_name.lower()}.png gerado")
        plt.close()
    
    # Cria gráfico comparativo de correlações significativas
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle('Significant Spearman Correlations by Tool (p < 0.05)', 
                fontsize=16, weight='bold')
    
    for idx, (tool_name, results) in enumerate(correlation_results.items()):
        correlations = results['correlations']
        
        # Filtra apenas correlações significativas
        sig_corrs = {k: v for k, v in correlations.items() if v.get('significant', False)}
        
        if not sig_corrs:
            axes[idx].text(0.5, 0.5, 'No significant\ncorrelations found', 
                          ha='center', va='center', fontsize=12)
            axes[idx].set_xlim(0, 1)
            axes[idx].set_ylim(0, 1)
            axes[idx].set_title(tool_name)
            axes[idx].axis('off')
            continue
        
        # Prepara dados para plotagem
        labels = []
        values = []
        colors = []
        
        for key, data in sig_corrs.items():
            # Formata label
            label = key.replace('_vs_', '\n→\n').replace('_', ' ').title()
            labels.append(label[:30])  # Limita tamanho
            
            corr = data['correlation']
            values.append(corr)
            
            # Cor baseada na força da correlação
            if abs(corr) > 0.5:
                colors.append('#d62728' if corr < 0 else '#2ca02c')  # Forte
            else:
                colors.append('#ff7f0e')  # Moderada
        
        # Plota barras horizontais
        y_pos = np.arange(len(labels))
        axes[idx].barh(y_pos, values, color=colors, alpha=0.7)
        axes[idx].set_yticks(y_pos)
        axes[idx].set_yticklabels(labels, fontsize=8)
        axes[idx].set_xlabel('Spearman ρ')
        axes[idx].set_title(f'{tool_name}\n({len(sig_corrs)} significant)', fontsize=12)
        axes[idx].axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        axes[idx].grid(axis='x', alpha=0.3)
        axes[idx].set_xlim(-1, 1)
        
        # Adiciona valores nas barras
        for i, v in enumerate(values):
            x_pos = v + 0.05 if v > 0 else v - 0.05
            ha = 'left' if v > 0 else 'right'
            axes[idx].text(x_pos, i, f'{v:.2f}', va='center', ha=ha, fontsize=9, weight='bold')
    
    plt.tight_layout()
    plt.savefig('spearman_significant_correlations.png', dpi=300, bbox_inches='tight')
    print("   - spearman_significant_correlations.png gerado")
    plt.close()


def export_correlation_results(correlation_results):
    """Exporta resultados de correlação para CSV"""
    
    print("\n14. Exportando resultados de correlação...")
    
    # DataFrame consolidado de todas as correlações
    all_correlations = []
    
    for tool_name, results in correlation_results.items():
        correlations = results['correlations']
        
        for corr_name, corr_data in correlations.items():
            all_correlations.append({
                'Tool': tool_name,
                'Correlation': corr_name,
                'Spearman_rho': corr_data['correlation'],
                'P_value': corr_data['p_value'],
                'Significant': corr_data['significant'],
                'Sample_size': corr_data['n'],
                'Strength': 'Strong' if abs(corr_data['correlation']) > 0.5 else 'Moderate' if abs(corr_data['correlation']) > 0.3 else 'Weak'
            })
    
    correlations_df = pd.DataFrame(all_correlations)
    correlations_df.to_csv('spearman_correlations_summary.csv', index=False)
    print("   - spearman_correlations_summary.csv gerado")
    
    # Exporta dados em nível de PR para cada ferramenta
    for tool_name, results in correlation_results.items():
        pr_df = results['pr_data']
        if not pr_df.empty:
            pr_df.to_csv(f'pr_level_data_{tool_name.lower()}.csv', index=False)
            print(f"   - pr_level_data_{tool_name.lower()}.csv gerado")
    
    # Cria resumo interpretativo
    print("\n" + "="*80)
    print("RESUMO DAS CORRELAÇÕES SIGNIFICATIVAS (p < 0.05)")
    print("="*80)
    
    sig_df = correlations_df[correlations_df['Significant'] == True]
    
    if sig_df.empty:
        print("\nNenhuma correlação significativa foi encontrada.")
    else:
        print(f"\nTotal de correlações significativas: {len(sig_df)}")
        print("\nPor ferramenta:")
        for tool in sig_df['Tool'].unique():
            tool_sig = sig_df[sig_df['Tool'] == tool]
            print(f"\n  {tool}: {len(tool_sig)} correlações significativas")
            for _, row in tool_sig.iterrows():
                direction = "positiva" if row['Spearman_rho'] > 0 else "negativa"
                print(f"    • {row['Correlation']}: ρ={row['Spearman_rho']:.3f} ({direction}, {row['Strength'].lower()})")
    
    return correlations_df

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
    fig.suptitle('Feedback Loop Metrics by Tool', fontsize=16)
    
    feedback_loop_df['tempo_ate_merge_hours_mean'].plot(kind='bar', ax=axes[0,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,0].set_title('Average Time to Merge (hours)')
    axes[0,0].set_ylabel('Hours')
    axes[0,0].set_xlabel('Tool')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    feedback_loop_df['numero_revisoes_mean'].plot(kind='bar', ax=axes[0,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,1].set_title('Average Number of Reviews')
    axes[0,1].set_ylabel('Reviews')
    axes[0,1].set_xlabel('Tool')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    feedback_loop_df['comentarios_ferramenta_mean'].plot(kind='bar', ax=axes[1,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,0].set_title('Average Comments per PR')
    axes[1,0].set_ylabel('Comments')
    axes[1,0].set_xlabel('Tool')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    feedback_loop_df['tempo_primeira_revisao_hours_mean'].plot(kind='bar', ax=axes[1,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,1].set_title('Average Time to First Review (hours)')
    axes[1,1].set_ylabel('Hours')
    axes[1,1].set_xlabel('Tool')
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('feedback_loop_metrics.png', dpi=300, bbox_inches='tight')
    print("   - feedback_loop_metrics.png gerado")
    
    # Cognitive Load
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Cognitive Load Metrics by Tool', fontsize=16)
    
    cognitive_load_df['conventional_commits_total'].plot(kind='bar', ax=axes[0,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,0].set_title('Total Conventional Commits')
    axes[0,0].set_ylabel('Commits')
    axes[0,0].set_xlabel('Tool')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    cognitive_load_df['arquivos_modificados_mean'].plot(kind='bar', ax=axes[0,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,1].set_title('Average Modified Files per PR')
    axes[0,1].set_ylabel('Files')
    axes[0,1].set_xlabel('Tool')
    axes[0,1].tick_params(axis='x', rotation=45)
    
    cognitive_load_df['code_churn_mean'].plot(kind='bar', ax=axes[1,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,0].set_title('Average Code Churn (commits per PR)')
    axes[1,0].set_ylabel('Commits')
    axes[1,0].set_xlabel('Tool')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    cognitive_load_df['issues_delta'].plot(kind='bar', ax=axes[1,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,1].set_title('Issues Delta (Closed - Open)')
    axes[1,1].set_ylabel('Issues')
    axes[1,1].set_xlabel('Tool')
    axes[1,1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('cognitive_load_metrics.png', dpi=300, bbox_inches='tight')
    print("   - cognitive_load_metrics.png gerado")
    
    # Flow
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Flow Metrics by Tool', fontsize=16)
    
    flow_df['total_prs'].plot(kind='bar', ax=axes[0,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,0].set_title('Total PRs')
    axes[0,0].set_ylabel('PRs')
    axes[0,0].set_xlabel('Tool')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    flow_df['merge_rate'].plot(kind='bar', ax=axes[0,1], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0,1].set_title('Merge Rate')
    axes[0,1].set_ylabel('Rate (0-1)')
    axes[0,1].set_xlabel('Tool')
    axes[0,1].set_ylim([0, 1])
    axes[0,1].tick_params(axis='x', rotation=45)
    
    flow_df['tempo_entre_commits_mean_hours'].plot(kind='bar', ax=axes[1,0], color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1,0].set_title('Average Time Between Commits (hours)')
    axes[1,0].set_ylabel('Hours')
    axes[1,0].set_xlabel('Tool')
    axes[1,0].tick_params(axis='x', rotation=45)
    axes[1,0].grid(axis='y', alpha=0.3)
    
    # Gráfico 4: Tempo até merge (corrigido)
    ax = axes[1,1]
    tools_names = flow_df.index.tolist()
    values = flow_df['tempo_ate_merge_mean_hours'].values
    bars = ax.bar(tools_names, values, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    
    # Adiciona valores em cima das barras
    for i, (bar, value) in enumerate(zip(bars, values)):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{value:.1f}h',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    ax.set_title('Average Time to Merge (hours)')
    ax.set_ylabel('Hours')
    ax.set_xlabel('Tool')
    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, max(values) * 1.15)  # Adiciona 15% de espaço para os labels
    
    plt.tight_layout()
    plt.savefig('flow_metrics.png', dpi=300, bbox_inches='tight')
    print("   - flow_metrics.png gerado")
    
    # NOVA SEÇÃO: Análise de Padrões Textuais
    print("\n6. Analisando padrões textuais...")
    text_patterns = {}
    for tool_name, data in all_data.items():
        print(f"   - Analisando padrões textuais de {tool_name}...")
        text_patterns[tool_name] = analyze_text_patterns(data)
    
    # Exibe resultados de padrões textuais
    print("\n" + "="*80)
    print("ANÁLISE DE PADRÕES TEXTUAIS")
    print("="*80)
    
    for tool_name, patterns in text_patterns.items():
        print(f"\n### {tool_name} ###")
        for category, stats in sorted(patterns.items(), key=lambda x: x[1]['count'], reverse=True):
            print(f"  {category:12} : {stats['count']:4} ocorrências ({stats['percentage']:.1f}%)")
    
    # Cria tabela de comparação
    comparison_table = create_comparison_table(text_patterns)
    comparison_table.to_csv('text_patterns_comparison.csv', index=False)
    
    print("\n" + "="*80)
    print("COMPARAÇÃO DE PADRÕES TEXTUAIS")
    print("="*80)
    print(comparison_table.to_string(index=False))
    
    # Gera gráfico radar
    print("\n7. Gerando gráfico radar de padrões textuais...")
    create_radar_chart(text_patterns, 
                      'Development Patterns Distribution by Tool',
                      'text_patterns_radar.png')
    
    # Gera gráfico de barras comparativo
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Detailed Pattern Comparison by Tool', fontsize=16, weight='bold')
    
    categories = ['fix', 'feat', 'refactor', 'docs', 'test', 'style', 'chore', 'build', 'ci', 'perf']
    
    # Gráfico 1: Top 5 categorias
    ax1 = axes[0, 0]
    top_categories = ['fix', 'feat', 'refactor', 'docs', 'test']
    x = np.arange(len(top_categories))
    width = 0.25
    
    for i, (tool_name, patterns) in enumerate(text_patterns.items()):
        counts = [patterns.get(cat, {}).get('count', 0) for cat in top_categories]
        ax1.bar(x + i*width, counts, width, label=tool_name, 
               color=['#1f77b4', '#ff7f0e', '#2ca02c'][i])
    
    ax1.set_xlabel('Category')
    ax1.set_ylabel('Count')
    ax1.set_title('Top 5 Most Frequent Categories')
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(top_categories)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Gráfico 2: Distribuição percentual
    ax2 = axes[0, 1]
    for tool_name, patterns in text_patterns.items():
        percentages = [patterns.get(cat, {}).get('percentage', 0) for cat in categories]
        ax2.plot(categories, percentages, marker='o', label=tool_name, linewidth=2)
    
    ax2.set_xlabel('Category')
    ax2.set_ylabel('Percentage (%)')
    ax2.set_title('Percentage Distribution by Category')
    ax2.legend()
    ax2.grid(alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Gráfico 3: Heatmap de contagens
    ax3 = axes[1, 0]
    heatmap_data = []
    for tool_name in text_patterns.keys():
        row = [text_patterns[tool_name].get(cat, {}).get('count', 0) for cat in categories]
        heatmap_data.append(row)
    
    im = ax3.imshow(heatmap_data, cmap='YlOrRd', aspect='auto')
    ax3.set_xticks(np.arange(len(categories)))
    ax3.set_yticks(np.arange(len(text_patterns)))
    ax3.set_xticklabels(categories)
    ax3.set_yticklabels(text_patterns.keys())
    ax3.tick_params(axis='x', rotation=45)
    
    # Adiciona valores no heatmap
    for i in range(len(text_patterns)):
        for j in range(len(categories)):
            text = ax3.text(j, i, heatmap_data[i][j],
                          ha="center", va="center", color="black", fontsize=9)
    
    ax3.set_title('Count Heatmap')
    plt.colorbar(im, ax=ax3)
    
    # Gráfico 4: Proporção total por ferramenta
    ax4 = axes[1, 1]
    totals = {}
    for tool_name, patterns in text_patterns.items():
        total = sum(p.get('count', 0) for p in patterns.values())
        totals[tool_name] = total
    
    colors_list = ['#1f77b4', '#ff7f0e', '#2ca02c']
    ax4.pie(totals.values(), labels=totals.keys(), autopct='%1.1f%%',
           colors=colors_list, startangle=90)
    ax4.set_title('Total Pattern Proportion by Tool')
    
    plt.tight_layout()
    plt.savefig('text_patterns_detailed.png', dpi=300, bbox_inches='tight')
    print("   - text_patterns_detailed.png gerado")
    
    plt.tight_layout()
    plt.savefig('text_patterns_detailed.png', dpi=300, bbox_inches='tight')
    print("   - text_patterns_detailed.png gerado")
    
    # NOVA SEÇÃO: Análise AI vs Humanos
    print("\n8. Analisando contribuições AI vs Humanos...")
    ai_vs_human_commits = {}
    ai_vs_human_comments = {}
    issue_reporters = {}
    cognitive_load_ai = {}
    issues_analysis = {}
    
    for tool_name, data in all_data.items():
        print(f"   - Analisando {tool_name}...")
        ai_vs_human_commits[tool_name] = analyze_ai_vs_human_commits(data)
        ai_vs_human_comments[tool_name] = analyze_ai_vs_human_comments(data)
        issue_reporters[tool_name] = analyze_issue_reporters(data)
        cognitive_load_ai[tool_name] = analyze_cognitive_load_with_ai(data)
        issues_analysis[tool_name] = analyze_issues_with_prs(data)
    
    # Exibe resultados
    print("\n" + "="*80)
    print("ANÁLISE AI vs HUMANOS - COMMITS")
    print("="*80)
    for tool_name, stats in ai_vs_human_commits.items():
        print(f"\n### {tool_name} ###")
        print(f"  Total commits: {stats['total_commits']}")
        print(f"  AI commits: {stats['ai_commits']} ({stats['ai_percentage']:.1f}%)")
        print(f"  Human commits: {stats['human_commits']} ({100-stats['ai_percentage']:.1f}%)")
        print(f"  Autores AI: {stats['ai_authors_count']}")
        print(f"  Autores Humanos: {stats['human_authors_count']}")
        print(f"\n  Top 5 Colaboradores Humanos (commits):")
        for author, count in stats['top_human_contributors'][:5]:
            print(f"    {author}: {count} commits")
    
    print("\n" + "="*80)
    print("ANÁLISE AI vs HUMANOS - COMENTÁRIOS")
    print("="*80)
    for tool_name, stats in ai_vs_human_comments.items():
        print(f"\n### {tool_name} ###")
        print(f"  Total comentários: {stats['total_comments']}")
        print(f"  AI comentários: {stats['ai_comments']} ({stats['ai_percentage']:.1f}%)")
        print(f"  Human comentários: {stats['human_comments']} ({100-stats['ai_percentage']:.1f}%)")
        print(f"  Reviewers AI: {stats['ai_reviewers_count']}")
        print(f"  Reviewers Humanos: {stats['human_reviewers_count']}")
        print(f"\n  Top 5 Colaboradores Humanos (comentários):")
        for reviewer, count in stats['top_human_commenters'][:5]:
            print(f"    {reviewer}: {count} comentários")
    
    print("\n" + "="*80)
    print("ANÁLISE DE ISSUE REPORTERS")
    print("="*80)
    for tool_name, stats in issue_reporters.items():
        print(f"\n### {tool_name} ###")
        print(f"  Reporters Humanos: {stats['human_reporters_count']}")
        print(f"  Issues reportadas por humanos: {stats['total_issues_by_humans']}")
        print(f"  Reporters AI: {stats['ai_reporters_count']}")
        print(f"  Issues reportadas por AI: {stats['total_issues_by_ai']}")
        print(f"\n  Top 5 Issue Reporters Humanos:")
        for reporter, count in stats['top_human_reporters'][:5]:
            print(f"    {reporter}: {count} issues")
    
    print("\n" + "="*80)
    print("CARGA COGNITIVA: PRs COM vs SEM AI")
    print("="*80)
    for tool_name, stats in cognitive_load_ai.items():
        print(f"\n### {tool_name} ###")
        print(f"  PRs COM AI:")
        print(f"    Quantidade: {stats['with_ai']['count']}")
        print(f"    Média comentários: {stats['with_ai']['avg_comments']:.2f}")
        print(f"    Média reviews: {stats['with_ai']['avg_reviews']:.2f}")
        print(f"    Média commits: {stats['with_ai']['avg_commits']:.2f}")
        print(f"    Tempo médio até merge: {stats['with_ai']['avg_time_to_merge']:.2f}h")
        print(f"\n  PRs SEM AI:")
        print(f"    Quantidade: {stats['without_ai']['count']}")
        print(f"    Média comentários: {stats['without_ai']['avg_comments']:.2f}")
        print(f"    Média reviews: {stats['without_ai']['avg_reviews']:.2f}")
        print(f"    Média commits: {stats['without_ai']['avg_commits']:.2f}")
        print(f"    Tempo médio até merge: {stats['without_ai']['avg_time_to_merge']:.2f}h")
    
    # Exporta DataFrames
    print("\n9. Exportando análises AI vs Humanos...")
    
    # Cria DataFrame de commits AI vs Humanos
    commits_comparison = []
    for tool_name, stats in ai_vs_human_commits.items():
        commits_comparison.append({
            'Ferramenta': tool_name,
            'AI_Commits': stats['ai_commits'],
            'Human_Commits': stats['human_commits'],
            'Total_Commits': stats['total_commits'],
            'AI_Percentage': stats['ai_percentage'],
            'AI_Authors': stats['ai_authors_count'],
            'Human_Authors': stats['human_authors_count']
        })
    commits_df = pd.DataFrame(commits_comparison)
    commits_df.to_csv('ai_vs_human_commits.csv', index=False)
    
    # Cria DataFrame de comentários AI vs Humanos
    comments_comparison = []
    for tool_name, stats in ai_vs_human_comments.items():
        comments_comparison.append({
            'Ferramenta': tool_name,
            'AI_Comments': stats['ai_comments'],
            'Human_Comments': stats['human_comments'],
            'Total_Comments': stats['total_comments'],
            'AI_Percentage': stats['ai_percentage'],
            'AI_Reviewers': stats['ai_reviewers_count'],
            'Human_Reviewers': stats['human_reviewers_count']
        })
    comments_df = pd.DataFrame(comments_comparison)
    comments_df.to_csv('ai_vs_human_comments.csv', index=False)
    
    # Exporta análise de issues
    for tool_name, df in issues_analysis.items():
        if not df.empty:
            df.to_csv(f'issues_analysis_{tool_name.lower()}.csv', index=False)
    
    # Exporta colaboradores mais ativos
    for tool_name, stats in ai_vs_human_commits.items():
        top_contributors_df = pd.DataFrame(stats['top_human_contributors'], 
                                          columns=['Developer', 'Commits'])
        top_contributors_df.to_csv(f'top_contributors_{tool_name.lower()}.csv', index=False)
    
    for tool_name, stats in ai_vs_human_comments.items():
        top_reviewers_df = pd.DataFrame(stats['top_human_commenters'], 
                                        columns=['Developer', 'Comments'])
        top_reviewers_df.to_csv(f'top_reviewers_{tool_name.lower()}.csv', index=False)
    
    # Gera gráficos radar AI vs Humanos
    print("\n10. Gerando gráficos radar AI vs Humanos...")
    
    # Gráfico Radar: Commits AI vs Humanos
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    categories = list(ai_vs_human_commits.keys())
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    angles += angles[:1]
    
    ai_commits_values = [ai_vs_human_commits[tool]['ai_percentage'] for tool in categories]
    human_commits_values = [100 - ai_vs_human_commits[tool]['ai_percentage'] for tool in categories]
    ai_commits_values += ai_commits_values[:1]
    human_commits_values += human_commits_values[:1]
    
    ax.plot(angles, ai_commits_values, 'o-', linewidth=2, label='AI Commits', color='#e74c3c')
    ax.fill(angles, ai_commits_values, alpha=0.25, color='#e74c3c')
    ax.plot(angles, human_commits_values, 'o-', linewidth=2, label='Human Commits', color='#3498db')
    ax.fill(angles, human_commits_values, alpha=0.25, color='#3498db')
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'])
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_title('Commits Distribution: AI vs Humans', size=16, pad=20, weight='bold')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.tight_layout()
    plt.savefig('ai_vs_human_commits_radar.png', dpi=300, bbox_inches='tight')
    print("   - ai_vs_human_commits_radar.png gerado")
    plt.close()
    
    # Gráfico Radar: Comentários AI vs Humanos
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    ai_comments_values = [ai_vs_human_comments[tool]['ai_percentage'] for tool in categories]
    human_comments_values = [100 - ai_vs_human_comments[tool]['ai_percentage'] for tool in categories]
    ai_comments_values += ai_comments_values[:1]
    human_comments_values += human_comments_values[:1]
    
    ax.plot(angles, ai_comments_values, 'o-', linewidth=2, label='AI Comments', color='#e74c3c')
    ax.fill(angles, ai_comments_values, alpha=0.25, color='#e74c3c')
    ax.plot(angles, human_comments_values, 'o-', linewidth=2, label='Human Comments', color='#3498db')
    ax.fill(angles, human_comments_values, alpha=0.25, color='#3498db')
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25%', '50%', '75%', '100%'])
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.set_title('Comments/Reviews Distribution: AI vs Humans', size=16, pad=20, weight='bold')
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.tight_layout()
    plt.savefig('ai_vs_human_comments_radar.png', dpi=300, bbox_inches='tight')
    print("   - ai_vs_human_comments_radar.png gerado")
    plt.close()
    
    # Gráfico de barras: Carga cognitiva com vs sem AI
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Cognitive Load Comparison: PRs WITH vs WITHOUT AI', fontsize=16, weight='bold')
    
    tools_list = list(cognitive_load_ai.keys())
    x = np.arange(len(tools_list))
    width = 0.35
    
    # Gráfico 1: Média de comentários
    with_ai_comments = [cognitive_load_ai[tool]['with_ai']['avg_comments'] for tool in tools_list]
    without_ai_comments = [cognitive_load_ai[tool]['without_ai']['avg_comments'] for tool in tools_list]
    
    axes[0].bar(x - width/2, with_ai_comments, width, label='With AI', color='#e74c3c')
    axes[0].bar(x + width/2, without_ai_comments, width, label='Without AI', color='#3498db')
    axes[0].set_xlabel('Tool')
    axes[0].set_ylabel('Average Comments')
    axes[0].set_title('Average Comments per PR')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(tools_list, rotation=45)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Gráfico 2: Média de reviews
    with_ai_reviews = [cognitive_load_ai[tool]['with_ai']['avg_reviews'] for tool in tools_list]
    without_ai_reviews = [cognitive_load_ai[tool]['without_ai']['avg_reviews'] for tool in tools_list]
    
    axes[1].bar(x - width/2, with_ai_reviews, width, label='With AI', color='#e74c3c')
    axes[1].bar(x + width/2, without_ai_reviews, width, label='Without AI', color='#3498db')
    axes[1].set_xlabel('Tool')
    axes[1].set_ylabel('Average Reviews')
    axes[1].set_title('Average Reviews per PR')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(tools_list, rotation=45)
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    # Gráfico 3: Média de commits
    with_ai_commits_avg = [cognitive_load_ai[tool]['with_ai']['avg_commits'] for tool in tools_list]
    without_ai_commits_avg = [cognitive_load_ai[tool]['without_ai']['avg_commits'] for tool in tools_list]
    
    axes[2].bar(x - width/2, with_ai_commits_avg, width, label='With AI', color='#e74c3c')
    axes[2].bar(x + width/2, without_ai_commits_avg, width, label='Without AI', color='#3498db')
    axes[2].set_xlabel('Tool')
    axes[2].set_ylabel('Average Commits')
    axes[2].set_title('Average Commits per PR')
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(tools_list, rotation=45)
    axes[2].legend()
    axes[2].grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('cognitive_load_ai_comparison.png', dpi=300, bbox_inches='tight')
    print("   - cognitive_load_ai_comparison.png gerado")
    plt.close()
    
    # Gráfico: Top colaboradores
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Top 10 Colaboradores Humanos por Ferramenta', fontsize=16, weight='bold')
    
    for idx, (tool_name, stats) in enumerate(ai_vs_human_commits.items()):
        top_10 = stats['top_human_contributors'][:10]
        if top_10:
            names = [item[0][:15] + '...' if len(item[0]) > 15 else item[0] for item in top_10]
            counts = [item[1] for item in top_10]
            
            axes[idx].barh(names, counts, color=['#1f77b4', '#ff7f0e', '#2ca02c'][idx])
            axes[idx].set_xlabel('Commits')
            axes[idx].set_title(tool_name)
            axes[idx].invert_yaxis()
            axes[idx].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('top_contributors_comparison.png', dpi=300, bbox_inches='tight')
    print("   - top_contributors_comparison.png gerado")
    plt.close()
    
    # NOVA SEÇÃO: Correlação de Issues com Bots
    print("\n11. Analisando correlação de Issues com PRs e Bots...")
    issues_bot_correlation = {}
    review_cycle_time = {}
    intervention_frequency = {}
    
    for tool_name, data in all_data.items():
        print(f"   - Analisando {tool_name}...")
        issues_bot_correlation[tool_name] = analyze_issues_bot_correlation(data)
        review_cycle_time[tool_name] = calculate_review_cycle_time(data)
        intervention_frequency[tool_name] = calculate_intervention_frequency(data)
    
    # Exporta correlação de issues com bots
    for tool_name, df in issues_bot_correlation.items():
        if not df.empty:
            df.to_csv(f'issues_bot_correlation_{tool_name.lower()}.csv', index=False)
            
            # Estatísticas resumidas
            with_bot = df[df['has_bot_involvement'] == True]
            without_bot = df[df['has_bot_involvement'] == False]
            
            print(f"\n### {tool_name} - Issues e Correlação com Bots ###")
            print(f"  Total issues analisadas: {len(df)}")
            print(f"  Issues com PRs que têm bot: {len(with_bot)} ({len(with_bot)/len(df)*100:.1f}%)")
            print(f"  Issues com PRs sem bot: {len(without_bot)} ({len(without_bot)/len(df)*100:.1f}%)")
            
            if len(with_bot) > 0:
                print(f"\n  PRs COM Bot:")
                print(f"    Média % commits de bot: {with_bot['bot_commits_percentage'].mean():.2f}%")
                print(f"    Média % comentários de bot: {with_bot['bot_comments_percentage'].mean():.2f}%")
                print(f"    Média % reviews de bot: {with_bot['bot_reviews_percentage'].mean():.2f}%")
            
            if len(without_bot) > 0:
                print(f"\n  PRs SEM Bot:")
                print(f"    Total commits: {without_bot['total_commits'].sum()}")
                print(f"    Total comentários: {without_bot['total_comments'].sum()}")
                print(f"    Total reviews: {without_bot['total_reviews'].sum()}")
    
    # Exibe Review Cycle Time
    print("\n" + "="*80)
    print("REVIEW CYCLE TIME (Tempo até Aprovação/Merge)")
    print("="*80)
    
    for tool_name, stats in review_cycle_time.items():
        print(f"\n### {tool_name} ###")
        print(f"  PRs COM Bot:")
        print(f"    Quantidade: {stats['with_bot']['count']}")
        print(f"    Tempo médio: {stats['with_bot']['mean_hours']:.2f}h ({stats['with_bot']['mean_hours']/24:.2f} dias)")
        print(f"    Tempo mediano: {stats['with_bot']['median_hours']:.2f}h ({stats['with_bot']['median_hours']/24:.2f} dias)")
        print(f"    Desvio padrão: {stats['with_bot']['std_hours']:.2f}h")
        print(f"    Min/Max: {stats['with_bot']['min_hours']:.2f}h / {stats['with_bot']['max_hours']:.2f}h")
        
        print(f"\n  PRs SEM Bot:")
        print(f"    Quantidade: {stats['without_bot']['count']}")
        print(f"    Tempo médio: {stats['without_bot']['mean_hours']:.2f}h ({stats['without_bot']['mean_hours']/24:.2f} dias)")
        print(f"    Tempo mediano: {stats['without_bot']['median_hours']:.2f}h ({stats['without_bot']['median_hours']/24:.2f} dias)")
        print(f"    Desvio padrão: {stats['without_bot']['std_hours']:.2f}h")
        print(f"    Min/Max: {stats['without_bot']['min_hours']:.2f}h / {stats['without_bot']['max_hours']:.2f}h")
    
    # Exporta Review Cycle Time
    cycle_time_comparison = []
    for tool_name, stats in review_cycle_time.items():
        cycle_time_comparison.append({
            'Ferramenta': tool_name,
            'Com_Bot_Count': stats['with_bot']['count'],
            'Com_Bot_Mean_Hours': stats['with_bot']['mean_hours'],
            'Com_Bot_Median_Hours': stats['with_bot']['median_hours'],
            'Com_Bot_Std_Hours': stats['with_bot']['std_hours'],
            'Sem_Bot_Count': stats['without_bot']['count'],
            'Sem_Bot_Mean_Hours': stats['without_bot']['mean_hours'],
            'Sem_Bot_Median_Hours': stats['without_bot']['median_hours'],
            'Sem_Bot_Std_Hours': stats['without_bot']['std_hours'],
        })
    cycle_time_df = pd.DataFrame(cycle_time_comparison)
    cycle_time_df.to_csv('review_cycle_time_comparison.csv', index=False)
    
    # Exibe Intervention Frequency
    print("\n" + "="*80)
    print("INTERVENTION FREQUENCY (Bot Comenta -> Humano Commita)")
    print("="*80)
    
    for tool_name, stats in intervention_frequency.items():
        print(f"\n### {tool_name} ###")
        print(f"  PRs analisados: {stats['total_prs_analyzed']}")
        print(f"  Total de intervenções detectadas: {stats['total_interventions']}")
        print(f"  Média de intervenções por PR: {stats['mean_interventions_per_pr']:.2f}")
        print(f"  Mediana de intervenções por PR: {stats['median_interventions_per_pr']:.2f}")
        print(f"  Taxa média de intervenção: {stats['mean_intervention_rate']:.2%}")
        if stats['total_prs_analyzed'] > 0:
            print(f"  PRs com pelo menos 1 intervenção: {stats['prs_with_interventions']} ({stats['prs_with_interventions']/stats['total_prs_analyzed']*100:.1f}%)")
        else:
            print(f"  PRs com pelo menos 1 intervenção: 0 (0.0%)")
    
    # Exporta Intervention Frequency
    intervention_comparison = []
    for tool_name, stats in intervention_frequency.items():
        intervention_comparison.append({
            'Ferramenta': tool_name,
            'PRs_Analisados': stats['total_prs_analyzed'],
            'Total_Intervencoes': stats['total_interventions'],
            'Media_Intervencoes_Por_PR': stats['mean_interventions_per_pr'],
            'Mediana_Intervencoes_Por_PR': stats['median_interventions_per_pr'],
            'Taxa_Media_Intervencao': stats['mean_intervention_rate'],
            'PRs_Com_Intervencoes': stats['prs_with_interventions'],
            'Percentual_PRs_Com_Intervencoes': (stats['prs_with_interventions']/stats['total_prs_analyzed']*100) if stats['total_prs_analyzed'] > 0 else 0
        })
    intervention_df = pd.DataFrame(intervention_comparison)
    intervention_df.to_csv('intervention_frequency_comparison.csv', index=False)
    
    # Gráficos adicionais
    print("\n12. Gerando gráficos de Review Cycle Time e Intervention Frequency...")
    
    # Gráfico: Review Cycle Time Comparison
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Review Cycle Time: With vs Without Bot', fontsize=16, weight='bold')
    
    tools_list = list(review_cycle_time.keys())
    x = np.arange(len(tools_list))
    width = 0.35
    
    # Tempo médio
    with_bot_mean = [review_cycle_time[tool]['with_bot']['mean_hours'] for tool in tools_list]
    without_bot_mean = [review_cycle_time[tool]['without_bot']['mean_hours'] for tool in tools_list]
    
    axes[0].bar(x - width/2, with_bot_mean, width, label='With Bot', color='#e74c3c')
    axes[0].bar(x + width/2, without_bot_mean, width, label='Without Bot', color='#3498db')
    axes[0].set_xlabel('Tool')
    axes[0].set_ylabel('Average Time (hours)')
    axes[0].set_title('Average Time to Approval/Merge')
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(tools_list, rotation=45)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    # Tempo mediano
    with_bot_median = [review_cycle_time[tool]['with_bot']['median_hours'] for tool in tools_list]
    without_bot_median = [review_cycle_time[tool]['without_bot']['median_hours'] for tool in tools_list]
    
    axes[1].bar(x - width/2, with_bot_median, width, label='With Bot', color='#e74c3c')
    axes[1].bar(x + width/2, without_bot_median, width, label='Without Bot', color='#3498db')
    axes[1].set_xlabel('Tool')
    axes[1].set_ylabel('Median Time (hours)')
    axes[1].set_title('Median Time to Approval/Merge')
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(tools_list, rotation=45)
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('review_cycle_time_comparison.png', dpi=300, bbox_inches='tight')
    print("   - review_cycle_time_comparison.png gerado")
    plt.close()
    
    # Gráfico: Intervention Frequency
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('Intervention Frequency (Bot → Human)', fontsize=16, weight='bold')
    
    # Total de intervenções
    total_interventions = [intervention_frequency[tool]['total_interventions'] for tool in tools_list]
    
    axes[0].bar(tools_list, total_interventions, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[0].set_xlabel('Tool')
    axes[0].set_ylabel('Total Interventions')
    axes[0].set_title('Total Detected Interventions')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].grid(axis='y', alpha=0.3)
    
    # Taxa de intervenção
    intervention_rates = [intervention_frequency[tool]['mean_intervention_rate']*100 for tool in tools_list]
    
    axes[1].bar(tools_list, intervention_rates, color=['#1f77b4', '#ff7f0e', '#2ca02c'])
    axes[1].set_xlabel('Tool')
    axes[1].set_ylabel('Intervention Rate (%)')
    axes[1].set_title('Average Intervention Rate per PR')
    axes[1].tick_params(axis='x', rotation=45)
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('intervention_frequency_comparison.png', dpi=300, bbox_inches='tight')
    print("   - intervention_frequency_comparison.png gerado")
    plt.close()
    
    # Gráfico: Issues com/sem Bot
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('Issues Distribution: PRs with vs without Bot', fontsize=16, weight='bold')
    
    for idx, (tool_name, df) in enumerate(issues_bot_correlation.items()):
        if not df.empty:
            with_bot = len(df[df['has_bot_involvement'] == True])
            without_bot = len(df[df['has_bot_involvement'] == False])
            
            axes[idx].pie([with_bot, without_bot], 
                         labels=['With Bot', 'Without Bot'],
                         autopct='%1.1f%%',
                         colors=['#e74c3c', '#3498db'],
                         startangle=90)
            axes[idx].set_title(f'{tool_name}\n({len(df)} issues)')
    
    plt.tight_layout()
    plt.savefig('issues_bot_distribution.png', dpi=300, bbox_inches='tight')
    print("   - issues_bot_distribution.png gerado")
    plt.close()
    
    # NOVA SEÇÃO: Análise de Correlação de Spearman
    correlation_results = calculate_spearman_correlations(all_data)
    create_correlation_heatmaps(correlation_results)
    export_correlation_results(correlation_results)
    
    print("\n" + "="*80)
    print("ANÁLISE COMPLETA FINALIZADA!")
    print("="*80)
    print("\nArquivos CSV gerados:")
    print("  - feedback_loop_metrics.csv")
    print("  - cognitive_load_metrics.csv")
    print("  - flow_metrics.csv")
    print("  - profile_metrics.csv")
    print("  - summary_comparison.csv")
    print("  - text_patterns_comparison.csv")
    print("  - ai_vs_human_commits.csv")
    print("  - ai_vs_human_comments.csv")
    print("  - issues_analysis_[tool].csv (3 arquivos)")
    print("  - issues_bot_correlation_[tool].csv (3 arquivos)")
    print("  - review_cycle_time_comparison.csv")
    print("  - intervention_frequency_comparison.csv")
    print("  - top_contributors_[tool].csv (3 arquivos)")
    print("  - top_reviewers_[tool].csv (3 arquivos)")
    print("  - spearman_correlations_summary.csv")
    print("  - pr_level_data_[tool].csv (3 arquivos)")
    print("\nGráficos PNG gerados:")
    print("  - feedback_loop_metrics.png")
    print("  - cognitive_load_metrics.png")
    print("  - flow_metrics.png")
    print("  - text_patterns_radar.png")
    print("  - text_patterns_detailed.png")
    print("  - ai_vs_human_commits_radar.png")
    print("  - ai_vs_human_comments_radar.png")
    print("  - cognitive_load_ai_comparison.png")
    print("  - top_contributors_comparison.png")
    print("  - review_cycle_time_comparison.png")
    print("  - intervention_frequency_comparison.png")
    print("  - issues_bot_distribution.png")
    print("  - spearman_correlation_[tool].png (3 arquivos)")
    print("  - spearman_significant_correlations.png")
    print("="*80)

if __name__ == '__main__':
    main()
