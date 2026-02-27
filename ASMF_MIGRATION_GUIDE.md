# ASMF Migration Guide

This guide explains the refactoring of job-lead-finder to use the AI Search Match Framework (ASMF).

## What Changed

### 1. New ASMF Package (`src/smf/`)

Created a reusable framework with:
- **Providers** - AI provider abstraction with automatic fallback
- **Parsers** - Document parsing (PDF, DOCX, TXT)
- **Analyzers** - Base pattern for domain-specific analysis
- **Utils** - Configuration and logging utilities

### 2. Updated Components

**Before:**
```python
# Direct provider instantiation
from app.gemini_provider import GeminiProvider
from app.ollama_provider import OllamaProvider

provider = OllamaProvider()
if not provider.is_available():
    provider = GeminiProvider()
```

**After:**
```python
# Use factory with automatic fallback
from smf.providers import get_factory

factory = get_factory()
provider = factory.create_with_fallback()  # Ollama -> Gemini
```

**Before:**
```python
# Custom PDF parsing
from pypdf import PdfReader
pdf = PdfReader(BytesIO(content))
text = extract_text_with_cleanup(pdf)
```

**After:**
```python
# Use ASMF parser
from smf.parsers import PDFParser
parser = PDFParser()
text = parser.parse(content)  # Includes cleanup
```

### 3. New Domain-Specific Analyzer

Created `JobLeadAnalyzer` extending ASMF's `BaseAnalyzer`:

```python
from smf.analyzers import BaseAnalyzer

class JobLeadAnalyzer(BaseAnalyzer):
    def analyze_single(self, job, resume):
        return self.provider.evaluate(job, resume)
    
    def get_required_fields(self):
        return ['title', 'company']
```

## Files Modified

1. **src/smf/** (NEW) - ASMF framework package
2. **src/app/gemini_provider.py** - Extends `smf.providers.BaseAIProvider`
3. **src/app/ollama_provider.py** - Extends `smf.providers.BaseAIProvider`
4. **src/app/job_lead_analyzer.py** (NEW) - Extends `smf.analyzers.BaseAnalyzer`
5. **src/app/job_finder.py** - Uses `AIProviderFactory`
6. **src/app/ui_server.py** - Uses ASMF parsers
7. **tests/test_job_finder.py** - Updated to test ASMF integration
8. **pyproject.toml** - Updated to include smf package

## Benefits

### For job-lead-finder
- Cleaner provider management with automatic fallback
- Standardized document parsing with security checks
- Better testability through clear interfaces

### For the Ecosystem
- **Consistency**: Same patterns in all projects (patent-eval, grant-finder, etc.)
- **Maintainability**: Bug fixes in ASMF benefit all projects
- **Reusability**: Easy to add new providers, parsers, analyzers

## Usage Examples

### Using AIProviderFactory

```python
from smf.providers import get_factory

# Get factory instance
factory = get_factory()

# Auto-select best provider
provider = factory.create_with_fallback()

# Or create specific provider
ollama = factory.create_provider('ollama')
gemini = factory.create_provider('gemini')

# Use provider
result = provider.evaluate(job, resume)
print(f"Score: {result['score']}")
```

### Using Document Parsers

```python
from smf.parsers import PDFParser, DOCXParser, TXTParser

# Parse PDF
pdf_parser = PDFParser()
if pdf_parser._available:  # Check if pypdf is installed
    text = pdf_parser.parse(pdf_bytes)
    metadata = pdf_parser.get_metadata(pdf_bytes)

# Parse DOCX (with macro check)
docx_parser = DOCXParser()
text = docx_parser.parse(docx_bytes)  # Raises if macros detected

# Parse text
txt_parser = TXTParser()
text = txt_parser.parse(txt_bytes)
```

### Using JobLeadAnalyzer

```python
from app.job_lead_analyzer import JobLeadAnalyzer
from smf.providers import get_factory

# Create analyzer
provider = get_factory().create_with_fallback()
analyzer = JobLeadAnalyzer(provider)

# Analyze single job
job = {'title': 'Python Dev', 'company': 'Tech Co'}
resume = 'Python expert...'
result = analyzer.analyze_single(job, resume)

# Batch analysis
results = analyzer.analyze_batch(jobs, resume, top_n=10)

# Validation
is_valid = analyzer.validate_item(job)
```

## Migration Checklist

If you have code using the old patterns:

- [ ] Replace direct provider instantiation with `AIProviderFactory`
- [ ] Replace custom PDF/DOCX parsing with ASMF parsers
- [ ] Consider extending `BaseAnalyzer` for domain logic
- [ ] Update tests to mock the factory instead of providers
- [ ] Update imports from `app.framework` to `smf`

## Testing

All existing tests pass with ASMF:
- Provider inheritance verified
- Factory registration confirmed
- Parsers functional
- Integration tests passing

Run tests:
```bash
pytest tests/test_job_finder.py -v
```

## Future Enhancements

ASMF can be extended with:
- Additional providers (OpenAI, Anthropic, Claude)
- Streaming support for long analyses
- Caching layer for provider responses
- Rate limiting and quota management
- Extract to separate PyPI package

## Questions?

See `src/smf/README.md` for comprehensive ASMF documentation.
