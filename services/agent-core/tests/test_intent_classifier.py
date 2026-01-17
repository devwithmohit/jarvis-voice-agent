"""
Unit tests for Intent Classifier
Tests rule-based and LLM classification
"""

import pytest
from src.pipeline.intent_classifier import IntentClassifier
from src.models.intent import IntentType


class TestIntentClassifier:
    """Test suite for IntentClassifier"""

    @pytest.fixture
    def classifier(self):
        """Create intent classifier instance"""
        return IntentClassifier()

    def test_search_intent_classification(self, classifier):
        """Test classification of search intents"""
        # Test various search patterns
        test_cases = [
            "search for Python tutorials",
            "find information about AI",
            "what is machine learning",
            "google the weather forecast",
        ]

        for user_input in test_cases:
            result = classifier.classify(user_input)
            assert result.intent.type == IntentType.SEARCH
            assert result.intent.confidence > 0.7

    def test_browse_intent_classification(self, classifier):
        """Test classification of browse intents"""
        test_cases = [
            "open https://example.com",
            "navigate to google.com",
            "go to youtube and play some music",
        ]

        for user_input in test_cases:
            result = classifier.classify(user_input)
            assert result.intent.type == IntentType.BROWSE
            assert result.intent.confidence > 0.7

    def test_remember_intent_classification(self, classifier):
        """Test classification of remember intents"""
        test_cases = [
            "remember that I like coffee",
            "save this note for later",
            "store my favorite color is blue",
        ]

        for user_input in test_cases:
            result = classifier.classify(user_input)
            assert result.intent.type == IntentType.REMEMBER
            assert result.intent.confidence > 0.7

    def test_execute_intent_classification(self, classifier):
        """Test classification of execute intents"""
        test_cases = [
            "create a new file called test.txt",
            "run the build script",
            "make a backup of my documents",
        ]

        for user_input in test_cases:
            result = classifier.classify(user_input)
            assert result.intent.type == IntentType.EXECUTE
            assert result.intent.confidence > 0.7

    def test_conversation_intent_classification(self, classifier):
        """Test classification of conversation intents"""
        test_cases = [
            "hello",
            "hi there",
            "thank you",
            "thanks for your help",
            "goodbye",
        ]

        for user_input in test_cases:
            result = classifier.classify(user_input)
            assert result.intent.type == IntentType.CONVERSATION
            assert result.intent.confidence > 0.8

    def test_clarification_intent_classification(self, classifier):
        """Test classification of clarification intents"""
        test_cases = [
            "what do you mean?",
            "can you clarify that?",
            "which one should I choose?",
        ]

        for user_input in test_cases:
            result = classifier.classify(user_input)
            assert result.intent.type == IntentType.CLARIFICATION
            assert result.intent.confidence > 0.7

    def test_ambiguous_input_triggers_llm(self, classifier):
        """Test that ambiguous input triggers LLM fallback"""
        # Very ambiguous input
        result = classifier.classify("it")

        # Should have lower confidence or require LLM fallback
        assert result.intent.confidence < 0.7 or result.required_llm_fallback

    def test_entity_extraction(self, classifier):
        """Test entity extraction from patterns"""
        result = classifier.classify("search for Python tutorials")

        # Check that entities are extracted (if configured in intents.yaml)
        assert isinstance(result.intent.entities, dict)

    def test_context_consideration(self, classifier):
        """Test that context is considered in classification"""
        context = {
            "conversation_summary": "User was asking about programming",
            "current_task": "learning Python",
        }

        result = classifier.classify("show me more", context=context)

        # Should classify successfully with context
        assert result.intent.type != IntentType.UNKNOWN

    def test_rule_based_fast_path(self, classifier):
        """Test that rule-based classification is used for clear intents"""
        result = classifier.classify("search for Python")

        # Should use rule-based classification (matched_rules present)
        assert len(result.matched_rules) > 0
        assert not result.required_llm_fallback

    def test_is_ambiguous_method(self, classifier):
        """Test ambiguity detection"""
        # Clear intent
        clear_result = classifier.classify("search for Python")
        assert not classifier.is_ambiguous(clear_result)

        # Ambiguous intent (very short input)
        ambiguous_result = classifier.classify("do it")
        # May be ambiguous depending on confidence
        if ambiguous_result.intent.confidence < 0.7:
            assert classifier.is_ambiguous(ambiguous_result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
