# drama3-h3-talking: text → Drama 3 voice → MiniMax H3 talking video (ComfyUI)

An open ComfyUI workflow. Text plus a reference voice plus a face image go into **Fish Audio Drama 3**, which makes expressive speech. That speech then drives **MiniMax H3 Ref2VA**, which makes a lip-synced talking video.

**▶ Watch/listen in your browser: [https://skysay-ai.github.io/drama3-h3-talking/](https://skysay-ai.github.io/drama3-h3-talking/)**

[![demo](media/demo.gif)](https://skysay-ai.github.io/drama3-h3-talking/)
In the demo the face is synthetic (Z-Image Turbo), the voice is the LJ Speech public-domain reference, and the speech comes from the [Emo-W4](https://github.com/skyzer/drama3-quant-bench) Drama 3 build (weights: [skysay/drama3-emo-w4](https://huggingface.co/skysay/drama3-emo-w4)). Voice track: [▶ play](https://skysay-ai.github.io/drama3-h3-talking/) · [mp4](media/mp4/demo_voice.mp4) · [wav](media/demo_voice.wav)

## Pipeline
1. **Stage A, audio:** ComfyUI-Drama3 (Loader → Encode voice → Generate → Decode).
2. **`/free`:** Drama 3 is unloaded. Drama 3 and H3 are never resident at the same time.
3. **Stage B, video:** `MiniMaxH3ReferenceToVideo` takes the face as `ref_image_0` and the take as `ref_audio_0`. Then `MiniMaxH3AddGuide` anchors the take at frame 0 (this is the lip-sync), followed by `res_multistep` for 20 steps with sigma shift 12/3, VAE decode, and mux with the original take.

## Files
- `workflows/drama3_to_h3_ref2va_api.json`: the single API-format graph.
- `workflows/stageA_drama3_api.json` and `workflows/stageB_h3_api.json`: the two stages as separate graphs.
- `b5_wf.py`: builds the graphs and runs A → `/free` → B on a ComfyUI server. Set these environment variables:
  - `B5_TEXT`: the line to speak
  - `B5_FACE`: the face image
  - `B5_PROMPT`: the H3 scene prompt
  - `B5_MODEL`: the Drama 3 model file
  - `B5_EXPERTS` and `B5_CACHE`: Drama 3 expert offload settings
  - `B5_SEED`: the H3 noise seed

## Requirements
- ComfyUI ≥ 0.40 (core MiniMax H3 nodes) and [ComfyUI-Drama3](https://github.com/PedroMarinhoDev/ComfyUI-Drama3).
- **H3 models:**
  - `minimax_h3_ref2va_pruned_bf16`
  - `qwen3vl_32b_minimax_h3_nvfp4_awq` text encoder
  - H3 video and audio VAEs
- **Speed:** measured on a 96 GB RTX PRO 6000. Stage A took 18–42 s and stage B about 130–190 s for a 7–9 s clip.

## Licenses and responsible use
- **MiniMax H3 Community License:** it excludes the EU, UK, South Korea and USA from the Applicable Territory, it requires a visible "MiniMax H3" attribution in products, and it has a revenue cap. Read it before you use this.
- **Fish Audio Community License:** commercial use is free only below USD 500k revenue, and it does not cover a hosted TTS or voice-cloning service.
- **Consent:** only use faces and voices you have consent for, and disclose synthetic media.
- This repository's code and workflow JSON are MIT.
