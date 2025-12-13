# TODO: Patent Analysis Framework - Core Implementation

**Priority**: P0 (Critical - New Project Kickoff)
**Project**: ai-patent-eval
**Complexity**: High
**Estimated Time**: 3-4 hours
**Auto-PR**: true
**Auto-Commit**: true
**Execution Mode**: Fully autonomous (no approval required)

## Objective

Build core patent analysis framework for pyrolysis technologies. User needs to analyze their patent attorney's draft, verify claims aren't bogus, search for prior art, and eventually draft new claims for other technical briefs.

## Context

- **Project Path**: `C:\Users\vcabo\job-lead-finder\ai-patent-eval`
- **User Goal**: Review patent draft, find first licensee for pyrolysis innovations, accelerate waste-to-energy deployment
- **Domain**: Pyrolysis systems (thermal decomposition 300-900°C, produces bio-oil/syngas/biochar)
- **User is NOT**: Patent expert or pyrolysis engineer - needs AI validation
- **Framework**: Can eventually share ai-search-match-framework from job-lead-finder

## Implementation Tasks

### 1. AI Provider Foundation (src/providers/)

**File**: `src/providers/base_provider.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAIProvider(ABC):
    """Base class for AI providers (Gemini, Ollama)."""
    
    @abstractmethod
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        pass
    
    @abstractmethod
    def analyze_text(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Analyze text with AI model."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass
```

**File**: `src/providers/gemini_provider.py`
- Implement GeminiProvider using google-generativeai
- Default model: gemini-1.5-pro
- Handle API errors gracefully
- Support streaming responses

**File**: `src/providers/ollama_provider.py`
- Implement OllamaProvider
- Default base_url: http://localhost:11434
- Support qwen2.5-coder:32b model
- Fallback chain: Gemini -> Ollama

### 2. Patent PDF Parser (src/parsers/)

**File**: `src/parsers/pdf_parser.py`
```python
from typing import List, Dict
import pypdf
import pdfplumber

class PatentClaim:
    """Represents a single patent claim."""
    def __init__(self, number: int, text: str, claim_type: str, depends_on: List[int] = None):
        self.number = number
        self.text = text
        self.claim_type = claim_type  # "independent" or "dependent"
        self.depends_on = depends_on or []

class PatentDocument:
    """Parsed patent document with claims."""
    def __init__(self, title: str, abstract: str, claims: List[PatentClaim]):
        self.title = title
        self.abstract = abstract
        self.claims = claims

class PDFPatentParser:
    """Extract patent claims from PDF documents."""
    
    def parse(self, pdf_path: str) -> PatentDocument:
        """Extract title, abstract, and claims from patent PDF."""
        # Use pypdf for basic extraction
        # Use pdfplumber for better table/structure handling
        # Identify "Claims" section
        # Parse claim numbers (1., 2., etc.)
        # Detect independent vs dependent claims
        # Detect claim dependencies ("The system of claim 1, wherein...")
        pass
    
    def extract_claims_section(self, text: str) -> str:
        """Find and extract the claims section."""
        # Look for "Claims", "What is claimed", "We claim"
        pass
    
    def parse_claim_dependencies(self, claim_text: str) -> List[int]:
        """Extract which claims this claim depends on."""
        # Regex for "claim 1", "claims 1-3", "any of claims 1, 2, or 3"
        pass
```

### 3. Prior Art Search (src/search/)

**File**: `src/search/google_patents.py`
```python
import httpx
from typing import List, Dict

class GooglePatentsSearch:
    """Search Google Patents for prior art."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://patents.google.com"
    
    def search(self, query: str, max_results: int = 50) -> List[Dict]:
        """Search for patents matching query."""
        # Use Google Patents public search
        # Extract patent numbers, titles, abstracts
        # Return structured results
        pass
    
    def search_by_keywords(self, keywords: List[str], domain: str = "pyrolysis") -> List[Dict]:
        """Search using extracted keywords from claims."""
        pass
    
    def get_patent_details(self, patent_number: str) -> Dict:
        """Fetch full patent details."""
        pass
```

