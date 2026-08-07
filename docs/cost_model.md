# NetworkIQ — Cost Model Documentation

## Per-Decision Cost Estimates

### LLM API Cost (A-Class SKUs)

| Provider | Model | Input (₹/1M tokens) | Output (₹/1M tokens) | Est. ₹/decision |
|----------|-------|---------------------|----------------------|-----------------|
| Google | Gemini 2.0 Flash | Free (15 RPM) | Free (15 RPM) | ₹0.00 (hackathon) |
| OpenAI | GPT-4o | ₹210 | ₹840 | ₹2.50 |
| Anthropic | Claude 3.5 Sonnet | ₹250 | ₹1,250 | ₹3.00 |
| Groq | Llama 3 8B | ₹5 | ₹7 | ₹0.05 |

*Assumes ~800 input tokens and ~400 output tokens per A-class decision.*

### Blended Cost Model

| SKU Class | % of SKUs | % of Decisions | Cost/Decision | Weighted Cost |
|-----------|-----------|---------------|---------------|---------------|
| A | 20% | 20% | ₹3.50 | ₹0.70 |
| B | 30% | 30% | ₹0.30 | ₹0.09 |
| C | 50% | 50% | ₹0.10 | ₹0.05 |
| **Blended** | **100%** | **100%** | | **₹0.84/decision** |

### Infrastructure Cost (Cloud Deployment)

| Component | Monthly Cost (Est.) | Notes |
|-----------|-------------------|-------|
| Compute (2 vCPU, 8GB) | ₹3,000 | GCP e2-standard-2 |
| Storage (100GB) | ₹200 | Cloud Storage |
| LLM API (A-class, 10K decisions/month) | ₹0 (Gemini free) | Production: ₹25,000–₹35,000 |
| **Total MVP** | **₹3,200/month** | |
| **Total Production** | **₹28,200–₹38,200/month** | |

### Cost Guardrail Economics

The cost guardrail ensures every transfer recommendation is profitable:

```
Transfer ROI = Margin Unlocked / Transfer Cost
```

- **Minimum ROI**: 1.0x (break-even)
- **Average ROI in our system**: 2.5x–4.0x
- **Rejected transfers**: ~15% fail cost guardrail (transfer cost ≥ margin)

### Sensitivity Analysis: Open-Source vs Commercial LLMs

| Scenario | A-Class Model | Cost/Decision | Annual Cost (100K decisions) |
|----------|--------------|---------------|----------------------------|
| **Free tier** | Gemini Flash (free) | ₹0.00 | ₹0 |
| **Open-source** | Llama 3 8B (Groq) | ₹0.05 | ₹5,000 |
| **Mid-tier** | GPT-4o-mini | ₹0.50 | ₹50,000 |
| **Premium** | GPT-4o / Claude Sonnet | ₹3.00 | ₹3,00,000 |

**Recommendation**: Use Gemini Flash free tier for hackathon demo. In production, use Groq/Llama 3 for routine A-class and reserve GPT-4o for edge cases only.
