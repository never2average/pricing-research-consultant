# Pricing Research Consultant - Usage Guide

## Quick Start

### Prerequisites
```bash
# 1. Set up environment variables
export OPENAI_API_KEY="your-openai-api-key"
export MONGODB_URI="mongodb://localhost:27017/pricing_research"  # Optional

# 2. Start MongoDB (choose one option):
# Option A: Local MongoDB
mongod

# Option B: Docker
docker run -d -p 27017:27017 mongo:latest

# Option C: Use MongoDB Atlas (set MONGODB_URI to your Atlas connection string)
```

### One-Command Setup and Run
```bash
# This will populate data and run a complete pricing experiment
python setup_and_run.py
```

## Individual Scripts

### 1. Populate Database
```bash
# Load product data from product_data.json into MongoDB
python populate_data.py
```

### 2. Run Pricing Experiments
```bash
# List available products
python run_experiment.py --list-products

# List existing experiments
python run_experiment.py --list-experiments

# Run a new experiment
python run_experiment.py --product-id <PRODUCT_ID> \
  --objective "Optimize pricing for enterprise customers" \
  --usecase "B2B SaaS pricing strategy"
```

### 3. Web Interface (FastAPI)
```bash
# Start the web server
python main.py

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## Workflow Stages

The pricing research workflow goes through these stages:

1. **segments_loaded** - Load and analyze customer segments
2. **positioning_usage_analysis_done** - Analyze product positioning and usage patterns
3. **roi_gap_analyzer_run** - Identify ROI gaps and opportunities
4. **experimental_plan_generated** - Generate experimental pricing plans
5. **simulations_run** - Run pricing simulations
6. **scenario_builder_completed** - Build different pricing scenarios
7. **cashflow_feasibility_runs_completed** - Analyze cashflow feasibility
8. **completed** - Experiment completed and ready for review

## Data Structure

The `product_data.json` contains:
- **Product info**: Name, description, features, documentation
- **Pricing models**: Different pricing tiers and models
- **Customer segments**: Target customer groups with usage patterns

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check if MongoDB is running
mongod --version

# For Docker:
docker ps | grep mongo

# Test connection
python -c "import mongoengine; mongoengine.connect('mongodb://localhost:27017/test')"
```

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### API Key Issues
```bash
# Verify your OpenAI API key
echo $OPENAI_API_KEY

# Test API access
python -c "from openai import OpenAI; client = OpenAI(); print('API key works!')"
```

## Example Workflow

```bash
# 1. Complete setup and first run
python setup_and_run.py

# 2. Run additional experiments with different parameters
python run_experiment.py --product-id <ID> \
  --objective "Test freemium conversion rates" \
  --usecase "Freemium to paid optimization"

# 3. Start web interface for management
python main.py
```

## Output

Each experiment generates:
- **Positioning analysis** - Market positioning insights
- **Usage patterns** - Customer usage analysis
- **ROI gaps** - Identified revenue opportunities
- **Pricing recommendations** - Experimental pricing strategies
- **Simulation results** - Projected outcomes
- **Cashflow analysis** - Financial feasibility assessment

Results are stored in MongoDB and can be accessed via the web interface or directly through the database.