**File**: `src/search/prior_art_analyzer.py`
```python
from typing import List, Dict
from ..providers.base_provider import BaseAIProvider

class PriorArtAnalyzer:
    """Analyze prior art for conflicts with claims."""
    
    def __init__(self, ai_provider: BaseAIProvider, search_engine: GooglePatentsSearch):
        self.ai_provider = ai_provider
        self.search = search_engine
    
    def find_conflicts(self, claim: PatentClaim) -> List[Dict]:
        """Find prior art that conflicts with claim."""
        # Extract key concepts from claim using AI
        # Search Google Patents
        # Use AI to assess similarity/conflict
        # Return ranked list of conflicts
        pass
    
    def assess_novelty(self, claim: PatentClaim, prior_art: List[Dict]) -> Dict:
        """AI assessment of claim novelty given prior art."""
        pass
```

### 4. Pyrolysis Knowledge Base (src/knowledge/)

**File**: `src/knowledge/pyrolysis_expert.py`
```python
class PyrolysisKnowledge:
    """Domain expertise for pyrolysis systems."""
    
    TEMPERATURE_RANGES = {
        "slow_pyrolysis": (300, 500),
        "fast_pyrolysis": (450, 650),
        "flash_pyrolysis": (800, 1000),
    }
    
    REACTOR_TYPES = [
        "fixed_bed",
        "fluidized_bed", 
        "rotary_kiln",
        "ablative",
        "microwave",
        "vacuum"
    ]
    
    FEEDSTOCKS = [
        "biomass",
        "plastics",
        "tires",
        "agricultural_waste",
        "municipal_solid_waste"
    ]
    
    PRODUCTS = {
        "bio_oil": "liquid fuel, chemical feedstock",
        "syngas": "H2, CO, CH4 for power generation",
        "biochar": "carbon sequestration, soil amendment"
    }
    
    @staticmethod
    def validate_temperature_claim(claim_text: str) -> Dict:
        """Check if temperature claims are technically feasible."""
        pass
    
    @staticmethod
    def validate_reactor_design(claim_text: str) -> Dict:
        """Assess reactor design claims for engineering validity."""
        pass
    
    @staticmethod
    def identify_pyrolysis_type(claim_text: str) -> str:
        """Classify pyrolysis process from claim description."""
        pass
```

### 5. Patent Claim Analyzer (src/analyzers/)

