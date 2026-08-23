# Security and integrity policy

## Supported scope

The current repository contains a static architecture packet, schemas, synthetic fixtures, an index builder, and an offline validator. It contains no product service, model runtime, vehicle connection, credential path, or private data pipeline.

Security support applies to the current default branch. Historical candidate bytes remain useful for provenance but do not receive corrective edits.

## Reporting

Use GitHub's private vulnerability reporting feature for issues that could expose secrets, conceal an indexed artifact, bypass a fail closed rule, execute unauthorized code, introduce a network or write path, corrupt evidence provenance, or forge an acceptance record.

Do not disclose an active exploit, leaked credential, or sensitive payload in a public issue. For non sensitive scientific or documentation defects, open a normal issue with a minimal reproducible example.

## Response boundary

A repository fix can correct architecture or validation logic. It cannot establish scientific validity, operational safety, standards compliance, legal advice, or operator acceptance. Material corrections create a new versioned record and preserve the affected prior state.
