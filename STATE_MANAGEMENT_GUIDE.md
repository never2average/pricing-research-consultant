# Unified State Management for Orchestrator Agents

This guide explains the unified Pydantic state management system implemented for seamless state tracking across all orchestrator agents.

## Overview

The unified state management system provides:
- **Centralized State**: All agent inputs/outputs in one Pydantic model
- **Step Tracking**: Monitor progress, failures, and completion status
- **Data Validation**: Ensure agents have required inputs before execution
- **Persistence**: Save/load state to/from MongoDB
- **Error Handling**: Track failures and recovery points

## Core Components

### 1. OrchestrationState Model

The main state container that holds all orchestration data:

```python
from datastore.orchestration_state import OrchestrationState, OrchestrationStateManager

# Create new state
state = OrchestrationState(
    invocation_id="unique_id",
    product_id="product_123",
    usage_scope="enterprise",
    customer_segment_id="segment_456"
)
```

### 2. OrchestrationStateManager

Utility class providing helper methods for state management:

```python
# Create initial state
state = OrchestrationStateManager.create_initial_state(
    product_id="product_123",
    usage_scope="enterprise"
)

# Get next executable agents
next_agents = OrchestrationStateManager.get_next_executable_agents(state)

# Validate state for specific agent
is_ready = OrchestrationStateManager.validate_state_for_agent(state, "segmentwise_roi")
```

## Agent Flow and Dependencies

```
1. product_offering (independent)
   ↓
2. segmentwise_roi (needs product_research) + pricing_analysis (independent) [parallel]
   ↓
3. value_capture_analysis (needs segment_research + pricing_research + product_research)
   ↓
4. experimental_pricing_recommendation (needs value_capture_research)
```

## State Structure

### Agent Outputs (Raw Text)
- `product_research`: Output from product_offering_agent
- `segment_research`: Output from segmentwise_roi_agent
- `pricing_research`: Output from pricing_analysis_agent
- `value_capture_research`: Output from value_capture_analysis_agent
- `experimental_pricing_research`: Output from experimental_pricing_recommendation_agent

### Structured Outputs
- `pricing_analysis_structured`: Parsed PricingAnalysisResponse model
- `experimental_pricing_structured`: Parsed RecommendedPricingModelResponse model

### Generated IDs
- `pricing_model_id`: ID of created pricing model
- `customer_segment_ids`: List of created customer segment IDs
- `recommended_pricing_id`: Main recommended pricing ID
- `recommended_pricing_ids`: All recommended pricing IDs

### Step Tracking
- `steps`: Dictionary of StepResult objects for each agent
- `current_step`: Current step number
- `total_steps`: Total number of steps (5)

## Usage Examples

### Basic Orchestration with State

```python
from orchestrator import final_agent

# Run orchestration - returns OrchestrationState object
state = final_agent(
    product_id="product_123",
    usage_scope="enterprise_usage",
    customer_segment_id="segment_456"
)

# Check completion status
if state.is_orchestration_complete():
    print("All agents completed successfully!")
    print(f"Progress: {state.get_progress_percentage():.1f}%")
else:
    failed_steps = state.get_failed_steps()
    if failed_steps:
        print(f"Failed steps: {failed_steps}")
```

### Manual Step Execution

```python
from datastore.orchestration_state import OrchestrationStateManager
from deepresearch.product_offering import agent as product_offering_agent

# Create state
state = OrchestrationStateManager.create_initial_state("product_123")

# Check what can run next
next_agents = OrchestrationStateManager.get_next_executable_agents(state)
print(f"Can execute: {next_agents}")  # ['product_offering']

# Get required inputs for agent
inputs = OrchestrationStateManager.get_agent_inputs(state, "product_offering")

# Start step tracking
state.start_step("product_offering", 1, inputs)

# Execute agent
try:
    result = product_offering_agent(**inputs)
    state.product_research = result
    state.complete_step("product_offering", result)
except Exception as e:
    state.fail_step("product_offering", str(e))
```

### State Persistence

```python
# Save state to MongoDB
state_id = OrchestrationStateManager.save_state_to_mongodb(state)

# Load state from MongoDB
loaded_state = OrchestrationStateManager.load_state_from_mongodb(invocation_id)
if loaded_state:
    print(f"Loaded state with {len(loaded_state.get_completed_steps())} completed steps")
```

### State Monitoring

```python
# Get comprehensive state summary
summary = OrchestrationStateManager.get_state_summary(state)
print(f"Progress: {summary['progress']['percentage']:.1f}%")
print(f"Available data: {summary['data_availability']}")
print(f"Next executable: {summary['next_executable_agents']}")

# Check specific step status
if state.is_step_completed("product_offering"):
    print("Product offering completed")

# Get all completed steps
completed = state.get_completed_steps()
print(f"Completed: {completed}")
```

## Error Handling

The state management system includes comprehensive error handling:

```python
# Check for failed steps
failed_steps = state.get_failed_steps()
if failed_steps:
    for step_name in failed_steps:
        step_result = state.steps[step_name]
        print(f"Step {step_name} failed: {step_result.error_message}")

# Validate before execution
if not OrchestrationStateManager.validate_state_for_agent(state, "value_capture_analysis"):
    print("Cannot run value capture analysis - missing dependencies")
    missing_data = []
    if not state.segment_research:
        missing_data.append("segment_research")
    if not state.pricing_research:
        missing_data.append("pricing_research")
    print(f"Missing: {missing_data}")
```

## Integration with Existing Code

### Updated orchestrator.py

The `final_agent` function now returns an `OrchestrationState` object instead of just an invocation ID:

```python
# Old way
invocation_id = final_agent("product_123")

# New way
state = final_agent("product_123")
invocation_id = state.invocation_id

# Access all data
print(f"Product research: {state.product_research}")
print(f"Pricing recommendations: {state.experimental_pricing_structured}")
```

### Backward Compatibility

The existing `save_orchestration_step` function is still called for MongoDB persistence, ensuring backward compatibility with existing database queries.

## Benefits

1. **Unified Data Model**: All agent data in one place with type safety
2. **Progress Tracking**: Real-time monitoring of orchestration progress
3. **Error Recovery**: Clear visibility into what failed and why
4. **Dependency Management**: Automatic validation of agent prerequisites
5. **Persistence**: Save/restore orchestration state for long-running processes
6. **Debugging**: Rich state information for troubleshooting

## Best Practices

1. **Always check state validity** before executing agents
2. **Use OrchestrationStateManager** helper methods instead of direct state manipulation
3. **Handle exceptions gracefully** and update state accordingly
4. **Save state periodically** for long-running orchestrations
5. **Monitor progress** using built-in progress tracking methods

## Running the Example

To see the state management in action:

```bash
python example_state_usage.py
```

This will demonstrate all key features of the unified state management system.
