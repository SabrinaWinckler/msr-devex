# Métricas Extraídas - Análise Comparativa de Ferramentas de IA para Desenvolvimento

## 📊 RESUMO COMPLETO DAS MÉTRICAS EXTRAÍDAS

Este documento lista todas as métricas extraídas dos dados de Claude Code, GitHub Copilot e Cursor.

---

## 1. MÉTRICAS DE FEEDBACK LOOP

### 1.1 Tempo de Resposta
- **tempo_ate_merge_hours_mean**: Tempo médio (em horas) desde criação do PR até merge
- **tempo_ate_merge_hours_median**: Tempo mediano até merge
- **tempo_ate_merge_hours_std**: Desvio padrão do tempo até merge
- **tempo_ate_merge_hours_total**: Total de PRs com dados de merge

### 1.2 Revisões
- **numero_revisoes_mean**: Número médio de revisões por PR
- **numero_revisoes_median**: Número mediano de revisões
- **numero_revisoes_std**: Desvio padrão do número de revisões
- **numero_revisoes_total**: Total de PRs revisados

### 1.3 Comentários
- **comentarios_ferramenta_mean**: Média de comentários por PR
- **comentarios_ferramenta_median**: Mediana de comentários
- **comentarios_ferramenta_std**: Desvio padrão de comentários
- **comentarios_ferramenta_total**: Total de PRs com comentários

### 1.4 Tempo de Primeira Revisão
- **tempo_primeira_revisao_hours_mean**: Tempo médio até primeira revisão (horas)
- **tempo_primeira_revisao_hours_median**: Tempo mediano até primeira revisão
- **tempo_primeira_revisao_hours_std**: Desvio padrão
- **tempo_primeira_revisao_hours_total**: Total de PRs com primeira revisão

### 1.5 Review Time
- **review_time_hours_mean**: Tempo médio de revisão (horas)
- **review_time_hours_median**: Tempo mediano de revisão
- **review_time_hours_std**: Desvio padrão
- **review_time_hours_total**: Total de PRs com review time

---

## 2. MÉTRICAS DE COGNITIVE LOAD

### 2.1 Commits Convencionais
- **conventional_commits_total**: Total de commits seguindo convenção

### 2.2 Comentários Totais
- **total_comments**: Soma de todos os comentários em PRs e reviews

### 2.3 Issues
- **issues_antes**: Issues abertas (estado: open)
- **issues_depois**: Issues fechadas
- **issues_delta**: Diferença entre issues fechadas e abertas

### 2.4 Frequência de Interrupções
- **frequencia_interrupcoes_mean_hours**: Intervalo médio entre commits (horas)
- **frequencia_interrupcoes_median_hours**: Intervalo mediano entre commits

### 2.5 Arquivos Modificados
- **arquivos_modificados_mean**: Média de arquivos modificados por PR
- **arquivos_modificados_median**: Mediana de arquivos modificados

### 2.6 Code Churn
- **code_churn_mean**: Média de commits por PR
- **code_churn_median**: Mediana de commits por PR

---

## 3. MÉTRICAS DE FLOW

### 3.1 Pull Requests
- **total_prs**: Total de PRs analisados
- **prs_open**: PRs ainda abertos
- **prs_closed**: PRs fechados
- **prs_merged**: PRs mergeados
- **merge_rate**: Taxa de merge (merged/total)

### 3.2 Tempo Entre Commits
- **tempo_entre_commits_mean_hours**: Intervalo médio entre commits (horas)
- **tempo_entre_commits_median_hours**: Intervalo mediano entre commits

### 3.3 Tempo Até Merge
- **tempo_ate_merge_mean_hours**: Tempo médio até merge (horas)
- **tempo_ate_merge_median_hours**: Tempo mediano até merge

---

## 4. MÉTRICAS DE PERFIL (Desenvolvedores e Projetos)

### 4.1 Desenvolvedores
- **num_developers**: Número de desenvolvedores únicos
- **num_repos**: Número de repositórios analisados

### 4.2 Linguagens de Programação
- **unique_languages**: Quantidade de linguagens únicas usadas
- **primary_language**: Linguagem mais utilizada
- **total_stars**: Total de estrelas nos repositórios
- **total_forks**: Total de forks nos repositórios

---

## 5. MÉTRICAS DE PADRÕES TEXTUAIS

Análise de commits, reviews e comentários categorizados por tipo:

### 5.1 Categorias de Commits
Para cada categoria (fix, feat, refactor, docs, test, style, chore, build, ci, perf):
- **count**: Quantidade de ocorrências
- **percentage**: Percentual do total
- **items**: Exemplos de mensagens

### Categorias Analisadas:
- **fix**: Correções de bugs
- **feat**: Novas funcionalidades
- **refactor**: Refatorações de código
- **docs**: Documentação
- **test**: Testes
- **style**: Formatação e estilo
- **chore**: Manutenção geral
- **build**: Build e deploy
- **ci**: Integração contínua
- **perf**: Performance e otimizações

