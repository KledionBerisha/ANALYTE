<!-- E gjeneruar nga scripts/build_appendices.py. Mos e ndrysho me dorë: ndrysho burimin dhe rigjenero. -->

## Shtojca G — Skema SQL e bazës së të dhënave

Skema PostgreSQL e ndërtuar nga modelet (`persistence/tables.py`): 16 tabela. Migrimet Alembic (`backend/alembic/versions/`) e prodhojnë të njëjtën skemë; një test krahason rezultatin e tyre me modelet. Terminologjia dhe intervalet referente nuk janë në bazë (`resources/` është burimi i vetëm).

```sql
CREATE TABLE audit_events (
	id SERIAL NOT NULL, 
	document_id UUID, 
	user_id UUID, 
	event_type VARCHAR(60) NOT NULL, 
	payload JSON NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_audit_events_document_created ON audit_events (document_id, created_at);

CREATE TABLE login_failures (
	id SERIAL NOT NULL, 
	email_key VARCHAR(64) NOT NULL, 
	ip_key VARCHAR(64) NOT NULL, 
	at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_login_failures_email_at ON login_failures (email_key, at);

CREATE INDEX ix_login_failures_ip_at ON login_failures (ip_key, at);

CREATE TABLE users (
	id UUID NOT NULL, 
	email VARCHAR(320) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE TABLE auth_sessions (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	revoked_reason VARCHAR(30), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_auth_sessions_user_id ON auth_sessions (user_id);

CREATE TABLE documents (
	id UUID NOT NULL, 
	user_id UUID NOT NULL, 
	filename_encrypted BYTEA NOT NULL, 
	mime VARCHAR(100) NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	storage_path VARCHAR(255) NOT NULL, 
	uploaded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	channel VARCHAR(20), 
	state VARCHAR(30) NOT NULL, 
	state_reason TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX ix_documents_user_id ON documents (user_id);

CREATE TABLE cross_references (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	analyte_code VARCHAR(20) NOT NULL, 
	state VARCHAR(30) NOT NULL, 
	assertion_id UUID, 
	finding_id UUID, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_cross_references_document_id ON cross_references (document_id);

CREATE TABLE document_glossary (
	id SERIAL NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	term VARCHAR(200) NOT NULL, 
	explanation_sq TEXT NOT NULL, 
	source_ref TEXT NOT NULL, 
	category VARCHAR(100), 
	synonyms JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_document_glossary_document_id ON document_glossary (document_id);

CREATE TABLE document_unexplained_terms (
	id SERIAL NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	term VARCHAR(200) NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_document_unexplained_terms_document_id ON document_unexplained_terms (document_id);

CREATE TABLE explanations (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	attempt INTEGER NOT NULL, 
	generator VARCHAR(200) NOT NULL, 
	prompt_version VARCHAR(50), 
	raw_output TEXT, 
	final_output TEXT, 
	is_fallback BOOLEAN NOT NULL, 
	delivered BOOLEAN NOT NULL, 
	error TEXT, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_explanations_document_id ON explanations (document_id);

CREATE TABLE lab_findings (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	analyte_code VARCHAR(20) NOT NULL, 
	analyte_name_raw VARCHAR(200) NOT NULL, 
	analyte_name_canonical VARCHAR(200) NOT NULL, 
	value_raw VARCHAR(64) NOT NULL, 
	value VARCHAR(64) NOT NULL, 
	unit_raw VARCHAR(40), 
	unit_canonical VARCHAR(40) NOT NULL, 
	value_canonical VARCHAR(64) NOT NULL, 
	ref_low VARCHAR(64), 
	ref_high VARCHAR(64), 
	ref_source VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	severity VARCHAR(64), 
	page INTEGER NOT NULL, 
	bbox JSON, 
	measured_at DATE, 
	flag_in_document VARCHAR(10), 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_lab_findings_document_analyte ON lab_findings (document_id, analyte_code);

CREATE TABLE pattern_observations (
	id SERIAL NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	pattern_id VARCHAR(20) NOT NULL, 
	finding_ids JSON NOT NULL, 
	source_ref TEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_pattern_observations_document_id ON pattern_observations (document_id);

CREATE TABLE processing_jobs (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	state VARCHAR(30) NOT NULL, 
	attempt INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	started_at TIMESTAMP WITH TIME ZONE, 
	finished_at TIMESTAMP WITH TIME ZONE, 
	error TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_processing_jobs_document_id ON processing_jobs (document_id);

CREATE TABLE refresh_tokens (
	id UUID NOT NULL, 
	session_id UUID NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	used_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES auth_sessions (id) ON DELETE CASCADE
);

CREATE INDEX ix_refresh_tokens_session_id ON refresh_tokens (session_id);

CREATE TABLE report_assertions (
	id UUID NOT NULL, 
	document_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	text_span TEXT NOT NULL, 
	analyte_code VARCHAR(20), 
	direction VARCHAR(20) NOT NULL, 
	polarity VARCHAR(20) NOT NULL, 
	certainty VARCHAR(20) NOT NULL, 
	kind VARCHAR(20) NOT NULL, 
	char_start INTEGER NOT NULL, 
	char_end INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(document_id) REFERENCES documents (id) ON DELETE CASCADE
);

CREATE INDEX ix_report_assertions_document_id ON report_assertions (document_id);

CREATE TABLE verification_results (
	id UUID NOT NULL, 
	explanation_id UUID NOT NULL, 
	mode VARCHAR(30) NOT NULL, 
	passed BOOLEAN NOT NULL, 
	rules_version VARCHAR(20) NOT NULL, 
	classifier_version VARCHAR(200), 
	duration_ms INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (explanation_id), 
	FOREIGN KEY(explanation_id) REFERENCES explanations (id) ON DELETE CASCADE
);

CREATE TABLE violations (
	id UUID NOT NULL, 
	verification_result_id UUID NOT NULL, 
	position INTEGER NOT NULL, 
	type VARCHAR(40) NOT NULL, 
	detected_by VARCHAR(20) NOT NULL, 
	sentence TEXT NOT NULL, 
	evidence TEXT NOT NULL, 
	confidence FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(verification_result_id) REFERENCES verification_results (id) ON DELETE CASCADE
);

CREATE INDEX ix_violations_verification_result_id ON violations (verification_result_id);
```
