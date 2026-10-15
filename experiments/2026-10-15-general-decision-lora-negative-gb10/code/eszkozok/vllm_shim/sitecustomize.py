"""vLLM v0.30.0 + transformers 5.17 csomagolási eltérés (2026-10-04, Mistral Small 4 boot).

A vllm/model_executor/models/pixtral.py még a régi transformers-neveket importálja
(`PixtralRotaryEmbedding`, `position_ids_in_meshgrid`); a 5.17-ben az első átnevezve
(`PixtralVisionRotaryEmbedding`), a második megszűnt → a `PixtralForConditionalGeneration`
architektúra-vizsgálata ImportErrorral bukik. A Mistral-formátumú (params.json) Mistral Small 4 a
natív vision-utat használja, ezek csak az import miatt kellenek. A HF-formátumú Pixtral-út
(PixtralHFVisionModel) helyességét ez a shim NEM garantálja. Csak a ldh-mistral konténerbe kerül
(PYTHONPATH), a többi futtatásba nem.
"""

try:
    import torch
    import transformers.models.pixtral.modeling_pixtral as _mp

    if not hasattr(_mp, "PixtralRotaryEmbedding"):
        _mp.PixtralRotaryEmbedding = _mp.PixtralVisionRotaryEmbedding
    if not hasattr(_mp, "position_ids_in_meshgrid"):
        def position_ids_in_meshgrid(patch_embeds_list, max_width):  # a transformers < 5.17 implementációja
            positions = []
            for patch in patch_embeds_list:
                height, width = patch.shape[-2:]
                mesh = torch.meshgrid(torch.arange(height), torch.arange(width), indexing="ij")
                h_grid, v_grid = torch.stack(mesh, dim=-1).reshape(-1, 2).chunk(2, -1)
                positions.append((h_grid * max_width + v_grid)[:, 0])
            return torch.cat(positions)

        _mp.position_ids_in_meshgrid = position_ids_in_meshgrid
except Exception:  # a shim sosem állíthatja meg az interpretert
    pass
