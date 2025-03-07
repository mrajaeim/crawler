import pytest
from modules.utils.increamental_id_generator import IncrementalIdGenerator


@pytest.fixture
def generator():
    """Fixture to create a new UniqueIDGenerator instance before each test"""
    return IncrementalIdGenerator()


def test_increment_existing(generator):
    """Test that the same input gets incremented correctly"""
    assert generator.get_id("apple") == 1
    assert generator.get_id("apple") == 2
    assert generator.get_id("apple") == 3


def test_new_unique_inputs(generator):
    """Test that new unique inputs start from 1"""
    assert generator.get_id("banana") == 1
    assert generator.get_id("cherry") == 1
    assert generator.get_id("date") == 1


def test_last_10_keys_in_memory(generator):
    """Test that after 10 unique inputs"""
    unique_inputs = ["apple", "banana", "cherry", "date", "elderberry", "fig", "grape", "honeydew", "kiwi", "lemon"]
    for item in unique_inputs:
        assert generator.get_id(item) == 1 # Fill up the first 10 unique inputs

    assert generator.get_id("apple") == 2
    assert generator.get_id("mongo") == 1 # Add new key
    assert generator.get_id("apple") == 1
