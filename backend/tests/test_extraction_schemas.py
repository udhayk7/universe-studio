from app.schemas.extraction import UniverseExtraction


def test_universe_extraction_schema_normalizes_relationship_type() -> None:
    extraction = UniverseExtraction.model_validate(
        {
            "universe": {
                "title": "Memory City",
                "premise": "Memories are traded as currency.",
                "genre": "Science fiction",
                "tone": "Cinematic mystery",
                "world_rules": ["A spent memory cannot be recalled without a receipt."],
            },
            "characters": [
                {
                    "name": "Mira Vale",
                    "description": "A broker who audits stolen memories.",
                    "personality": ["precise"],
                    "goals": ["recover her childhood"],
                    "fears": ["forgetting her sister"],
                    "current_status": "active",
                }
            ],
            "locations": [
                {
                    "name": "The Mnemonic Exchange",
                    "description": "The city's central memory market.",
                    "type": "market",
                }
            ],
            "objects": [
                {
                    "name": "Glass Ledger",
                    "description": "A portable archive of unpaid memories.",
                    "importance": "high",
                }
            ],
            "events": [
                {
                    "title": "The First Audit",
                    "summary": "Mira discovers counterfeit memory coins.",
                    "participants": ["Mira Vale"],
                    "location": "The Mnemonic Exchange",
                    "importance": 8,
                }
            ],
            "relationships": [
                {
                    "source_character": "Mira Vale",
                    "target_character": "Mira Vale",
                    "type": "knows deeply",
                    "strength": 25,
                }
            ],
        }
    )

    assert extraction.relationships[0].type == "KNOWS_DEEPLY"
