"""
Intent Classifier - Hybrid rule-based and LLM classification
Fast pattern matching with LLM fallback for complex cases
"""

import re
import json
import yaml
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
import sys

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from src.models.intent import Intent, IntentType, IntentClassificationResult
from src.llm.client import LLMClient


class IntentClassifier:
    """
    Classifies user intent using hybrid approach:
    1. Fast rule-based pattern matching
    2. LLM fallback for ambiguous cases
    """

    def __init__(self):
        """Initialize intent classifier"""
        self.llm_client = LLMClient()
        self.rules = self._load_rules()
        self.llm_fallback_threshold = 0.7  # Use LLM if confidence below this

    def _load_rules(self) -> Dict[str, Any]:
        """Load intent rules from YAML configuration"""
        config_path = Path(__file__).parent.parent.parent / "config" / "intents.yaml"

        if not config_path.exists():
            print(f"Warning: intents.yaml not found at {config_path}")
            return {}

        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading intents.yaml: {e}")
            return {}

    def classify(
        self, user_input: str, context: Optional[Dict[str, Any]] = None
    ) -> IntentClassificationResult:
        """
        Classify user intent

        Args:
            user_input: User's input text
            context: Optional conversation context

        Returns:
            IntentClassificationResult with intent, confidence, and entities
        """
        # Try rule-based classification first
        rule_result = self._match_rules(user_input)

        if rule_result and rule_result.confidence >= self.llm_fallback_threshold:
            return rule_result

        # Fall back to LLM for complex cases
        print(
            f"Using LLM fallback for intent classification (rule confidence: {rule_result.confidence if rule_result else 0})"
        )
        return self._classify_with_llm(user_input, context or {})

    def _match_rules(self, user_input: str) -> Optional[IntentClassificationResult]:
        """
        Match user input against rule-based patterns

        Args:
            user_input: User input text

        Returns:
            IntentClassificationResult if matched, None otherwise
        """
        if not self.rules or "intents" not in self.rules:
            return None

        user_input_lower = user_input.lower().strip()
        best_match = None
        best_confidence = 0.0

        for intent_config in self.rules.get("intents", []):
            intent_name = intent_config.get("name")
            patterns = intent_config.get("patterns", [])
            base_confidence = intent_config.get("confidence", 0.8)

            # Check patterns
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    if base_confidence > best_confidence:
                        best_confidence = base_confidence
                        entities = self._extract_entities(
                            user_input, intent_config.get("entities", [])
                        )
                        best_match = IntentClassificationResult(
                            intent=Intent(
                                type=IntentType(intent_name.upper()),
                                confidence=base_confidence,
                                entities=entities,
                            ),
                            matched_rules=[pattern],
                            required_llm_fallback=False,
                        )

        # Check for ambiguity indicators
        ambiguity_patterns = self.rules.get("ambiguity_indicators", [])
        for pattern in ambiguity_patterns:
            if re.search(pattern, user_input_lower):
                if best_match:
                    # Lower confidence due to ambiguity
                    best_match.intent.confidence *= 0.7
                    best_match.required_llm_fallback = True
                break

        return best_match

    def _extract_entities(
        self, user_input: str, entity_definitions: List[Dict]
    ) -> Dict[str, str]:
        """
        Extract entities using regex patterns

        Args:
            user_input: User input text
            entity_definitions: Entity definitions from config

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        for entity_def in entity_definitions:
            entity_name = entity_def.get("name")
            pattern = entity_def.get("pattern")

            if not pattern:
                continue

            match = re.search(pattern, user_input, re.IGNORECASE)
            if match:
                if match.groups():
                    entities[entity_name] = match.group(1)
                else:
                    entities[entity_name] = match.group(0)

        return entities

    def _classify_with_llm(
        self, user_input: str, context: Dict[str, Any]
    ) -> IntentClassificationResult:
        """
        Classify intent using LLM

        Args:
            user_input: User input
            context: Conversation context

        Returns:
            IntentClassificationResult from LLM
        """
        try:
            response = self.llm_client.classify_intent(user_input, context)
            result = json.loads(response)

            # Parse LLM response
            intent_type_str = result.get("intent", "UNKNOWN").upper()
            confidence = result.get("confidence", 0.5)
            entities = result.get("entities", {})
            reasoning = result.get("reasoning", "")

            # Validate intent type
            try:
                intent_type = IntentType(intent_type_str)
            except ValueError:
                intent_type = IntentType.UNKNOWN
                confidence = 0.3

            return IntentClassificationResult(
                intent=Intent(
                    type=intent_type,
                    confidence=confidence,
                    entities=entities,
                    reasoning=reasoning,
                ),
                matched_rules=[],
                required_llm_fallback=True,
            )

        except Exception as e:
            print(f"Error in LLM intent classification: {e}")
            # Return unknown intent as fallback
            return IntentClassificationResult(
                intent=Intent(
                    type=IntentType.UNKNOWN,
                    confidence=0.1,
                    entities={},
                    reasoning=f"Classification error: {str(e)}",
                ),
                matched_rules=[],
                required_llm_fallback=True,
            )

    def is_ambiguous(self, result: IntentClassificationResult) -> bool:
        """
        Check if classification result is ambiguous

        Args:
            result: Classification result

        Returns:
            True if ambiguous, False otherwise
        """
        return (
            result.intent.confidence < self.llm_fallback_threshold
            or result.required_llm_fallback
            or result.intent.type == IntentType.CLARIFICATION
        )
