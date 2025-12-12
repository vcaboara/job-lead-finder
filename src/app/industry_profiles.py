"""Industry-specific job search profiles.

Defines company lists, search parameters, and preferences for different industries.
Users can select a profile to customize their job search.

TODO: Allow users to create custom profile(s) for industries not listed here.
      Add /api/config/profiles endpoint for CRUD operations on custom profiles.
"""

from typing import Any, Dict, List

INDUSTRY_PROFILES = {
    "tech": {
        "name": "Technology & Software",
        "description": "Software engineering, AI/ML, cloud, cybersecurity, and tech companies",
        "excluded_companies": [
            # Musk companies
            "Tesla",
            "SpaceX",
            "X Corp",
            "Twitter",
            "Neuralink",
            "Boring Company",
            # Zuckerberg companies
            "Meta",
            "Facebook",
            "Instagram",
            "WhatsApp",
        ],
        "target_companies": [
            # Top tier
            "Apple",
            "Microsoft",
            "NVIDIA",
            "Alphabet",
            "Google",
            "Amazon",
            "Broadcom",
            "Oracle",
            "SAP",
            "Salesforce",
            # Cloud/Enterprise
            "ServiceNow",
            "Snowflake",
            "Workday",
            "Adobe",
            "IBM",
            "Cisco",
            "VMware",
            "Red Hat",
            "Dell",
            "HPE",
            "Palo Alto Networks",
            "Fortinet",
            "CrowdStrike",
            "Datadog",
            "MongoDB",
            # Semiconductors
            "Intel",
            "AMD",
            "Qualcomm",
            "Texas Instruments",
            "Micron",
            "NVIDIA",
            # Software
            "Atlassian",
            "Shopify",
            "Stripe",
            "Square",
            "PayPal",
            "Intuit",
            "Autodesk",
            "Splunk",
            "Twilio",
            "Zoom",
            "Slack",
            "Dropbox",
            "Box",
            "GitLab",
            "GitHub",
            # AI/Data
            "Palantir",
            "C3.ai",
            "UiPath",
            "Databricks",
            "Scale AI",
            "OpenAI",
            "Anthropic",
            "Cohere",
        ],
        "search_keywords": ["software engineer", "developer", "AI engineer", "cloud engineer", "DevOps", "SRE"],
        "preferred_locations": ["Remote", "San Francisco", "Seattle", "New York", "Austin"],
    },
    "finance": {
        "name": "Financial Technology & Banking",
        "description": "Fintech, banking, trading, payments, and financial services technology",
        "excluded_companies": [],
        "target_companies": [
            # Traditional Finance
            "JPMorgan Chase",
            "Goldman Sachs",
            "Morgan Stanley",
            "Bank of America",
            "Citigroup",
            "Wells Fargo",
            "Charles Schwab",
            "Fidelity Investments",
            "Capital One",
            "American Express",
            # Fintech
            "Stripe",
            "Square",
            "Block",
            "PayPal",
            "Visa",
            "Mastercard",
            "Coinbase",
            "Robinhood",
            "Plaid",
            "Affirm",
            "SoFi",
            "Chime",
            "Brex",
            "Ramp",
            # Trading/Investment
            "Citadel",
            "Jane Street",
            "Two Sigma",
            "D.E. Shaw",
            "Renaissance Technologies",
            "Bridgewater",
            "BlackRock",
            "Vanguard",
            "State Street",
        ],
        "search_keywords": ["software engineer", "quant", "trading systems", "financial engineer", "backend developer"],
        "preferred_locations": ["New York", "Chicago", "London", "Remote"],
    },
    "healthcare": {
        "name": "Healthcare & Medical Technology",
        "description": "Health tech, medical devices, biotech, pharmaceuticals, and healthcare IT",
        "excluded_companies": [],
        "target_companies": [
            # Health Tech
            "Epic Systems",
            "Cerner",
            "Allscripts",
            "Athenahealth",
            "Veeva Systems",
            # Medical Devices
            "Medtronic",
            "Abbott",
            "Boston Scientific",
            "Stryker",
            "Intuitive Surgical",
            # Pharma/Biotech
            "Pfizer",
            "Moderna",
            "Johnson & Johnson",
            "Roche",
            "Novartis",
            "Merck",
            "Gilead Sciences",
            "Amgen",
            "Biogen",
            "Regeneron",
            # Digital Health
            "Teladoc",
            "Livongo",
            "Oscar Health",
            "Omada Health",
            "Hinge Health",
            # Genomics/AI
            "Illumina",
            "23andMe",
            "Tempus",
            "Recursion Pharmaceuticals",
        ],
        "search_keywords": [
            "software engineer",
            "health tech",
            "medical software",
            "clinical systems",
            "data engineer",
        ],
        "preferred_locations": ["Remote", "Boston", "San Francisco", "Research Triangle Park"],
    },
    "gaming": {
        "name": "Gaming & Interactive Entertainment",
        "description": "Video games, esports, game engines, and interactive media",
        "excluded_companies": [],
        "target_companies": [
            # AAA Studios
            "Epic Games",
            "Valve",
            "Riot Games",
            "Blizzard",
            "Activision",
            "Electronic Arts",
            "Take-Two",
            "Ubisoft",
            "Nintendo",
            "Sony Interactive Entertainment",
            "Microsoft Gaming",
            # Engines/Platforms
            "Unity Technologies",
            "Unreal Engine",
            "Roblox",
            "Steam",
            # Mobile/Casual
            "Supercell",
            "King",
            "Zynga",
            "Rovio",
            "Playrix",
            # Esports/Streaming
            "Twitch",
            "Discord",
            "FaceIt",
        ],
        "search_keywords": [
            "game developer",
            "game engineer",
            "graphics programmer",
            "gameplay engineer",
            "engine developer",
        ],
        "preferred_locations": ["Remote", "Seattle", "Los Angeles", "Austin", "Montreal"],
    },
    "ecommerce": {
        "name": "E-commerce & Retail Technology",
        "description": "Online retail, marketplaces, logistics, and retail tech platforms",
        "excluded_companies": [],
        "target_companies": [
            # Major Platforms
            "Amazon",
            "Shopify",
            "eBay",
            "Etsy",
            "Wayfair",
            "Chewy",
            "Carvana",
            # Fashion/Apparel
            "Stitch Fix",
            "Farfetch",
            "ASOS",
            "Zalando",
            "ThredUp",
            # Grocery/Food
            "Instacart",
            "DoorDash",
            "Uber Eats",
            "Grubhub",
            "HelloFresh",
            "Blue Apron",
            # Traditional Retail Tech
            "Walmart Global Tech",
            "Target",
            "Best Buy",
            "Home Depot",
            "Lowe's",
            # Logistics
            "Flexport",
            "ShipBob",
            "Deliverr",
        ],
        "search_keywords": [
            "software engineer",
            "backend engineer",
            "full stack",
            "platform engineer",
            "data engineer",
        ],
        "preferred_locations": ["Remote", "San Francisco", "Seattle", "New York", "Chicago"],
    },
    "automotive": {
        "name": "Automotive & Autonomous Vehicles",
        "description": "Electric vehicles, autonomous driving, automotive software, and mobility",
        "excluded_companies": [
            "Tesla",  # Musk company
        ],
        "target_companies": [
            # EVs
            "Rivian",
            "Lucid Motors",
            "Canoo",
            "Fisker",
            "Polestar",
            # Traditional OEMs
            "GM Cruise",
            "Ford",
            "BMW",
            "Mercedes-Benz",
            "Toyota",
            "Honda",
            "Volkswagen",
            # Autonomous/AI
            "Waymo",
            "Aurora",
            "Zoox",
            "Argo AI",
            "Motional",
            "Nuro",
            # Suppliers
            "Bosch",
            "Continental",
            "Aptiv",
            "Magna",
            "Denso",
            # Software
            "Woven Planet",
            "Nvidia Automotive",
            "Qualcomm Automotive",
        ],
        "search_keywords": [
            "software engineer",
            "autonomous systems",
            "embedded engineer",
            "robotics",
            "perception engineer",
        ],
        "preferred_locations": ["Remote", "San Francisco", "Pittsburgh", "Detroit", "Austin"],
    },
    "aerospace": {
        "name": "Aerospace & Defense",
        "description": "Aerospace, satellites, defense technology, and space exploration",
        "excluded_companies": [
            "SpaceX",  # Musk company
        ],
        "target_companies": [
            # Space
            "Blue Origin",
            "Rocket Lab",
            "Planet Labs",
            "Spire Global",
            "Relativity Space",
            # Defense/Aerospace
            "Lockheed Martin",
            "Boeing",
            "Northrop Grumman",
            "Raytheon",
            "General Dynamics",
            "L3Harris",
            "BAE Systems",
            "Airbus",
            "Collins Aerospace",
            # Satellites
            "Maxar",
            "Iridium",
            "SES",
            "Intelsat",
        ],
        "search_keywords": [
            "software engineer",
            "aerospace engineer",
            "systems engineer",
            "embedded software",
            "flight software",
        ],
        "preferred_locations": ["Remote", "Los Angeles", "Seattle", "Denver", "Washington DC"],
    },
    "esg": {
        "name": "ESG & Sustainability",
        "description": (
            "Environmental, Social, Governance focused companies, "
            "renewable energy, climate tech, sustainable technology"
        ),
        "excluded_companies": [
            # Fossil fuel companies
            "ExxonMobil",
            "Chevron",
            "BP",
            "Shell",
            "ConocoPhillips",
            # Controversial tech
            "Palantir",  # Defense contracts
            "Meta",  # Privacy concerns
            "Facebook",
        ],
        "target_companies": [
            # Renewable Energy
            "Tesla Energy",
            "Enphase Energy",
            "SunPower",
            "First Solar",
            "Sunrun",
            "Vestas",
            "Orsted",
            "NextEra Energy",
            # Climate Tech
            "Climeworks",
            "Carbon Engineering",
            "LanzaTech",
            "Impossible Foods",
            "Beyond Meat",
            "Apeel Sciences",
            "Indigo Agriculture",
            # Clean Transportation
            "Rivian",
            "Lucid Motors",
            "Proterra",
            "ChargePoint",
            "EVgo",
            # Sustainable Tech
            "Patagonia",
            "Allbirds",
            "ThredUp",
            "The RealReal",
            "Impossible Foods",
            # ESG-Focused Tech
            "Salesforce",  # Strong ESG ratings
            "Microsoft",  # Carbon negative goals
            "Google",  # Renewable energy leader
            "Apple",  # 100% renewable energy
            "SAP",  # Sustainability solutions
            # Environmental Monitoring
            "Planet Labs",
            "Orbital Insight",
            "Descartes Labs",
            # Water Tech
            "Xylem",
            "Evoqua Water",
            "Veolia",
            # Recycling/Circular Economy
            "TerraCycle",
            "Rubicon",
            "AMP Robotics",
            # Green Building
            "Interface",
            "Owens Corning",
            # ESG Software/Analytics
            "Sustainalytics",
            "Arabesque",
            "TruValue Labs",
            "RepRisk",
        ],
        "search_keywords": [
            "sustainability engineer",
            "climate tech",
            "renewable energy",
            "ESG analyst",
            "environmental data",
            "carbon accounting",
            "clean energy",
        ],
        "preferred_locations": ["Remote", "San Francisco", "Boulder", "Portland", "Seattle", "Boston"],
    },
}


def get_profile(industry: str) -> Dict[str, Any]:
    """Get industry profile configuration."""
    return INDUSTRY_PROFILES.get(industry, INDUSTRY_PROFILES["tech"])


def list_profiles() -> List[Dict[str, str]]:
    """List all available industry profiles."""
    return [
        {"key": key, "name": profile["name"], "description": profile["description"]}
        for key, profile in INDUSTRY_PROFILES.items()
    ]


def get_companies_for_profile(industry: str) -> List[str]:
    """Get target companies for an industry profile."""
    profile = get_profile(industry)
    return profile.get("target_companies", [])


def get_excluded_companies(industry: str) -> List[str]:
    """Get excluded companies for an industry profile."""
    profile = get_profile(industry)
    return profile.get("excluded_companies", [])
