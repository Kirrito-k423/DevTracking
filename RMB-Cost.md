# RMB Cost

- Generated at: `2026-07-06T13:58:56Z`
- Confidence: `estimate`
- USD/CNY: `7.2`
- Task: GSD Phase 6 ship and v1.0 milestone close
- Codex effective goal meter: `849,793` tokens (0.849793M)
- Session: `/Users/Zhuanz/.codex/sessions/2026/07/06/rollout-2026-07-06T19-21-31-019f3729-7528-75f3-8f1c-af70e4f48792.jsonl`
- Token window events: `2026-07-06T13:10:37.110Z` -> `2026-07-06T13:58:38.389Z`

## Token Usage

| Item | Tokens | M tokens |
|---|---:|---:|
| Input total | 25,369,729 | 25.369729 |
| Cached input | 24,621,312 | 24.621312 |
| Uncached input | 748,417 | 0.748417 |
| Output | 102,621 | 0.102621 |
| Reasoning output, included in output when provider reports it that way | 26,125 | 0.026125 |

## Price Assumptions

| Model | Input USD/M | Cached input USD/M | Output USD/M | Note |
|---|---:|---:|---:|---|
| gpt-5.5 | 5 | 0.5 | 30 | Script default; verify current OpenAI pricing before payable use. |
| deepseek-v4-pro | 0.435 | 0.003625 | 0.87 | Script default; verify current DeepSeek pricing before payable use. |

## Cost Breakdown

| Model | Component | Cache status | Tokens | M tokens | USD/M | USD | RMB |
|---|---|---|---:|---:|---:|---:|---:|
| gpt-5.5 | Input (cache miss) | not cached | 748,417 | 0.748417 | 5 | 3.74 | 26.94 |
| gpt-5.5 | Input (cache hit) | cached | 24,621,312 | 24.621312 | 0.5 | 12.31 | 88.64 |
| gpt-5.5 | Output | not applicable | 102,621 | 0.102621 | 30 | 3.08 | 22.17 |
| deepseek-v4-pro | Input (cache miss) | not cached | 748,417 | 0.748417 | 0.435 | 0.3256 | 2.34 |
| deepseek-v4-pro | Input (cache hit) | cached | 24,621,312 | 24.621312 | 0.003625 | 0.0893 | 0.6426 |
| deepseek-v4-pro | Output | not applicable | 102,621 | 0.102621 | 0.87 | 0.0893 | 0.6428 |

## Cost Summary

| Model | Input cache miss RMB | Input cache hit RMB | Output RMB | Total RMB | Total USD |
|---|---:|---:|---:|---:|---:|
| gpt-5.5 | 26.94 | 88.64 | 22.17 | 137.75 | 19.13 |
| deepseek-v4-pro | 2.34 | 0.6426 | 0.6428 | 3.63 | 0.5041 |

## Formula

`uncached_input = input_total - cached_input`

`uncached_input_cost = uncached_input_M * input_usd_per_M`

`cached_input_cost = cached_input_M * cached_input_usd_per_M`

`output_cost = output_M * output_usd_per_M`

`total_rmb = (uncached_input_cost + cached_input_cost + output_cost) * USD_CNY`

## Notes

- Re-run with current official API prices and FX before using this for reimbursement or budget approval.
- Codex goal `tokensUsed` can differ from raw session input/output because it is an effective meter, while session logs also expose cache hits and repeated context reads.
