# Multi-Step Reasoning in Merlin

This document explains how Merlin's multi-step reasoning system works and how to use it effectively.

## Overview

The multi-step reasoning system allows Merlin to break down complex tasks into smaller, sequential steps. This is particularly useful for tasks that involve:

1. Finding and analyzing files
2. Making decisions based on file contents
3. Executing multiple related commands
4. Synthesizing information from multiple sources

## How It Works

The system uses a chain-of-thought approach with the following components:

1. **ReasoningStep**: Represents a single step in the reasoning process
2. **ReasoningChain**: Manages a sequence of steps for a specific task
3. **ReasoningEngine**: Controls the execution of reasoning chains

When you ask Merlin to perform a complex task, it:

1. Analyzes the request to determine if it requires multiple steps
2. Creates a plan with specific steps to accomplish the task
3. Executes each step in sequence
4. Uses the results of previous steps to inform subsequent steps
5. Synthesizes a final response that addresses your original request

## Available Tools

The reasoning system can use the following tools:

- **execute_commands**: Run terminal commands
- **search_files**: Search for files in indexed directories
- **synthesize**: Analyze results and generate insights

## Example Usage

Here's how you might use multi-step reasoning with Merlin:

```
You: Find all PDF files about finance and move them to a folder called Finance

Merlin: I'll help you with your request: 'Find all PDF files about finance and move them to a folder called Finance'

I've broken this down into 4 steps. Working on step 1: Search for PDF files related to finance...

[Merlin executes the steps in sequence and provides updates]

I've completed your request. I found 3 PDF files related to finance and moved them to a new folder called 'Finance'.

Files moved:
- finance_report_2023.pdf
- finance_report_2024.pdf
- tax_info_2023.pdf

The folder is located at /home/user/Finance
```

## Enabling Multi-Step Reasoning

To enable multi-step reasoning, use the `--multi-step` flag when starting Merlin:

```bash
python main.py --multi-step
```

## Customizing the Reasoning Process

You can customize the reasoning process by modifying the following files:

- `src/core/reasoning.py`: Core reasoning system implementation
- `src/nlp/openai_response.py`: Integration with OpenAI's API
- `src/core/response_processor.py`: Processing of responses

## Limitations

The multi-step reasoning system has the following limitations:

1. It may take longer to process complex requests
2. It requires more API calls to OpenAI
3. Very complex tasks with many interdependencies might not be handled optimally

## Extending the System

To extend the system with new tools:

1. Add the tool definition in `openai_response.py`
2. Implement the tool execution in `execute_reasoning_step()` function
3. Update the system prompt to describe the new tool

## Debug and Troubleshooting

To see the detailed reasoning steps, you can examine the active reasoning chains:

```python
from src.core.reasoning import reasoning_engine

# Get all active reasoning chains
chains = reasoning_engine.active_chains

# Print details of the first chain
first_chain = list(chains.values())[0]
print(f"Query: {first_chain.query}")
print(f"Steps: {len(first_chain.steps)}")

# Print each step
for i, step in enumerate(first_chain.steps):
    print(f"Step {i+1}: {step.description}")
    print(f"Result: {step.result}")
```