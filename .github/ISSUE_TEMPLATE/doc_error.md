---
name: Doc error
about: Report an incorrect, incomplete, or misleading protocol specification
title: '[DOC ERROR] '
labels: bug
assignees: ''
---

## Affected Document and Section

<!-- File path and section heading where the error appears,
     e.g., "ble/packets.md — PairingKey" -->

## Incorrect or Missing Content

<!-- Quote the exact text that is wrong, or describe the omission precisely. -->

## Correct Specification

<!-- The correct text, value, or definition — with source or rationale if known. -->

## Safety Impact

<!-- Could this specification error cause incorrect firmware behaviour?
     Examples:
     - Wrong field width → firmware reads garbage
     - Missing byte ordering → implementation-defined behaviour
     - Incorrect alarm threshold range → alarm fires at wrong level
     - Missing error case → firmware has no defined response

     If yes, prefix the issue title with [SAFETY] -->

## Known Affected Implementations

<!-- Are any firmware versions or companion-app versions known to have been
     built against the incorrect specification? List git SHAs if known. -->

## References

<!-- Related firmware source files, companion-app code, hardware specs,
     or other openCCR documentation that bears on this issue. -->
