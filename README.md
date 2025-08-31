## Agent Purpose

**Transform AI pricing from guesswork to science with ROI-based optimization.**

For AI companies, traditional pricing models fail to capture your technology's true value. This intelligent agent analyzes your pricing ecosystem to deliver:
- **Segment-specific ROI analysis** for optimal pricing per customer type
- **Dynamic recommendations** based on usage patterns and value capture
- **A/B testing frameworks** for experimental validation
- **Data-driven strategies** that maximize revenue and reduce churn

### Essential Documentation Required

#### 📋 Product Docs
- ICP descriptions with use cases
- Feature catalogs with value propositions
- Customer success stories with ROI metrics

#### 🏗️ Infrastructure Docs
- Usage metrics and cost structures
- Scalability constraints and benchmarks
- Integration requirements

#### 🤖 AI Usage Docs
- Model performance metrics
- Token consumption patterns
- Usage analytics and adoption data

**Ready to optimize your AI pricing?** Follow the setup instructions below.


## Agent Architecture

This diagram illustrates the complete workflow of the AI Pricing Research Consultant, showing how data flows through various specialized agents to deliver comprehensive pricing recommendations.

The architecture follows a modular design with clear separation of concerns:
- Data ingestion and storage layers
- Specialized AI agents for different analysis phases
- Orchestration layer coordinating the workflow
- Multiple AI model integrations for optimal performance

Each agent is designed to handle specific aspects of pricing analysis, from initial product offering assessment to experimental recommendation generation.

```mermaid
---
config:
  theme: mc
  look: classic
  layout: dagre
---
flowchart TD
    A["CLI Entry Point<br>main.py"] --> B{"Command Type"}
    B -- "--create" --> C["Data Creation Flow"]
    B -- "--orchestrator" --> D["Orchestrator Flow"]
    B -- "--delete" --> E["Delete Operations"]
    B -- "--list" --> F["List Operations"]
    C --> C1["JSON/CSV Input"]
    C1 --> C2["connectors.py<br>create_from_json_file<br>create_from_csv_file"]
    C2 --> C3["MongoDB<br>Product, PricingModel,<br>CustomerSegment"]
    D --> D1["orchestrator.py<br>final_agent"]
    D1 --> D2["Product Offering Agent<br>deepresearch/product_offering.py"]
    D2 --> D3["Segmentwise ROI Agent<br>deepresearch/segmentwise_roi.py"] & AI1["OpenAI o3-deep-research<br>with web search, file search,<br>code interpreter"] & DB1[("MongoDB<br>Product Data")]
    D3 --> D4["Pricing Analysis Agent<br>deepresearch/pricing_analysis.py"] & AI2["OpenAI GPT-5<br>with reasoning"] & DB2[("MongoDB<br>CustomerSegment<br>CustomerUsageAnalysis")]
    D4 --> D5["Value Capture Analysis Agent<br>deepresearch/value_capture_analysis.py"] & AI3["OpenAI GPT-5 +<br>LiteLLM Kimi-K2-Instruct<br>for structured parsing"] & DB3[("MongoDB<br>PricingPlanSegmentContribution")]
    D5 --> D6["Experimental Pricing Recommendation Agent<br>deepresearch/experimental_pricing_recommendation.py"] & AI4["OpenAI GPT-5<br>with rabbithole thinking"]
    D6 --> AI5["OpenAI GPT-5 +<br>LiteLLM Kimi-K2-Instruct<br>for structured parsing"] & DB4[("MongoDB<br>RecommendedPricingModel")]
    E --> E1["connectors.py<br>delete_one/delete_many"]
    E1 --> E2[("MongoDB<br>Delete Operations")]
    F --> F1["connectors.py<br>list_one_markdown<br>list_all_markdown"]
    F1 --> F2[("MongoDB<br>Query Operations")]
    G["Data Models<br>datastore/models.py"] --> G1["Product"] & G2["ProductPricingModel"] & G3["CustomerSegment"] & G4["PricingPlanSegmentContribution"] & G5["CustomerUsageAnalysis"] & G6["RecommendedPricingModel"] & G7["TimeseriesData"]
    H["Utils<br>utils/openai_client.py"] --> H1["OpenAI Client"] & H2["LiteLLM Client"]
    I["Prompts<br>deepresearch/prompts.py"] --> I1["System Prompts<br>for each agent"]
    F2 --> n1["Untitled Node"]
    style A fill:#e1f5fe
    style D1 fill:#f3e5f5
    style AI1 fill:#fff3e0
    style DB1 fill:#e8f5e8
    style AI2 fill:#fff3e0
    style DB2 fill:#e8f5e8
    style AI3 fill:#fff3e0
    style DB3 fill:#e8f5e8
    style AI4 fill:#fff3e0
    style AI5 fill:#fff3e0
    style DB4 fill:#e8f5e8
```

### Key Architecture Components

**Data Layer**: MongoDB serves as the central data repository with structured collections for products, customer segments, pricing models, and analysis results.

**AI Integration Layer**: Multiple AI models are strategically used - GPT-5 for complex reasoning, o3-deep-research for comprehensive analysis.

**Agent Orchestration**: The orchestrator coordinates the sequential execution of specialized agents, ensuring data flows correctly between analysis phases.

**CLI Interface**: Simple command-line interface provides easy access to all functionality while maintaining the sophisticated AI processing underneath.

## How to use it?

### Prerequisites

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set API keys
export OPENAI_API_KEY="your-openai-api-key"
export TOGETHER_API_KEY="your-together-ai-api-key"

# Optional: Set MongoDB connection
export MONGODB_URI="mongodb://localhost:27017/pricing-research"  # or your Atlas URI
```

**MongoDB Options:**
- **Local**: Install MongoDB and run `mongod`
- **Cloud**: Use MongoDB Atlas and set `MONGODB_URI`
- **Docker**: `docker run -d -p 27017:27017 mongo:latest`

### Usage

```bash
# Create data from JSON/CSV
python main.py --create path/to/your/data.json

# Run pricing analysis
python main.py --orchestrator product_id

# List data
python main.py --list collection_name

# Delete data
python main.py --delete collection_name document_id
```