---

## 6. MÉTRICAS AI vs HUMANOS - COMMITS

### 6.1 Distribuição de Commits
- **ai_commits**: Total de commits feitos por bots/IA
- **human_commits**: Total de commits feitos por humanos
- **total_commits**: Total geral de commits
- **ai_percentage**: Percentual de commits de IA
- **ai_authors_count**: Número de bots/IA distintos
- **human_authors_count**: Número de desenvolvedores humanos distintos

### 6.2 Top Colaboradores
- **top_human_contributors**: Top 10 desenvolvedores por número de commits
- **ai_authors_list**: Lista de bots identificados
- **human_authors_sample**: Amostra de desenvolvedores humanos

---

## 7. MÉTRICAS AI vs HUMANOS - COMENTÁRIOS E REVIEWS

### 7.1 Distribuição de Comentários
- **ai_comments**: Total de comentários de bots
- **human_comments**: Total de comentários de humanos
- **total_comments**: Total geral de comentários
- **ai_percentage**: Percentual de comentários de IA
- **ai_reviewers_count**: Número de bots reviewers
- **human_reviewers_count**: Número de reviewers humanos

### 7.2 Top Reviewers
- **top_human_commenters**: Top 10 reviewers por comentários
- **ai_reviewers_list**: Lista de bots reviewers
- **human_reviewers_sample**: Amostra de reviewers humanos

---

## 8. MÉTRICAS DE ISSUE REPORTERS

### 8.1 Distribuição de Reporters
- **human_reporters_count**: Número de reporters humanos
- **ai_reporters_count**: Número de reporters bots
- **total_issues_by_humans**: Issues abertas por humanos
- **total_issues_by_ai**: Issues abertas por bots

### 8.2 Top Reporters
- **top_human_reporters**: Top 10 humanos que mais reportam issues
- **top_ai_reporters**: Top 5 bots que mais reportam issues

---

## 9. MÉTRICAS DE CARGA COGNITIVA COM IA

Comparação entre PRs COM e SEM envolvimento de ferramentas de IA:

### 9.1 PRs COM AI
- **count**: Quantidade de PRs com bot envolvido
- **avg_comments**: Média de comentários
- **avg_reviews**: Média de reviews
- **avg_commits**: Média de commits
- **avg_time_to_merge**: Tempo médio até merge (horas)

### 9.2 PRs SEM AI
- **count**: Quantidade de PRs sem bot
- **avg_comments**: Média de comentários
- **avg_reviews**: Média de reviews
- **avg_commits**: Média de commits
- **avg_time_to_merge**: Tempo médio até merge

---

## 10. MÉTRICAS DE CORRELAÇÃO ISSUES-BOT

Análise detalhada de issues e sua relação com PRs que têm bots:

### 10.1 Dados da Issue
- **issue_number**: Número da issue
- **issue_title**: Título da issue
- **issue_reporter**: Usuário que reportou
- **issue_state**: Estado (open/closed)
- **issue_created_at**: Data de criação
- **issue_closed_at**: Data de fechamento

### 10.2 Dados do PR Relacionado
- **pr_id**: ID do PR relacionado
- **has_bot_involvement**: Se há bot envolvido (True/False)
- **bot_names**: Nomes dos bots envolvidos

### 10.3 Métricas de Commits do PR
- **total_commits**: Total de commits no PR
- **ai_commits**: Commits feitos por bots
- **human_commits**: Commits feitos por humanos
- **bot_commits_percentage**: % de commits de bot

### 10.4 Métricas de Comentários do PR
- **total_comments**: Total de comentários
- **ai_comments**: Comentários de bots
- **human_comments**: Comentários de humanos
- **bot_comments_percentage**: % de comentários de bot

### 10.5 Métricas de Reviews do PR
- **total_reviews**: Total de reviews
- **ai_reviews**: Reviews de bots
- **human_reviews**: Reviews de humanos
- **bot_reviews_percentage**: % de reviews de bot

---

## 11. MÉTRICAS DE REVIEW CYCLE TIME

Tempo entre submissão do PR e aprovação/merge, separado por presença de bot:

### 11.1 PRs COM Bot
- **count**: Quantidade de PRs
- **mean_hours**: Tempo médio (horas)
- **median_hours**: Tempo mediano (horas)
- **std_hours**: Desvio padrão
- **min_hours**: Tempo mínimo
- **max_hours**: Tempo máximo

### 11.2 PRs SEM Bot
- **count**: Quantidade de PRs
- **mean_hours**: Tempo médio (horas)
- **median_hours**: Tempo mediano (horas)
- **std_hours**: Desvio padrão
- **min_hours**: Tempo mínimo
- **max_hours**: Tempo máximo

---

