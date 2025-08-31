## Agent Purpose


## Agent Architecture

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

## How to use it?

### Prerequisites

Before running this pricing research consultant, you'll need to set up the following:

#### 1. OpenAI Credentials
Set your OpenAI API key as an environment variable:
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

This is required for the main GPT-5 model used throughout the research pipeline.

#### 2. LiteLLM Client for Together AI
The system uses LiteLLM with Together AI for structured parsing. You'll need to configure the Together AI API:

**Option A: Environment Variables**
```bash
export TOGETHER_API_KEY="your-together-ai-api-key-here"
```

**Option B: LiteLLM Configuration**
Create a `.env` file or set the following environment variables:
```bash
export LITELLM_API_KEY="your-together-ai-api-key-here"
export LITELLM_MODEL="together_ai/moonshotai/Kimi-K2-Instruct"
```

The system uses the `together_ai/moonshotai/Kimi-K2-Instruct` model for structured data parsing and validation.

#### 3. MongoDB Setup
The system requires MongoDB for data persistence. You have several options:

**Option A: Local MongoDB**
1. Install MongoDB locally
2. Start MongoDB service:
```bash
# On macOS with Homebrew
brew services start mongodb/brew/mongodb-community

# On Ubuntu/Debian
sudo systemctl start mongod
```

**Option B: MongoDB Atlas (Cloud)**
1. Create a MongoDB Atlas account at https://cloud.mongodb.com
2. Create a cluster and get your connection string
3. Set the connection string as an environment variable:
```bash
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/pricing-research?retryWrites=true&w=majority"
```

**Option C: Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Default Configuration:**
If no `MONGODB_URI` is set, the system defaults to:
```
mongodb://localhost:27017/pricing-research
```

#### 4. Python Dependencies
Install the required packages:
```bash
pip install -r requirements.txt
```

### Running the Application

Once all prerequisites are configured, you can run the pricing research consultant:

```bash
# Create data from JSON/CSV
python main.py --create path/to/your/data.json

# Run the full orchestrator pipeline
python main.py --orchestrator product_id

# List existing data
python main.py --list collection_name

# Delete data
python main.py --delete collection_name document_id
```

### Environment Variables Summary
```bash
# Required
export OPENAI_API_KEY="your-key"
export TOGETHER_API_KEY="your-key"  # or LITELLM_API_KEY

# Optional
export MONGODB_URI="your-mongodb-connection-string"
```
