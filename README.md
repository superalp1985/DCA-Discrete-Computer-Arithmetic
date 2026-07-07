# DCA Inference Engine

**DCA Inference Engine** is a C++17 research inference engine for testing
**Discrete Computer Arithmetic (DCA)** on quantized language models.

The short version: this project tries to make transformer inference look less
like "a pile of floats" and more like an auditable finite computation. Tokens,
weights, activations, recurrent state, KV state, samplers and chat history are
represented as explicit integers or fixed-point values.

The current target is a Qwen3.5/Qwen3-Next style GGUF model. The engine can
load GGUF metadata and tensors, tokenize with a Qwen-style byte-level BPE path,
generate real tokens through a 24-layer integer/fixed-point path, stream output,
and run multi-turn chat with reusable session state.

## Relationship To DCA

This repository is the inference-engine companion to
[DCA: Discrete Computer Arithmetic](https://github.com/superalp1985/DCA-Discrete-Computer-Arithmetic).

The DCA repository is the broader finite-computation-oriented draft: it keeps
the definitions, scope, mathematical notes, proof sketches and references
around arithmetic, algebra, discrete analysis, formal verification, quantized
AI computation and related finite structures.

This repository is narrower and more practical:

- it treats the DCA draft as the arithmetic and engineering contract;
- it implements one concrete LLM inference path under that contract;
- it turns DCA ideas into inspectable code, tests, tensor layouts, tokenizers
  and session-state behavior;
- it provides a place to compare CPU reference kernels with future accelerator
  kernels.

So the relationship is:

```text
DCA-Discrete-Computer-Arithmetic
  -> concepts, definitions, boundaries, references

DCA-Inference-Engine
  -> executable transformer inference experiment under those boundaries
```

The goal here is not to claim a new universal AI runtime. More modestly: this
is a working laboratory for first testing whether the DCA route can run through
end to end. CPU optimization has started; hardware backends are deliberately
left for the next stage.

## Why This Exists

Modern LLM inference is usually optimized around floating-point kernels. That
is fast, but it can make exact behavior harder to inspect: rounding, overflow,
quantization, sampling and cache state often live in several different mental
models.

DCA takes the opposite angle:

- every value has a finite representation,
- every rounding or saturation rule is explicit,
- model state can be inspected as integer arrays,
- tests can run without private model files,
- deterministic replay and session-cache comparison are first-class checks.

This is still a research prototype. It is not trying to beat llama.cpp today.
It is trying to be a clean, hackable place to explore integer-first LLM
inference.

## Main Selling Points

- **Integer/fixed-point inference path**: Q8.8 activations, Q16 weights and
  nonlinear maps, integer RoPE, finite-table softmax and bounded integer
  sampling.
- **Real token generation**: the default path runs embedding, 24 decoder
  layers, output norm, tied output-head scan and integer argmax/sampling.
- **Reusable chat state**: `--chat` keeps token history, recurrent state and
  K/V state across turns instead of replaying the whole conversation.
- **Streaming output**: `--stream` emits token pieces as they are selected.
- **Tokenizer discipline**: GGUF vocabulary, token types, ranked BPE merges,
  special tokens and Qwen3.5 pre-tokenization are tested explicitly.
- **Distributable CI**: tests create a synthetic GGUF fixture at runtime, so a
  fresh clone can run `ctest` without a private model file.
- **Hardware-friendly direction, not yet a backend**: the arithmetic contract
  is shaped so later accelerator kernels can be compared against the CPU
  reference. No Ascend/CANN or other NPU backend is implemented yet.

## Current Status

Working today:

- Windows/MSVC CMake build and GitHub Actions CI.
- GGUF v3 header, metadata, tensor-info and aligned tensor-data reading.
- Tensor loading for F32, F16, I8, Q4_K, Q5_K, Q6_K and Q8_0 paths.
- Direct Q4_K/Q5_K/Q6_K dot products with int8 activations and Q16
  accumulators.
- Integer RMSNorm, finite lookup-table sigmoid/exp/softplus/SiLU, integer RoPE
  and finite softmax.
- DCA layered generation, integer Top-K/Top-P/temperature sampling, streaming
  and multi-turn chat.
- First CPU/memory-residency step: optional `--resident-weights` preloads GGUF
  tensors, and dense F32/F16/I8 weights cache their Q16 conversion after first
  use.
- Second CPU/memory step: projections that share the same Q8.8 input now reuse
  one int8 activation packing, and `--profile` reports per-operator and
  per-layer CPU timing counters.
- Optional `--threads` row-parallel K-quant projections and greedy output-head
  argmax avoid materializing full-vocabulary logits when exact greedy decoding
  is selected.
- Default CPU decode now uses reported hardware concurrency (`--threads 0`)
  and a `128` row split threshold; this is faster on the current i7-14650HX
  smoke machine than the earlier conservative single-thread default.
- Optional AVX2 integer kernels accelerate Q4_K/Q5_K/Q6_K block dots when the
  CPU supports AVX2; scalar DCA kernels remain the fallback.
- FFN gate/up projections are fused into one row-parallel dispatch when both
  consume the same packed activation.
- Linear-attention `qkv/gate/beta/alpha` K-quant projections can be grouped
  into one row-parallel dispatch while preserving each projection's row-local
  dot order.
- Packed activations cache 32-value and 16-value finite sums so AVX2 K-quant
  kernels do not recompute the same activation sums for every output row.
- Linear-attention recurrent heads run in parallel across disjoint head-state
  slices, and full-attention scoring reuses scaled Q16 query values with
  cache-local value accumulation.
- Bounded sampled decoding (`temperature > 0` with finite `top_k`) streams the
  exact output-head Top-K candidates without retaining a full-vocabulary logit
  vector.
- One-shot generation skips evaluating the final selected token when no next
  token or persistent session state will consume it.
- RoPE sin/cos tables are cached per position in Q16, expanding the DCA lookup
  path where it removes repeated integer CORDIC work.
- Exact zero-block skipping avoids K-quant block dots when a packed activation
  block is all zero, and all-zero packed activations return exact zero
  projections without scanning weight rows.
- Per-run layer weight handles are cached before the token loop, reducing CPU
  map/string overhead while leaving tensor bytes and arithmetic unchanged.
- `--profile` provides trace counters and a deterministic trace hash, so
  normal runs remain traceable without re-auditing every arithmetic operation.
- Optional target-model validation for the local Qwen GGUF layout.

Honest limits:

- The engine is still a correctness-first prototype, not a production-speed
  runtime.
- Code-level performance optimization currently covers memory residency,
  Q16 conversion caching, shared activation packing, profiling, optional
  row-parallel K-quant projection, reusable projection worker pools, exact
  AVX2 K-quant block-dot kernels, activation-sum reuse, fused/grouped
  projections, immediate row rescale, tuned default threading, threaded
  linear-attention heads, output-head greedy/Top-K shortcuts, RoPE table
  caching, final-token decode-boundary trimming and exact zero-skip paths.
  Deeper cache blocking and backend dispatch are not implemented yet.
- Semantic QA still fails on the local target model; see
  [docs/semantic_qa_2026-07-07.md](docs/semantic_qa_2026-07-07.md). The engine
  is faster and DCA-clean, but model-quality parity is not solved yet.
- Hardware optimization has not started; Ascend/CANN and other accelerator
  notes are roadmap material, not current functionality.
- The main tested platform is Windows with MSVC.
- Model quality is experimental while tokenizer and layer math continue to be
  compared against external references.
- Full target-model tests require you to provide a compatible GGUF model file.

## Quick Start

### 1. Install Tools

On Windows:

- Visual Studio 2022 Build Tools
- CMake 3.15 or newer
- Ninja, or the Visual Studio CMake generator

### 2. Build

From a Visual Studio developer shell:

```powershell
cd E:\DCA\dca_transformer
cmake -S . -B build_codex -G Ninja -DCMAKE_BUILD_TYPE=Release -DCA_BUILD_TESTS=ON -DDCA_ENABLE_AVX2=ON
cmake --build build_codex --config Release
```

`DCA_ENABLE_AVX2` builds optional x86/x64 integer SIMD kernels. Runtime CPU
detection keeps the scalar path available when AVX2 is not present.

### 3. Run Tests

```powershell
ctest --test-dir build_codex --output-on-failure
```

Expected public test result:

```text
100% tests passed, 0 tests failed out of 2
```

The e2e test creates a tiny GGUF file automatically and validates parser,
tokenizer, tensor loading, DCA arithmetic, streaming and session reuse.

## Running A Model

Set a local GGUF model path:

```powershell
$env:DCA_TEST_MODEL = 'E:\DCA\qwen3.5-2b-q4km\Qwen3.5-2B-Q4_K_M.gguf'
.\build_codex\dca_test_e2e.exe
```

Single prompt:

```powershell
.\build_codex\dca_transformer.exe `
  --model 'E:\DCA\qwen3.5-2b-q4km\Qwen3.5-2B-Q4_K_M.gguf' `
  --prompt 'DCA' `
  --max-tokens 2 `
  --echo `
  --verbose
```

Streaming:

```powershell
.\build_codex\dca_transformer.exe --model '<model.gguf>' --prompt 'DCA' --max-tokens 8 --stream
```

Memory-resident weight preload:

```powershell
.\build_codex\dca_transformer.exe --model '<model.gguf>' --prompt 'DCA' --max-tokens 8 --resident-weights --verbose
```

CPU operator profile:

```powershell
.\build_codex\dca_transformer.exe --model '<model.gguf>' --prompt 'DCA' --max-tokens 1 --resident-weights --profile
```

Threaded K-quant projection smoke:

```powershell
.\build_codex\dca_transformer.exe --model '<model.gguf>' --prompt 'DCA' --max-tokens 1 --resident-weights --threads 8 --profile
```

Multi-turn chat with reusable state:

```powershell
.\build_codex\dca_transformer.exe `
  --model '<model.gguf>' `
  --chat `
  --max-tokens 64 `
  --system 'You are concise.'
```

Scripted chat and cold-replay comparison:

```powershell
.\build_codex\dca_transformer.exe `
  --model '<model.gguf>' `
  --chat-script '.\chat_turns.txt' `
  --max-tokens 16 `
  --compare-session
```

Example comparison from a local target model:

```text
turn 1: reused prefix tokens 0,  reuse time 25.0864s, cold replay 23.7718s, output match yes
turn 2: reused prefix tokens 16, reuse time 20.2476s, cold replay 48.9397s, output match yes
```

## CLI Cheatsheet

```text
--model PATH              GGUF model path
--prompt TEXT             Single prompt
--prompt-file PATH        Read prompt from UTF-8 file
--stdin                   Read prompt from stdin
--max-tokens N            Maximum generated tokens
--temperature F           Q16 temperature; 0 means greedy
--top-k N                 Integer Top-K; 1 means greedy
--top-p F                 Q16 nucleus threshold
--seed N                  Integer sampler seed
--threads N               Projection worker threads; 0 uses CPU concurrency
--projection-min-rows-per-thread N
                           Minimum output rows assigned to each worker
--stream                  Stream token pieces
--resident-weights        Load all GGUF tensors into memory at startup
--profile                 Print DCA CPU operator timing counters
--chat                    Interactive chat REPL
--chat-script PATH        One user turn per UTF-8 line
--compare-session         Compare session reuse with cold replay
--head-only               Diagnostic embedding/norm/output-head path
--deterministic-smoke     Deterministic test generator
```

## DCA Arithmetic Contract

The inference path is intentionally explicit:

- machine words are finite words, not mathematical integers;
- K-quant binary16 scales are converted to Q16 before inference arithmetic;
- activations are Q8.8 between current sublayers;
- projection paths use int8 activations with recorded right shifts;
- nonlinear maps are finite Q16 lookup tables with integer interpolation;
- Q16 multiply-shift operations use saturating helpers;
- sampling uses Q16 controls, finite integer candidate arrays and a `uint64_t`
  xorshift RNG;
- chat sessions keep token ids, Q8.8 hidden state, Q16 recurrent state, Q16 K/V
  state and explicit position counters.

Details live in [docs/dca_arithmetic_contract.md](docs/dca_arithmetic_contract.md).

## Future Accelerator Direction

DCA is not tied to one hardware vendor. The interesting part is the shape of
the computation: explicit integer/fixed-point tensors, bounded lookup tables,
finite state and deterministic kernels.

This section is a roadmap, not a claim of current acceleration. Today the
engine is a CPU reference implementation used to test whether the DCA
inference path can run correctly.

That shape is especially relevant to China-made accelerator stacks such as
Huawei Ascend:

- Ascend/CANN exposes custom operator development through Ascend C and a
  hardware model built around AI Core style vector/matrix execution.
- DCA kernels are already decomposed into small finite operators such as
  integer matvec, RMSNorm, lookup-table nonlinearities, finite softmax and
  stateful KV/recurrent updates.
- The current scalar kernels can be used as a reference implementation before
  writing Ascend C kernels.
- Q8.8/Q16-style contracts make quantization, rounding and saturation choices
  visible at the operator boundary, which is useful when porting to NPU
  toolchains.

Near-term accelerator work should target:

1. First keep expanding CPU reference tests and output comparison fixtures.
2. Then port Q4_K/Q5_K/Q6_K packed-weight matvec kernels.
3. Then port Q8.8 -> int8 activation packing.
4. Then port integer RMSNorm, residual saturation and finite softmax.
5. Finally move session-reuse decode kernels toward accelerator execution.

See [docs/accelerator_roadmap.md](docs/accelerator_roadmap.md).

## Repository Map

```text
src/
  dca_core/          finite words and arithmetic helpers
  dca_tensor/        integer tensor kernels
  gguf_reader/       GGUF parser, K-quant loading and projection helpers
  tokenizer/         Qwen byte-level BPE tokenizer
  transformer/       DCA norm, softmax, layer helpers and KV state
  model/             Qwen3.5-style inference and session API
docs/                design notes, arithmetic contract and test reports
tools/               helper scripts such as tokenizer golden export
tests/data/          checked-in small test corpora
```

## Documentation

- [Documentation index](docs/index.md)
- [Relationship to DCA](docs/dca_relationship.md)
- [DCA arithmetic contract](docs/dca_arithmetic_contract.md)
- [Session reuse chat](docs/session_reuse_chat.md)
- [Tokenizer parity harness](docs/tokenizer_parity.md)
- [CI synthetic GGUF fixture](docs/ci_synthetic_fixture.md)
- [Target tensor layout validation](docs/tensor_layout_validation.md)
- [Accelerator roadmap](docs/accelerator_roadmap.md)

## Contributing

Contributions are welcome, especially around:

- tokenizer parity,
- GGUF model coverage,
- integer kernel correctness,
- CPU reference fixtures for future Ascend/CANN or other NPU backend
  experiments,
- documentation and reproducible tests.

Please read [CONTRIBUTING.md](CONTRIBUTING.md). Keep the DCA contract visible:
new inference code should state its finite representation, rounding and
overflow behavior.

## License

Apache License 2.0. See [LICENSE](LICENSE).

Copyright 2026 Wang Bingqin.
