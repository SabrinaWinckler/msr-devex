# Explicação da Estrutura dos Dados - AI Teammates in SE

## Estrutura Geral

Os dados estão organizados em três pastas principais:
- `claude_code/` - Dados de projetos usando Claude Code
- `copilot/` - Dados de projetos usando GitHub Copilot  
- `cursor/` - Dados de projetos usando Cursor

Cada pasta contém os mesmos tipos de arquivos com dados coletados do GitHub.

---

## Arquivos e Seus Significados

### 1. **prs.json** - Pull Requests
Lista completa de PRs com informações detalhadas:
- `id`, `number`: Identificadores do PR
- `title`, `body`: Título e descrição
- `user`: Autor do PR
- `state`: Estado (open/closed)
- `created_at`, `updated_at`, `closed_at`: Timestamps
- `merged_at`: Data de merge (se aplicável)
- `comments`: Número de comentários
- Indica se o PR foi gerado com ajuda da ferramenta de IA (geralmente no body com tags como "🤖 Generated with Claude Code")

### 2. **pr_commits.json** - Commits dos PRs
Organizado por PR ID (formato: `{pr_id}.json`):
- Lista de commits de cada PR
- Para cada commit:
  - `sha`: Hash único do commit
  - `commit.message`: Mensagem do commit
  - `commit.author`: Autor e data
  - `commit.committer`: Quem fez o commit
  - Útil para calcular **frequência de commits** e **code churn**

### 3. **pr_reviews.json** - Revisões dos PRs
Organizado por PR ID:
- Revisões formais feitas no PR
- `user`: Quem fez a revisão
- `state`: APPROVED, CHANGES_REQUESTED, COMMENTED
- `submitted_at`: Quando foi submetida
- `body`: Comentário da revisão
- Permite calcular **tempo até primeira revisão** e **número de revisões**

### 4. **pr_review_comments.json** - Comentários em Código
Comentários específicos em linhas de código:
- `path`: Arquivo comentado
- `position`: Posição no diff
- `body`: Texto do comentário
- `user`: Quem comentou
- `created_at`: Data do comentário
- Muitos desses comentários são da ferramenta de IA sugerindo melhorias

### 5. **pr_comments.json** - Comentários Gerais
Comentários gerais no PR (não em código específico):
- Discussões sobre o PR
- Comentários de bots (CI/CD, ferramentas de IA)
- `user`: Autor do comentário
- `body`: Conteúdo
- `created_at`: Data

### 6. **pr_timelines.json** - Timeline de Eventos
Eventos cronológicos do PR:
- `event`: Tipo de evento (committed, merged, closed, review_requested, etc.)
- `created_at`: Quando ocorreu
- `actor`: Quem realizou a ação
- `commit_id`: ID do commit (quando aplicável)
- Útil para análise de **flow** e **interrupções**

### 7. **issues.json** - Issues Relacionadas
Issues do repositório:
- `number`, `title`: Identificação
- `state`: open/closed
- `created_at`, `closed_at`: Datas
- `body`: Descrição
- `assignee`: Responsável
- Permite avaliar **issues antes/depois** do uso da ferramenta

### 8. **developer_metadata.json** - Perfil dos Desenvolvedores
Metadados dos desenvolvedores:
- `login`: Username no GitHub
- `name`: Nome completo
- `company`, `location`: Informações profissionais
- `public_repos`, `followers`: Métricas públicas
- `created_at`: Quando entrou no GitHub
- Para **caracterizar o perfil** dos desenvolvedores

### 9. **repo_metadata.json** - Metadados dos Repositórios
Informações dos repositórios:
- `name`, `full_name`: Nome do repo
- `language`: Linguagem principal
- `stargazers_count`, `forks_count`: Popularidade
- `size`: Tamanho do repo
- `created_at`, `pushed_at`: Datas
- `topics`: Tags do projeto
- Para **caracterizar os projetos**

### 10. **gpt_conventional_commits.csv** - Commits Convencionais
Commits classificados por tipo convencional:
- `agent`: Ferramenta usada
- `id`: ID do PR
- `title`: Título do commit
- `type`: fix, feat, refactor, docs, etc.
- `confidence`: Confiança da classificação
- Identifica **conventional commits** gerados pela IA

### 11. **prs.csv** - PRs em Formato Tabular
Versão simplificada de prs.json em CSV:
- Facilita análise com pandas
- Campos principais: id, number, title, user, state, datas

### 12. **related_issues.csv** - Relacionamento PR-Issue
Liga PRs às issues que resolvem:
- `agent`: Ferramenta
- `pr_id`, `pr_number`: Identificação do PR
- `issue_number`: Issue relacionada
- `source`: De onde veio a relação (body, commit message)

---

## Métricas Extraídas

### **Feedback Loop**
1. **Tempo até merge**: `closed_at - created_at` (de prs.json)
2. **Número de revisões**: Contagem em pr_reviews.json
3. **Comentários da ferramenta**: Soma de pr_comments + pr_review_comments
4. **Tempo até primeira revisão**: `primeira_review.submitted_at - pr.created_at`
5. **Review time**: Tempo desde criação até última revisão

### **Cognitive Load**
1. **Conventional commits**: Contagem em gpt_conventional_commits.csv
2. **Comentários totais**: Soma de todos os comentários
3. **Issues antes/depois**: Issues abertas vs fechadas
4. **Frequência de interrupções**: Intervalo médio entre commits
5. **Arquivos modificados**: Estimativa por commit message
6. **Code churn**: Número de commits por PR

### **Flow**
1. **Total de PRs**: Contagem total
2. **Taxa de merge**: PRs merged / total PRs
3. **Tempo entre commits**: Intervalo global entre commits
4. **Tempo até merge**: Média do tempo até merge

### **Perfil**
1. **Desenvolvedores**: Contagem única
2. **Repositórios**: Número de repos
3. **Linguagens**: Linguagens usadas
4. **Popularidade**: Stars e forks totais

---

## Como Usar

Execute o script Python:
```bash
python analyze_ai_tools.py
```

Ou use o Jupyter Notebook:
```bash
jupyter notebook load_AIDev.ipynb
```

Os resultados serão salvos em arquivos CSV e gráficos PNG para comparação entre as três ferramentas.
