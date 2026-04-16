"""Pipeline configuration: Secrets Manager, S3, region. No hardcoded credentials."""

import os

AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", AWS_REGION)

SECRETS_MANAGER_SECRET_ID = os.environ.get(
    "AXONAI_DB_SECRET_ID", "axonai/db/credentials"
)

S3_BUCKET = os.environ.get(
    "AXONAI_MODEL_ARTIFACTS_BUCKET", "axonai-model-artifacts-924300129944"
)

# RDS endpoint (may also appear inside the secret as `host`)
DEFAULT_DB_HOST = os.environ.get(
    "AXONAI_DB_HOST",
    "axonai-db-prod.cl6susyag7hl.ap-southeast-2.rds.amazonaws.com",
)

# Application database name (secret may override with `dbname` / `database`)
DEFAULT_DB_NAME = os.environ.get("AXONAI_DB_NAME", "axonai")

MIN_STUDENTS_TO_TRAIN = int(os.environ.get("AXONAI_ML_MIN_STUDENTS", "5"))
