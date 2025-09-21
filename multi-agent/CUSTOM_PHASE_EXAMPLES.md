# Custom Phase System Examples

## Overview

Our system now supports **truly custom phases** that users can define without modifying core code. Here are examples showing how to create different phase systems.

## Current System Analysis

### ✅ What Works Now
- **Flexible Phase Provider**: Supports any custom phase registry
- **Phase Registry System**: Users can define their own phases
- **Tool Categorization**: Custom tool mappings per phase
- **Transition Validation**: Custom transition rules
- **Backward Compatibility**: Adapter for existing code

### ❌ What Was Missing (Now Fixed)
- Hard-coded `ExecutionPhase` enum → Now supports custom phase registries
- Hard-coded phase guidance → Now supports custom guidance per phase
- Hard-coded tool mappings → Now supports custom tool categories
- No validation of phase systems → Now validates transitions and setup

## Example 1: Custom Research Workflow

```python
from elements.nodes.common.agent.extensible_phases import PhaseDefinition, PhaseRegistry
from elements.nodes.common.agent.flexible_phase_provider import FlexiblePhaseProviderFactory

# Define custom research phases
def create_research_workflow():
    registry = PhaseRegistry("research")
    
    # Literature Review Phase
    literature = PhaseDefinition(
        name="literature_review",
        description="Review existing research and build knowledge base",
        guidance="PHASE: LITERATURE_REVIEW - Search and analyze existing research. Build comprehensive knowledge base before forming hypotheses.",
        tool_categories={"search", "analysis", "knowledge", "database"},
        keywords={"search", "review", "analyze", "literature"},
        allowed_transitions={"literature_review", "hypothesis_formation"}
    )
    
    # Hypothesis Formation Phase  
    hypothesis = PhaseDefinition(
        name="hypothesis_formation",
        description="Form testable hypotheses based on literature",
        guidance="PHASE: HYPOTHESIS_FORMATION - Create specific, testable hypotheses. Define success criteria and experimental approach.",
        tool_categories={"analysis", "planning", "hypothesis", "design"},
        keywords={"hypothesis", "plan", "criteria", "design"},
        allowed_transitions={"literature_review", "hypothesis_formation", "experimentation"}
    )
    
    # Experimentation Phase
    experiment = PhaseDefinition(
        name="experimentation", 
        description="Conduct experiments to test hypotheses",
        guidance="PHASE: EXPERIMENTATION - Execute planned experiments systematically. Collect data rigorously. Document all procedures.",
        tool_categories={"experiment", "data", "measurement", "lab"},
        keywords={"experiment", "measure", "collect", "execute"},
        allowed_transitions={"experimentation", "analysis"}
    )
    
    # Analysis Phase
    analysis = PhaseDefinition(
        name="analysis",
        description="Analyze experimental results and draw conclusions", 
        guidance="PHASE: ANALYSIS - Analyze collected data statistically. Test hypotheses. Draw evidence-based conclusions.",
        tool_categories={"analysis", "statistics", "visualization", "interpretation"},
        keywords={"analyze", "statistics", "visualize", "interpret"},
        allowed_transitions={"experimentation", "analysis", "publication"}
    )
    
    # Publication Phase (Terminal)
    publication = PhaseDefinition(
        name="publication",
        description="Prepare and publish research findings",
        guidance="PHASE: PUBLICATION - Write research paper. Create publication-quality visualizations. Prepare for peer review.",
        tool_categories={"writing", "visualization", "formatting", "submission"},
        keywords={"write", "format", "publish", "submit"},
        is_terminal=True,
        allowed_transitions={"publication"}
    )
    
    # Register all phases
    for phase in [literature, hypothesis, experiment, analysis, publication]:
        registry.register_phase(phase)
    
    return registry

# Use the custom workflow
research_registry = create_research_workflow()
research_provider = FlexiblePhaseProviderFactory.create_custom_provider(
    tools=my_research_tools,
    phase_registry=research_registry,
    node_uid="research-agent"
)

# Use with strategy
strategy = PlanAndExecuteStrategy(
    llm_chat=llm_chat,
    tools=my_research_tools,
    parser=parser,
    phase_provider=research_provider  # Custom phases!
)
```

