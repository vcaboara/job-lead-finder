# Patent Analysis Framework - AI Instructions

## Project Overview
Patent analysis framework focused on pyrolysis technologies and waste-to-energy systems. Analyzes patent claims for technical validity, prior art conflicts, and commercial viability.

## Core Capabilities
- Patent claim parsing and analysis
- Prior art search (Google Patents integration)
- Technical feasibility evaluation for pyrolysis systems
- Patent claim drafting assistance
- Market and commercialization assessment

## Technology Stack
- Python 3.12+
- Flask web UI
- AI Providers: Gemini API, Ollama
- PDF processing
- Docker containerization

## Development Guidelines
- Follow PEP 8, use type hints
- Support multiple AI providers with fallback
- Respect patent claim structure
- Validate all uploads, sanitize inputs
- Mock external APIs in tests

## Pyrolysis Domain Focus
- Thermal decomposition (300-900°C)
- Products: bio-oil, syngas, biochar
- Applications: waste-to-energy, carbon capture
- Reactor types: fixed bed, fluidized bed, rotary kiln