## 12. MÉTRICAS DE INTERVENTION FREQUENCY

Frequência de intervenção: bot comenta → humano commita (indica correção):

### 12.1 Dados Gerais
- **total_prs_analyzed**: Total de PRs analisados
- **total_interventions**: Total de intervenções detectadas
- **mean_interventions_per_pr**: Média de intervenções por PR
- **median_interventions_per_pr**: Mediana de intervenções por PR
- **mean_intervention_rate**: Taxa média de intervenção (%)
- **prs_with_interventions**: PRs com pelo menos 1 intervenção
- **percentual_prs_com_intervencoes**: % de PRs com intervenções

### 12.2 Detalhes por PR (DataFrame)
- **pr_id**: ID do PR
- **total_events**: Total de eventos (commits + comentários)
- **interventions**: Número de intervenções detectadas
- **intervention_rate**: Taxa de intervenção no PR

---

## 📈 RESULTADOS PRINCIPAIS

### Claude Code
- **54.2%** das issues têm PRs com bot
- Média de **15.13%** commits de bot nos PRs relacionados
- **21.0%** dos PRs têm pelo menos 1 intervenção bot→humano
- Review cycle time: **5.23 dias** (com bot) vs **5.23 dias** (sem bot)

### GitHub Copilot
- **99.9%** das issues têm PRs com bot (altíssima automação!)
- Média de **88.82%** commits de bot nos PRs relacionados
- **13.3%** dos PRs têm intervenções
- Review cycle time: **2.67 dias** (com bot) vs **0.13 dias** (sem bot)

### Cursor
- **97.2%** das issues têm PRs com bot
- Média de **71.23%** commits de bot nos PRs relacionados
- **60.4%** dos commits são de IA (maior proporção)
- **63.8%** dos comentários são de IA

---

## 📁 ARQUIVOS GERADOS

### CSVs (18 arquivos):
1. `feedback_loop_metrics.csv`
2. `cognitive_load_metrics.csv`
3. `flow_metrics.csv`
4. `profile_metrics.csv`
5. `summary_comparison.csv`
6. `text_patterns_comparison.csv`
7. `ai_vs_human_commits.csv`
8. `ai_vs_human_comments.csv`
9. `issues_bot_correlation_claude_code.csv`
10. `issues_bot_correlation_copilot.csv`
11. `issues_bot_correlation_cursor.csv`
12. `review_cycle_time_comparison.csv`
13. `intervention_frequency_comparison.csv`
14. `top_contributors_claude_code.csv`
15. `top_contributors_copilot.csv`
16. `top_contributors_cursor.csv`
17. `top_reviewers_claude_code.csv`
18. `top_reviewers_copilot.csv`
19. `top_reviewers_cursor.csv`
20. `issues_analysis_claude_code.csv`
21. `issues_analysis_copilot.csv`
22. `issues_analysis_cursor.csv`

### Gráficos (12 arquivos):
1. `feedback_loop_metrics.png`
2. `cognitive_load_metrics.png`
3. `flow_metrics.png`
4. `text_patterns_radar.png`
5. `text_patterns_detailed.png`
6. `ai_vs_human_commits_radar.png`
7. `ai_vs_human_comments_radar.png`
8. `cognitive_load_ai_comparison.png`
9. `top_contributors_comparison.png`
10. `review_cycle_time_comparison.png`
11. `intervention_frequency_comparison.png`
12. `issues_bot_distribution.png`

---

## 🎯 INSIGHTS CHAVE

### 1. Correlação Issues-Bot
- **Copilot** tem quase 100% de issues relacionadas a PRs com bots
- **Cursor** tem 71% de commits feitos por bots nos PRs
- **Claude Code** tem maior equilíbrio: 54% de issues com bot, apenas 15% dos commits

### 2. Review Cycle Time
- PRs **com bot** no Copilot levam **20x mais tempo** que sem bot (2.67 dias vs 0.13 dias)
- Claude Code mantém tempo similar com ou sem bot (~5 dias)

### 3. Intervention Frequency
- **Claude Code**: 21% dos PRs têm intervenções (bot comenta → humano corrige)
- **Copilot**: 13.3% dos PRs têm intervenções
- Média de **0.33 intervenções/PR** no Claude Code vs **0.18** no Copilot

### 4. Carga Cognitiva
- PRs **com AI** recebem **3x mais comentários** e reviews
- Sugestão: AI estimula mais discussão e refinamento

---

## 🔬 MÉTRICAS PARA TRIANGULAÇÃO

Todas essas métricas podem ser cruzadas para análises mais profundas:
- Correlacionar **intervention frequency** com **cognitive load**
- Comparar **review cycle time** entre ferramentas
- Analisar impacto de **bot percentage** no **merge rate**
- Triangular **issue reporters** com **PR contributors**
- Relacionar **text patterns** com **AI involvement**

**Total de métricas únicas extraídas: 150+**