## Example 2: Software Development Workflow

```python
def create_software_dev_workflow():
    registry = PhaseRegistry("software_dev")
    
    # Requirements Analysis
    requirements = PhaseDefinition(
        name="requirements_analysis",
        description="Gather and analyze requirements",
        guidance="PHASE: REQUIREMENTS_ANALYSIS - Gather stakeholder requirements. Analyze feasibility. Create user stories.",
        tool_categories={"requirements", "analysis", "stakeholder", "documentation"},
        keywords={"gather", "analyze", "requirements", "stories"},
        allowed_transitions={"requirements_analysis", "design"}
    )
    
    # Design Phase
    design = PhaseDefinition(
        name="design",
        description="Create system and component designs",
        guidance="PHASE: DESIGN - Create system architecture. Design components and interfaces. Plan implementation approach.",
        tool_categories={"design", "architecture", "modeling", "planning"},
        keywords={"design", "architecture", "model", "plan"},
        allowed_transitions={"requirements_analysis", "design", "implementation"}
    )
    
    # Implementation Phase
    implementation = PhaseDefinition(
        name="implementation",
        description="Write and integrate code",
        guidance="PHASE: IMPLEMENTATION - Write code following design. Implement features incrementally. Maintain code quality.",
        tool_categories={"coding", "integration", "version_control", "quality"},
        keywords={"code", "implement", "integrate", "commit"},
        allowed_transitions={"design", "implementation", "testing"}
    )
    
    # Testing Phase
    testing = PhaseDefinition(
        name="testing",
        description="Test functionality and quality",
        guidance="PHASE: TESTING - Execute test plans. Verify functionality. Ensure quality standards are met.",
        tool_categories={"testing", "quality", "automation", "validation"},
        keywords={"test", "verify", "validate", "quality"},
        allowed_transitions={"implementation", "testing", "deployment"}
    )
    
    # Deployment Phase (Terminal)
    deployment = PhaseDefinition(
        name="deployment",
        description="Deploy to production environment",
        guidance="PHASE: DEPLOYMENT - Deploy to production. Monitor system health. Document deployment process.",
        tool_categories={"deployment", "monitoring", "documentation", "operations"},
        keywords={"deploy", "monitor", "document", "release"},
        is_terminal=True,
        allowed_transitions={"deployment"}
    )
    
    # Register phases
    for phase in [requirements, design, implementation, testing, deployment]:
        registry.register_phase(phase)
    
    return registry
```

## Example 3: Data Science Pipeline