**File**: `src/analyzers/claim_analyzer.py`
```python
from typing import List, Dict
from ..parsers.pdf_parser import PatentClaim
from ..providers.base_provider import BaseAIProvider
from ..knowledge.pyrolysis_expert import PyrolysisKnowledge

class ClaimAnalysisResult:
    """Results of claim analysis."""
    def __init__(self):
        self.technical_issues: List[Dict] = []
        self.prior_art_conflicts: List[Dict] = []
        self.clarity_issues: List[Dict] = []
        self.scope_assessment: Dict = {}
        self.patentability_score: float = 0.0
        self.recommendations: List[str] = []

class ClaimAnalyzer:
    """Analyze patent claims for validity and quality."""
    
    def __init__(self, ai_provider: BaseAIProvider):
        self.ai = ai_provider
        self.pyrolysis_expert = PyrolysisKnowledge()
    
    def analyze(self, claims: List[PatentClaim], domain: str = "pyrolysis") -> ClaimAnalysisResult:
        """Comprehensive claim analysis."""
        result = ClaimAnalysisResult()
        
        for claim in claims:
            # Technical feasibility check
            tech_issues = self._check_technical_feasibility(claim)
            result.technical_issues.extend(tech_issues)
            
            # Clarity and enablement check
            clarity = self._check_claim_clarity(claim)
            result.clarity_issues.extend(clarity)
            
            # Scope assessment
            scope = self._assess_claim_scope(claim)
            result.scope_assessment[claim.number] = scope
        
        # Overall patentability score
        result.patentability_score = self._calculate_score(result)
        result.recommendations = self._generate_recommendations(result)
        
        return result
    
    def _check_technical_feasibility(self, claim: PatentClaim) -> List[Dict]:
        """Validate claim against pyrolysis engineering principles."""
        issues = []
        
        # Temperature validation
        temp_check = self.pyrolysis_expert.validate_temperature_claim(claim.text)
        if not temp_check["valid"]:
            issues.append({
                "claim": claim.number,
                "type": "temperature_infeasible",
                "detail": temp_check["reason"]
            })
        
        # Reactor design validation
        reactor_check = self.pyrolysis_expert.validate_reactor_design(claim.text)
        if not reactor_check["valid"]:
            issues.append({
                "claim": claim.number,
                "type": "reactor_design_issue",
                "detail": reactor_check["reason"]
            })
        
        # Use AI for complex feasibility questions
        ai_prompt = f"""
        Analyze this pyrolysis patent claim for technical feasibility:
        
        Claim {claim.number}: {claim.text}
        
        Consider:
        - Material and energy balance
        - Thermodynamic constraints
        - Safety and containment
        - Scalability
        
        Identify any technical impossibilities or implausibilities.
        """
        
        ai_response = self.ai.analyze_text(ai_prompt)
        # Parse AI response for issues
        
        return issues
    
    def _check_claim_clarity(self, claim: PatentClaim) -> List[Dict]:
        """Check for claim clarity and definiteness issues."""
        # Use AI to assess:
        # - Vague terminology ("substantially", "approximately" without context)
        # - Unclear antecedents
        # - Missing structural details
        # - Enablement concerns
        pass
    
    def _assess_claim_scope(self, claim: PatentClaim) -> Dict:
        """Assess if claim scope is appropriate."""
        # Too broad: covers prior art
        # Too narrow: easy to design around
        # Use AI to evaluate
        pass
    
    def _calculate_score(self, result: ClaimAnalysisResult) -> float:
        """Calculate overall patentability score 0-1."""
        pass
    
    def _generate_recommendations(self, result: ClaimAnalysisResult) -> List[str]:
        """Generate actionable recommendations for attorney."""
        pass
```

### 6. Flask Web UI (src/ui/)

**File**: `src/ui/server.py`
```python
from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
import os
from pathlib import Path

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.config['UPLOAD_FOLDER'] = Path(__file__).parent.parent.parent / 'data' / 'uploads'

@app.route('/')
def index():
    """Main upload and analysis page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_patent():
    """Upload patent PDF for analysis."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Only PDF files allowed'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    # Trigger analysis
    from ..parsers.pdf_parser import PDFPatentParser
    from ..analyzers.claim_analyzer import ClaimAnalyzer
    from ..providers.gemini_provider import GeminiProvider
    
    parser = PDFPatentParser()
    patent = parser.parse(filepath)
    
    ai_provider = GeminiProvider()
    analyzer = ClaimAnalyzer(ai_provider)
    result = analyzer.analyze(patent.claims)
    
    return jsonify({
        'filename': filename,
        'claims_found': len(patent.claims),
        'technical_issues': len(result.technical_issues),
        'clarity_issues': len(result.clarity_issues),
        'patentability_score': result.patentability_score,
        'recommendations': result.recommendations
    })

@app.route('/analyze/<filename>')
def get_analysis(filename):
    """Get full analysis results for uploaded patent."""
    # Return detailed analysis from saved results
    pass

@app.route('/search-prior-art', methods=['POST'])
def search_prior_art():
    """Search for prior art for specific claims."""
    data = request.json
    claims = data.get('claims', [])
    
    from ..search.google_patents import GooglePatentsSearch
    from ..search.prior_art_analyzer import PriorArtAnalyzer
    
    # Perform search and return results
    pass

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
```

