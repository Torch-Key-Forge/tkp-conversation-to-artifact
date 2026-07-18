$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

python -m pip install -e ".[dev]"
python -m pytest -q

if (Test-Path ".\public-output") {
    Remove-Item ".\public-output" -Recurse -Force
}

python -m tkp_conversation_to_artifact `
    ".\fixtures\sanitized_normalized_conversation.json" `
    ".\fixtures\sanitized_authority_intelligence.json" `
    ".\public-output"
