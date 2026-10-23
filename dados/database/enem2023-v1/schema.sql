CREATE UNIQUE INDEX idx_participantes_id ON participantes ("NU_INSCRICAO");

CREATE INDEX idx_particoes_conjunto ON particoes(partition, validation_fold);

CREATE TABLE "agregados_desenvolvimento" (
"SG_UF_PROVA" TEXT,
  "TP_ESCOLA" TEXT,
  "TP_SEXO" TEXT,
  "IN_TREINEIRO" TEXT,
  "Q006" TEXT,
  "score_bin" INTEGER,
  "count" INTEGER,
  "score_sum" REAL,
  "score_sum_squared" REAL,
  "zeros" INTEGER,
  "minimum" REAL,
  "maximum" REAL
);

CREATE TABLE "associacoes_entradas" (
"variable_a" TEXT,
  "variable_b" TEXT,
  "metric" TEXT,
  "value" REAL,
  "value_with_missing_category" REAL,
  "n" INTEGER,
  "n_observed" INTEGER,
  "missing_either" INTEGER
);

CREATE TABLE "cruzamentos" (
"variable_a" TEXT,
  "variable_b" TEXT,
  "code_a" TEXT,
  "code_b" TEXT,
  "n" INTEGER,
  "mean" REAL,
  "std" REAL,
  "zeros" INTEGER
);

CREATE TABLE "dicionario" (
"variavel" TEXT,
  "descricao" TEXT,
  "tipo_declarado" TEXT,
  "alternativas_json" TEXT
);

CREATE TABLE "dobras_cv" (
"model" TEXT,
  "evaluated_set" TEXT,
  "fold" INTEGER,
  "rmse" REAL,
  "mae" REAL,
  "r2" REAL,
  "n_train" INTEGER,
  "n_evaluated" INTEGER
);

CREATE TABLE metadados(chave TEXT PRIMARY KEY, valor TEXT NOT NULL);

CREATE TABLE participantes ("NU_INSCRICAO" TEXT NOT NULL, "NU_ANO" REAL, "TP_FAIXA_ETARIA" TEXT, "TP_SEXO" TEXT, "TP_ESTADO_CIVIL" TEXT, "TP_COR_RACA" TEXT, "TP_NACIONALIDADE" TEXT, "TP_ST_CONCLUSAO" TEXT, "TP_ANO_CONCLUIU" TEXT, "TP_ESCOLA" TEXT, "TP_ENSINO" TEXT, "IN_TREINEIRO" TEXT, "CO_MUNICIPIO_ESC" TEXT, "NO_MUNICIPIO_ESC" TEXT, "CO_UF_ESC" TEXT, "SG_UF_ESC" TEXT, "TP_DEPENDENCIA_ADM_ESC" TEXT, "TP_LOCALIZACAO_ESC" TEXT, "TP_SIT_FUNC_ESC" TEXT, "CO_MUNICIPIO_PROVA" TEXT, "NO_MUNICIPIO_PROVA" TEXT, "CO_UF_PROVA" TEXT, "SG_UF_PROVA" TEXT, "TP_PRESENCA_CN" TEXT, "TP_PRESENCA_CH" TEXT, "TP_PRESENCA_LC" TEXT, "TP_PRESENCA_MT" TEXT, "CO_PROVA_CN" TEXT, "CO_PROVA_CH" TEXT, "CO_PROVA_LC" TEXT, "CO_PROVA_MT" TEXT, "NU_NOTA_CN" REAL, "NU_NOTA_CH" REAL, "NU_NOTA_LC" REAL, "NU_NOTA_MT" REAL, "TX_RESPOSTAS_CN" TEXT, "TX_RESPOSTAS_CH" TEXT, "TX_RESPOSTAS_LC" TEXT, "TX_RESPOSTAS_MT" TEXT, "TP_LINGUA" TEXT, "TX_GABARITO_CN" TEXT, "TX_GABARITO_CH" TEXT, "TX_GABARITO_LC" TEXT, "TX_GABARITO_MT" TEXT, "TP_STATUS_REDACAO" TEXT, "NU_NOTA_COMP1" TEXT, "NU_NOTA_COMP2" TEXT, "NU_NOTA_COMP3" TEXT, "NU_NOTA_COMP4" TEXT, "NU_NOTA_COMP5" TEXT, "NU_NOTA_REDACAO" REAL, "Q001" TEXT, "Q002" TEXT, "Q003" TEXT, "Q004" TEXT, "Q005" TEXT, "Q006" TEXT, "Q007" TEXT, "Q008" TEXT, "Q009" TEXT, "Q010" TEXT, "Q011" TEXT, "Q012" TEXT, "Q013" TEXT, "Q014" TEXT, "Q015" TEXT, "Q016" TEXT, "Q017" TEXT, "Q018" TEXT, "Q019" TEXT, "Q020" TEXT, "Q021" TEXT, "Q022" TEXT, "Q023" TEXT, "Q024" TEXT, "Q025" TEXT);

