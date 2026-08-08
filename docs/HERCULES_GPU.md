# Hercules GPU

## Detect order

1. `HERCULES_GPU_BACKEND` env override
2. PyTorch CUDA
3. PyTorch MPS (Apple Metal)
4. Darwin → `metal_soft`
5. Else `fallback_cpu`

## Pool

- Slots (default 2)
- Reserve / release by lease id
- VRAM soft estimate (no nvidia-smi required)
- Temperature field reserved for future probes

## Policy

If GPU reservation fails → execute on CPU path (never hard-fail the job for missing GPU in sandbox).
