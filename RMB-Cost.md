# RMB Cost

- Generated at: `2026-07-06T13:57:37Z`
- Confidence: `estimate`
- USD/CNY: `7.2`
- Task: GSD Phase 6 ship and v1.0 milestone close
- Codex effective goal meter: `814,681` tokens (0.814681M)
- Session: `/Users/Zhuanz/.codex/sessions/2026/07/06/rollout-2026-07-06T19-21-31-019f3729-7528-75f3-8f1c-af70e4f48792.jsonl`
- Token window events: `2026-07-06T13:10:37.110Z` -> `2026-07-06T13:56:54.490Z`

## Token Usage

| Item | Tokens | M tokens |
|---|---:|---:|
| Input total | 23,962,934 | 23.962934 |
| Cached input | 23,239,168 | 23.239168 |
| Uncached input | 723,766 | 0.723766 |
| Output | 99,332 | 0.099332 |
| Reasoning output, included in output when provider reports it that way | 25,329 | 0.025329 |

## Price Assumptions

| Model | Input USD/M | Cached input USD/M | Output USD/M | Note |
|---|---:|---:|---:|---|
| gpt-5.5 | 5 | 0.5 | 30 | Script default; verify current OpenAI pricing before payable use. |
| deepseek-v4-pro | 0.435 | 0.003625 | 0.87 | Script default; verify current DeepSeek pricing before payable use. |

## Cost Breakdown

| Model | Component | Cache status | Tokens | M tokens | USD/M | USD | RMB |
|---|---|---|---:|---:|---:|---:|---:|
| gpt-5.5 | Input (cache miss) | not cached | 723,766 | 0.723766 | 5 | 3.62 | 26.06 |
| gpt-5.5 | Input (cache hit) | cached | 23,239,168 | 23.239168 | 0.5 | 11.62 | 83.66 |
| gpt-5.5 | Output | not applicable | 99,332 | 0.099332 | 30 | 2.98 | 21.46 |
| deepseek-v4-pro | Input (cache miss) | not cached | 723,766 | 0.723766 | 0.435 | 0.3148 | 2.27 |
| deepseek-v4-pro | Input (cache hit) | cached | 23,239,168 | 23.239168 | 0.003625 | 0.0842 | 0.6065 |
| deepseek-v4-pro | Output | not applicable | 99,332 | 0.099332 | 0.87 | 0.0864 | 0.6222 |

## Cost Summary

| Model | Input cache miss RMB | Input cache hit RMB | Output RMB | Total RMB | Total USD |
|---|---:|---:|---:|---:|---:|
| gpt-5.5 | 26.06 | 83.66 | 21.46 | 131.17 | 18.22 |
| deepseek-v4-pro | 2.27 | 0.6065 | 0.6222 | 3.50 | 0.4855 |

## Formula

`uncached_input = input_total - cached_input`

`uncached_input_cost = uncached_input_M * input_usd_per_M`

`cached_input_cost = cached_input_M * cached_input_usd_per_M`

`output_cost = output_M * output_usd_per_M`

`total_rmb = (uncached_input_cost + cached_input_cost + output_cost) * USD_CNY`

## Notes

- Re-run with current official API prices and FX before using this for reimbursement or budget approval.
- Codex goal `tokensUsed` can differ from raw session input/output because it is an effective meter, while session logs also expose cache hits and repeated context reads.