CREATE TABLE particoes ("NU_INSCRICAO" TEXT PRIMARY KEY REFERENCES participantes("NU_INSCRICAO"), partition TEXT NOT NULL CHECK(partition IN ('development','test')), validation_fold INTEGER, CHECK((partition='test' AND validation_fold IS NULL) OR (partition='development' AND validation_fold IN (0,1,2)))) WITHOUT ROWID;

CREATE TABLE "perfis" (
"variable" TEXT,
  "code" TEXT,
  "label" TEXT,
  "n" INTEGER,
  "mean" REAL,
  "std" REAL,
  "zeros" INTEGER
);

CREATE TABLE "relacoes_alvo" (
"variable" TEXT,
  "label" TEXT,
  "description" TEXT,
  "kind" TEXT,
  "n" INTEGER,
  "n_observed" INTEGER,
  "missing" INTEGER,
  "groups_observed" INTEGER,
  "eta_squared" REAL,
  "eta_squared_all" REAL,
  "pearson" REAL,
  "spearman" REAL
);

CREATE TABLE "resumo_cv" (
"model" TEXT,
  "evaluated_set" TEXT,
  "n_splits" INTEGER,
  "elapsed_seconds" REAL,
  "std_ddof" INTEGER,
  "warning_count" INTEGER,
  "rmse_mean" REAL,
  "rmse_std" REAL,
  "mae_mean" REAL,
  "mae_std" REAL,
  "r2_mean" REAL,
  "r2_std" REAL
);

CREATE VIEW contagens_particoes AS SELECT partition, COUNT(*) AS participantes FROM particoes GROUP BY partition;

CREATE VIEW desenvolvimento AS SELECT p."NU_INSCRICAO", p."NU_NOTA_CN", p."Q005", p."TP_FAIXA_ETARIA", p."TP_SEXO", p."TP_ESTADO_CIVIL", p."TP_COR_RACA", p."TP_NACIONALIDADE", p."TP_ST_CONCLUSAO", p."TP_ANO_CONCLUIU", p."TP_ESCOLA", p."TP_ENSINO", p."IN_TREINEIRO", p."TP_DEPENDENCIA_ADM_ESC", p."TP_LOCALIZACAO_ESC", p."TP_SIT_FUNC_ESC", p."SG_UF_PROVA", p."TP_LINGUA", p."Q001", p."Q002", p."Q003", p."Q004", p."Q006", p."Q007", p."Q008", p."Q009", p."Q010", p."Q011", p."Q012", p."Q013", p."Q014", p."Q015", p."Q016", p."Q017", p."Q018", p."Q019", p."Q020", p."Q021", p."Q022", p."Q023", p."Q024", p."Q025", f.validation_fold FROM participantes p JOIN particoes f ON p."NU_INSCRICAO"=f."NU_INSCRICAO" WHERE f.partition='development';
