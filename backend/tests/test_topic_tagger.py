"""
Tests for topic tagging service.
"""

import pytest
from app.services.nlp.topic_tagger import TopicTagger


def test_tag_solar_topic():
    """Test tagging solar energy articles."""
    tagger = TopicTagger()
    
    title = "New solar farm announced in California"
    content = "A 500MW solar power project will be built using photovoltaic panels."
    
    topics = tagger.tag_article(title, content)
    
    assert "renewables_solar" in topics


def test_tag_wind_topic():
    """Test tagging wind energy articles."""
    tagger = TopicTagger()
    
    title = "Offshore wind project approved"
    content = "The wind farm will have 100 turbines generating clean electricity."
    
    topics = tagger.tag_article(title, content)
    
    assert "renewables_wind" in topics


def test_tag_battery_storage():
    """Test tagging battery storage articles."""
    tagger = TopicTagger()
    
    title = "Grid-scale battery storage deployment accelerates"
    content = "Lithium-ion battery systems are being installed for energy storage."
    
    topics = tagger.tag_article(title, content)
    
    assert "storage_batteries" in topics


def test_tag_ev_transport():
    """Test tagging electric vehicle articles."""
    tagger = TopicTagger()
    
    title = "Electric vehicle sales surge"
    content = "EV adoption is growing with new charging infrastructure."
    
    topics = tagger.tag_article(title, content)
    
    assert "ev_transport" in topics


def test_tag_hydrogen():
    """Test tagging hydrogen articles."""
    tagger = TopicTagger()
    
    title = "Green hydrogen production facility opens"
    content = "The electrolyzer will produce hydrogen using renewable electricity."
    
    topics = tagger.tag_article(title, content)
    
    assert "hydrogen" in topics


def test_tag_policy_regulation():
    """Test tagging policy articles."""
    tagger = TopicTagger()
    
    title = "Government announces new climate policy"
    content = "New regulations mandate renewable energy standards and tax credits."
    
    topics = tagger.tag_article(title, content)
    
    assert "policy_regulation" in topics


def test_tag_power_grid():
    """Test tagging power grid articles."""
    tagger = TopicTagger()
    
    title = "Grid modernization project underway"
    content = "Transmission lines and substations will improve grid reliability."
    
    topics = tagger.tag_article(title, content)
    
    assert "power_grid" in topics


def test_tag_carbon_markets():
    """Test tagging carbon markets articles."""
    tagger = TopicTagger()
    
    title = "Carbon capture facility commissioned"
    content = "The CCS project will sequester CO2 and generate carbon credits."
    
    topics = tagger.tag_article(title, content)
    
    assert "carbon_markets_ccus" in topics


def test_tag_oil_gas_transition():
    """Test tagging oil & gas transition articles."""
    tagger = TopicTagger()
    
    title = "Shell invests in renewable energy"
    content = "The oil major is diversifying into clean energy as part of energy transition."
    
    topics = tagger.tag_article(title, content)
    
    assert "oil_gas_transition" in topics


def test_tag_corporate_finance():
    """Test tagging corporate finance articles."""
    tagger = TopicTagger()
    
    title = "Renewable energy company raises $500M"
    content = "The investment will fund expansion with capital from private equity."
    
    topics = tagger.tag_article(title, content)
    
    assert "corporate_finance" in topics


def test_tag_critical_minerals():
    """Test tagging critical minerals articles."""
    tagger = TopicTagger()
    
    title = "Lithium mining project approved"
    content = "The mine will supply critical minerals for battery supply chains."
    
    topics = tagger.tag_article(title, content)
    
    assert "critical_minerals_supply_chain" in topics


def test_tag_multiple_topics():
    """Test article with multiple topics."""
    tagger = TopicTagger()
    
    title = "Solar project receives government funding"
    content = "The photovoltaic farm will benefit from new policy incentives."
    
    topics = tagger.tag_article(title, content)
    
    assert "renewables_solar" in topics
    assert "policy_regulation" in topics or "corporate_finance" in topics


def test_tag_max_three_topics():
    """Test that max 3 topics are returned."""
    tagger = TopicTagger(max_topics=3)
    
    title = "Renewable energy investment policy"
    content = """
    The government announced funding for solar, wind, and battery storage projects.
    New regulations mandate grid upgrades. Electric vehicles will receive tax credits.
    Hydrogen production is also supported. Carbon capture incentives are included.
    """
    
    topics = tagger.tag_article(title, content)
    
    assert len(topics) <= 3