```python
def create_data_science_workflow():
    registry = PhaseRegistry("data_science")
    
    # Data Collection
    collection = PhaseDefinition(
        name="data_collection",
        description="Collect and acquire data sources",
        guidance="PHASE: DATA_COLLECTION - Identify and collect relevant data sources. Ensure data quality and completeness.",
        tool_categories={"data_sources", "collection", "apis", "databases"},
        keywords={"collect", "acquire", "source", "extract"},
        allowed_transitions={"data_collection", "data_preparation"}
    )
    
    # Data Preparation
    preparation = PhaseDefinition(
        name="data_preparation", 
        description="Clean and prepare data for analysis",
        guidance="PHASE: DATA_PREPARATION - Clean, transform, and prepare data. Handle missing values and outliers.",
        tool_categories={"cleaning", "transformation", "preprocessing", "validation"},
        keywords={"clean", "transform", "prepare", "preprocess"},
        allowed_transitions={"data_collection", "data_preparation", "exploration"}
    )
    
    # Exploratory Data Analysis
    exploration = PhaseDefinition(
        name="exploration",
        description="Explore and understand the data",
        guidance="PHASE: EXPLORATION - Perform exploratory data analysis. Understand patterns and relationships.",
        tool_categories={"analysis", "visualization", "statistics", "exploration"},
        keywords={"explore", "analyze", "visualize", "understand"},
        allowed_transitions={"data_preparation", "exploration", "modeling"}
    )
    
    # Model Development
    modeling = PhaseDefinition(
        name="modeling",
        description="Develop and train models",
        guidance="PHASE: MODELING - Select algorithms. Train and tune models. Validate performance.",
        tool_categories={"machine_learning", "training", "validation", "tuning"},
        keywords={"model", "train", "validate", "tune"},
        allowed_transitions={"exploration", "modeling", "evaluation"}
    )
    
    # Model Evaluation
    evaluation = PhaseDefinition(
        name="evaluation",
        description="Evaluate model performance and results",
        guidance="PHASE: EVALUATION - Evaluate model performance. Compare alternatives. Prepare for deployment.",
        tool_categories={"evaluation", "metrics", "comparison", "reporting"},
        keywords={"evaluate", "measure", "compare", "report"},
        is_terminal=True,
        allowed_transitions={"modeling", "evaluation"}
    )
    
    # Register phases
    for phase in [collection, preparation, exploration, modeling, evaluation]:
        registry.register_phase(phase)
    
    return registry
```

## Example 4: Using Custom Phases with Strategy

```python
# Create your custom workflow
custom_registry = create_data_science_workflow()

# Create provider with your phases
custom_provider = FlexiblePhaseProviderFactory.create_custom_provider(
    tools=my_data_science_tools,
    phase_registry=custom_registry,
    node_uid="data-scientist-agent"
)

# Use with strategy - no changes needed!
strategy = PlanAndExecuteStrategy(
    llm_chat=llm_chat,
    tools=my_data_science_tools, 
    parser=parser,
    phase_provider=custom_provider  # Your custom phases work seamlessly
)

# The strategy will now use your custom phases:
# 1. data_collection
# 2. data_preparation  
# 3. exploration
# 4. modeling
# 5. evaluation
```

## Example 5: Backward Compatibility

```python
# For existing code that uses ExecutionPhase enum
from elements.nodes.common.agent.flexible_phase_provider import LegacyPhaseAdapter

# Create flexible provider
flexible_provider = FlexiblePhaseProviderFactory.create_standard_provider(tools)

# Wrap with adapter for compatibility
legacy_adapter = LegacyPhaseAdapter(flexible_provider)

# Use with existing strategy code that expects old interface
old_strategy = OldPlanAndExecuteStrategy(
    phase_tool_provider=legacy_adapter,
    phase_context_provider=legacy_adapter,
    phase_transition_policy=legacy_adapter
)
```

## Key Benefits

### ✅ **True Extensibility**
- Define any phases you want
- Custom guidance for each phase
- Custom tool mappings
- Custom transition rules

### ✅ **SOLID Principles**
- **SRP**: Each phase has single responsibility
- **OCP**: Extensible without modifying core code
- **LSP**: All providers are interchangeable
- **ISP**: Clean, focused interfaces
- **DIP**: Depends on abstractions, not concrete implementations

### ✅ **Easy to Use**
```python
# 3 steps to custom phases:
1. Define your phases with PhaseDefinition
2. Register them in a PhaseRegistry  
3. Create provider with FlexiblePhaseProviderFactory

# That's it! No core code changes needed.
```

### ✅ **Validation Built-in**
- Validates phase transitions
- Validates tool categories
- Validates phase definitions
- Clear error messages for issues

### ✅ **Backward Compatible**
- Existing code continues to work
- Gradual migration path
- Legacy adapter available

## Conclusion

The system now supports **truly custom phases** while maintaining:
- Clean OOP design
- SOLID principles  
- Backward compatibility
- Easy extensibility
- Comprehensive validation

Users can define any workflow they want without touching core code!