**File**: `src/ui/templates/index.html`
```html
<!DOCTYPE html>
<html>
<head>
    <title>Patent Analysis Framework</title>
    <style>
        body { font-family: Arial; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; }
        .results { margin-top: 20px; }
        .issue { padding: 10px; margin: 10px 0; border-left: 3px solid #f00; background: #fee; }
        .recommendation { padding: 10px; margin: 10px 0; border-left: 3px solid #0a0; background: #efe; }
    </style>
</head>
<body>
    <h1>Patent Analysis Framework - Pyrolysis Systems</h1>
    
    <div class="upload-area">
        <h2>Upload Patent Draft (PDF)</h2>
        <input type="file" id="fileInput" accept=".pdf">
        <button onclick="uploadFile()">Analyze Patent</button>
    </div>
    
    <div id="results" class="results" style="display:none;">
        <h2>Analysis Results</h2>
        <div id="summary"></div>
        <h3>Technical Issues</h3>
        <div id="technical-issues"></div>
        <h3>Clarity Issues</h3>
        <div id="clarity-issues"></div>
        <h3>Recommendations</h3>
        <div id="recommendations"></div>
    </div>
    
    <script>
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            if (!file) {
                alert('Please select a PDF file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                displayResults(result);
            } catch (error) {
                alert('Error analyzing patent: ' + error);
            }
        }
        
        function displayResults(data) {
            document.getElementById('results').style.display = 'block';
            document.getElementById('summary').innerHTML = `
                <p><strong>File:</strong> ${data.filename}</p>
                <p><strong>Claims Found:</strong> ${data.claims_found}</p>
                <p><strong>Patentability Score:</strong> ${(data.patentability_score * 100).toFixed(0)}%</p>
            `;
            
            // Display issues and recommendations
            // ... populate divs with data
        }
    </script>
</body>
</html>
```

### 7. Testing (tests/)

**File**: `tests/test_pdf_parser.py`
- Test parsing sample patent PDFs
- Test claim extraction
- Test dependency detection

**File**: `tests/test_claim_analyzer.py`
- Test technical feasibility checks
- Test pyrolysis-specific validation
- Mock AI provider responses

**File**: `tests/test_prior_art_search.py`
- Mock Google Patents API
- Test search result parsing
- Test conflict detection

## Implementation Guidelines

1. **Start with parsers**: PDF extraction is foundational
2. **Use existing patterns**: Copy AI provider structure from job-lead-finder if helpful
3. **Mock external APIs**: Don't make real Google Patents calls in tests
4. **Validate inputs**: All PDF uploads, all user inputs
5. **Log everything**: Patent analysis needs audit trail
6. **Error handling**: Graceful failures, helpful error messages

## Testing Strategy

```bash
# Create test fixtures
mkdir tests/fixtures
# Add sample pyrolysis patent PDFs (public domain)

# Run tests
pytest tests/ -v

# Test web UI manually
python -m src.ui.server
# Upload test patent PDF
# Verify analysis runs
# Check recommendations make sense
```

## Expected Outcome

- ✅ User can upload their attorney's patent draft PDF
- ✅ System extracts and parses all claims
- ✅ Technical feasibility validated against pyrolysis principles
- ✅ Prior art search identifies potential conflicts
- ✅ Clear report with patentability score and recommendations
- ✅ User can review report and give attorney feedback
- ✅ All tests passing
- ✅ Code follows Python best practices (black, isort, flake8, mypy)

## Success Criteria

User returns from picking up son, runs:
```bash
cd C:\Users\vcabo\job-lead-finder\ai-patent-eval
.\.venv\Scripts\Activate.ps1
python -m src.ui.server
```

Opens browser to http://localhost:8000, uploads patent PDF, sees comprehensive analysis report with:
- All claims extracted and numbered
- Technical issues flagged (if any)
- Prior art search results
- Patentability score
- Actionable recommendations for attorney

## Notes

- This is the user's path to getting pollution-reducing innovations to market
- Quality matters more than speed - validate thoroughly
- When in doubt about pyrolysis, ask AI provider for technical validation
- Patent law is complex - flag anything uncertain for attorney review
- The goal: User can confidently say "yes, proceed" or "no, fix these issues" to their attorney