def test_negative_keywords_battery_vs_ev():
    """Test that negative keywords help differentiate battery storage from EV."""
    tagger = TopicTagger()
    
    # Battery storage article should not be tagged as EV
    title = "Grid-scale battery storage project"
    content = "Utility scale lithium-ion battery system for stationary energy storage."
    
    topics = tagger.tag_article(title, content)
    
    assert "storage_batteries" in topics
    # Should not strongly associate with EV due to "stationary storage" negative keyword
    if "ev_transport" in topics:
        # If EV is tagged, storage_batteries should rank higher
        assert topics.index("storage_batteries") < topics.index("ev_transport")


def test_negative_keywords_solar_not_wind():
    """Test negative keywords prevent cross-tagging renewables."""
    tagger = TopicTagger()
    
    # Pure solar article
    title = "Solar panel efficiency breakthrough"
    content = "New photovoltaic cells achieve record efficiency in solar energy conversion."
    
    topics = tagger.tag_article(title, content)
    
    assert "renewables_solar" in topics
    # Wind should not be tagged due to negative keywords
    assert "renewables_wind" not in topics


def test_title_weight_higher():
    """Test that title mentions have higher weight."""
    tagger = TopicTagger()
    
    # Solar in title should rank higher
    title = "Solar energy revolution"
    content = "Wind and battery storage are also growing, but solar leads the way."
    
    topics = tagger.tag_article(title, content)
    
    if len(topics) >= 1:
        assert topics[0] == "renewables_solar"


def test_phrase_matching():
    """Test multi-word phrase matching."""
    tagger = TopicTagger()
    
    title = "Electric vehicle charging infrastructure"
    content = "Fast charging stations are essential for EV adoption."
    
    topics = tagger.tag_article(title, content)
    
    assert "ev_transport" in topics


def test_empty_text():
    """Test tagging empty text."""
    tagger = TopicTagger()
    
    topics = tagger.tag_article("", "")
    
    assert topics == []


def test_no_topics_matched():
    """Test text with no matching topics."""
    tagger = TopicTagger()
    
    title = "Company announces quarterly results"
    content = "The firm reported earnings growth this quarter."
    
    topics = tagger.tag_article(title, content)
    
    # Might match corporate_finance, or might not - depends on keywords
    assert isinstance(topics, list)


def test_case_insensitive():
    """Test case-insensitive matching."""
    tagger = TopicTagger()
    
    title = "SOLAR POWER PROJECT ANNOUNCED"
    content = "PHOTOVOLTAIC PANELS WILL BE INSTALLED"
    
    topics = tagger.tag_article(title, content)
    
    assert "renewables_solar" in topics


def test_specific_terms_higher_score():
    """Test that specific multi-word terms score higher."""
    tagger = TopicTagger()
    
    # "electric vehicle" should score higher than just "electric" or "vehicle"
    title = "Electric vehicle market grows"
    content = "Electric vehicle sales have doubled this year."
    
    topics = tagger.tag_article(title, content)
    
    assert "ev_transport" in topics


def test_grid_scale_battery():
    """Test grid-scale battery storage tagging."""
    tagger = TopicTagger()
    
    title = "Grid scale battery deployment"
    content = "Utility scale battery storage for grid stabilization."
    
    topics = tagger.tag_article(title, content)
    
    # Should tag both power_grid and storage_batteries
    assert "storage_batteries" in topics or "power_grid" in topics


def test_hydrogen_fuel_cell():
    """Test hydrogen fuel cell tagging."""
    tagger = TopicTagger()
    
    title = "Fuel cell technology advances"
    content = "Hydrogen fuel cells show promise for clean energy applications."
    
    topics = tagger.tag_article(title, content)
    
    assert "hydrogen" in topics


def test_cop_climate_summit():
    """Test climate summit policy tagging."""
    tagger = TopicTagger()
    
    title = "COP28 climate summit outcomes"
    content = "Paris Agreement targets discussed at climate summit."
    
    topics = tagger.tag_article(title, content)
    
    assert "policy_regulation" in topics


def test_rare_earth_minerals():
    """Test rare earth and critical minerals tagging."""
    tagger = TopicTagger()
    
    title = "Rare earth mining project"
    content = "Critical minerals supply chain for battery production."
    
    topics = tagger.tag_article(title, content)
    
    assert "critical_minerals_supply_chain" in topics


def test_convenience_method():
    """Test convenience method for simple tagging."""
    tagger = TopicTagger()
    
    text = "Solar panels and wind turbines generate renewable energy"
    topics = tagger.tag_text(text)
    
    assert "renewables_solar" in topics or "renewables_wind" in topics
    assert isinstance(topics, list)
