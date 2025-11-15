# Research Findings: Test Suites Improvements

**Feature Branch**: `015-test-suite-improvements` | **Date**: 2025-11-11 | **Plan**: /Users/jlim/Projects/CollabIQ/specs/015-test-suite-improvements/plan.md

## Overview

This document outlines initial research considerations for enhancing the CollabIQ project's test suites. Given the detailed nature of the feature specification, explicit `NEEDS CLARIFICATION` markers were not present in the technical context. However, this section serves to document general best practices and potential tools/approaches for the planned improvements.

## Research Areas & Considerations

### 1. Automated E2E Testing with Real External Services (Gmail, Notion)

**Decision**: Leverage `pytest` fixtures for setup and teardown of real external service interactions.
**Rationale**: `pytest` fixtures provide a robust and flexible way to manage resources (like test Gmail accounts and Notion databases) before and after tests. This allows for controlled interaction with real services while ensuring proper cleanup.
**Alternatives Considered**: Manual setup/teardown (rejected due to increased overhead and potential for missed cleanup), dedicated test environments (more complex than necessary for current scope).

### 2. Date Parsing and Normalization Libraries in Python

**Decision**: Investigate and potentially adopt a specialized Python library for date parsing and normalization.
**Rationale**: The `spec.md` highlights struggles with date extraction. A dedicated library can offer more robust parsing capabilities, handle various formats (including Korean), and manage edge cases more effectively than custom regex or basic `datetime` operations.
**Alternatives Considered**: Custom parsing logic (rejected due to complexity and potential for bugs), relying solely on LLM extraction (rejected due to observed inaccuracies).

### 3. LLM Benchmarking and Prompt Engineering Strategies

**Decision**: Implement a systematic benchmarking approach for LLM performance and explore prompt engineering techniques.
**Rationale**: To optimize LLM performance for Korean text, a structured approach is needed. Benchmarking will provide measurable data, and prompt engineering can significantly influence extraction quality.
**Alternatives Considered**: Ad-hoc testing (rejected due to lack of reproducibility and comparability), relying on default LLM behavior (rejected due to observed performance gaps).

### 4. Granular Code Coverage Reporting with `pytest-cov`

**Decision**: Configure `pytest-cov` to generate separate coverage reports for different test types.
**Rationale**: `pytest-cov` is the established tool for code coverage in the project. Its configuration options allow for generating distinct reports, which will provide granular insights into coverage per test layer (unit, integration, E2E).
**Alternatives Considered**: Manual analysis of coverage (rejected due to inefficiency and error proneness), using other coverage tools (rejected to maintain consistency with existing project setup).

### 5. Performance Testing Frameworks and Methodologies in Python

**Decision**: Integrate a performance testing approach within the `pytest` framework or a lightweight dedicated library.
**Rationale**: Formalizing performance testing requires consistent measurement and assertion. Leveraging `pytest` for this can keep the testing infrastructure unified. For more complex scenarios, a lightweight library might be considered.
**Alternatives Considered**: Heavy-duty load testing tools (rejected as overkill for current scope), manual timing (rejected due to lack of automation and consistency).

### 6. Fuzz Testing Tools and Techniques in Python

**Decision**: Explore Python-based fuzzing libraries for input parsing and data validation.
**Rationale**: Fuzz testing is crucial for uncovering unexpected vulnerabilities and edge-case bugs. Python offers several libraries that can be integrated into the existing test suite.
**Alternatives Considered**: Manual creation of edge cases (rejected due to limited scope and human error), external fuzzing services (rejected due to complexity and cost for current scope).