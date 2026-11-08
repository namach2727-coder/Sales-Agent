BEGIN;

LOCK TABLE alembic_version IN EXCLUSIVE MODE;
SELECT 1 / CASE
    WHEN count(*) = 1 AND min(version_num) = '0027_traceable_receipt_versions' THEN 1
    ELSE 0 END AS expected_revision_verified
FROM alembic_version;


-- Running upgrade 0027_traceable_receipt_versions -> 0028_seo_google_onboarding

CREATE TABLE seo_access_grants (
    id SERIAL NOT NULL, 
    tenant_id INTEGER NOT NULL, 
    store_id INTEGER NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    max_sites INTEGER NOT NULL, 
    max_connections INTEGER NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(store_id, tenant_id) REFERENCES stores (id, tenant_id), 
    CONSTRAINT uq_seo_grant_scope UNIQUE (tenant_id, store_id), 
    CONSTRAINT ck_seo_grant_sites CHECK (max_sites BETWEEN 1 AND 20), 
    CONSTRAINT ck_seo_grant_connections CHECK (max_connections BETWEEN 1 AND 10), 
    CONSTRAINT ck_seo_grant_status CHECK (status IN ('active', 'disabled')), 
    FOREIGN KEY(tenant_id) REFERENCES tenants (id)
);

CREATE TABLE seo_oauth_attempts (
    id SERIAL NOT NULL, 
    tenant_id INTEGER NOT NULL, 
    store_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    state_digest VARCHAR(64) NOT NULL, 
    session_digest VARCHAR(64) NOT NULL, 
    encrypted_verifier TEXT, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    used_at TIMESTAMP WITH TIME ZONE, 
    cancelled_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(store_id, tenant_id) REFERENCES stores (id, tenant_id), 
    FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
    FOREIGN KEY(user_id) REFERENCES user_identities (id), 
    UNIQUE (state_digest)
);

CREATE TABLE seo_google_connections (
    id SERIAL NOT NULL, 
    public_id VARCHAR(36) NOT NULL, 
    tenant_id INTEGER NOT NULL, 
    store_id INTEGER NOT NULL, 
    user_id INTEGER NOT NULL, 
    encrypted_refresh_token TEXT, 
    key_version VARCHAR(30) NOT NULL, 
    granted_scope TEXT NOT NULL, 
    consent_version VARCHAR(30) NOT NULL, 
    status VARCHAR(30) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    disconnected_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(store_id, tenant_id) REFERENCES stores (id, tenant_id), 
    CONSTRAINT uq_seo_connection_owner UNIQUE (tenant_id, store_id, user_id), 
    CONSTRAINT uq_seo_connection_scope UNIQUE (id, tenant_id, store_id), 
    CONSTRAINT ck_seo_connection_status CHECK (status IN ('connected', 'reauthorization_required', 'disconnected')), 
    FOREIGN KEY(tenant_id) REFERENCES tenants (id), 
    FOREIGN KEY(user_id) REFERENCES user_identities (id)
);

CREATE TABLE seo_sites (
    id SERIAL NOT NULL, 
    public_id VARCHAR(36) NOT NULL, 
    tenant_id INTEGER NOT NULL, 
    store_id INTEGER NOT NULL, 
    connection_id INTEGER NOT NULL, 
    property_id VARCHAR(2048) NOT NULL, 
    permission_level VARCHAR(30) NOT NULL, 
    status VARCHAR(20) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(connection_id, tenant_id, store_id) REFERENCES seo_google_connections (id, tenant_id, store_id), 
    CONSTRAINT uq_seo_site_property UNIQUE (tenant_id, store_id, property_id), 
    CONSTRAINT ck_seo_site_status CHECK (status IN ('connected', 'disconnected', 'permission_lost'))
);

CREATE INDEX ix_seo_access_grants_tenant_id ON seo_access_grants (tenant_id);

CREATE INDEX ix_seo_access_grants_store_id ON seo_access_grants (store_id);

CREATE INDEX ix_seo_oauth_attempts_tenant_id ON seo_oauth_attempts (tenant_id);

CREATE INDEX ix_seo_oauth_attempts_store_id ON seo_oauth_attempts (store_id);

CREATE INDEX ix_seo_google_connections_tenant_id ON seo_google_connections (tenant_id);

CREATE INDEX ix_seo_google_connections_store_id ON seo_google_connections (store_id);

CREATE INDEX ix_seo_sites_tenant_id ON seo_sites (tenant_id);

CREATE INDEX ix_seo_sites_store_id ON seo_sites (store_id);

CREATE INDEX ix_seo_oauth_attempts_user_id ON seo_oauth_attempts (user_id);

CREATE INDEX ix_seo_google_connections_user_id ON seo_google_connections (user_id);

CREATE UNIQUE INDEX ix_seo_google_connections_public_id ON seo_google_connections (public_id);

CREATE UNIQUE INDEX ix_seo_sites_public_id ON seo_sites (public_id);

CREATE INDEX ix_seo_sites_connection_id ON seo_sites (connection_id);

UPDATE alembic_version SET version_num='0028_seo_google_onboarding' WHERE alembic_version.version_num = '0027_traceable_receipt_versions';

-- Running upgrade 0028_seo_google_onboarding -> 0029_seo_pilot_revision

ALTER TABLE seo_access_grants ADD COLUMN revision INTEGER DEFAULT '1' NOT NULL;

ALTER TABLE seo_access_grants ADD CONSTRAINT ck_seo_grant_revision CHECK (revision >= 1);

UPDATE alembic_version SET version_num='0029_seo_pilot_revision' WHERE alembic_version.version_num = '0028_seo_google_onboarding';

COMMIT;

