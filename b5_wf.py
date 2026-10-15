"""B5: Drama3 -> H3 Ref2VA lip-sync. Builds API workflows (stage A audio, stage B video, unified) and runs A,/free,B. usage: b5_wf.py run|export"""
import json, sys, time, urllib.request, os
H = os.environ.get("B5_HOST", "http://127.0.0.1:8188"); COMFY = os.environ.get("COMFY_DIR", "ComfyUI")
TEXT = os.environ.get("B5_TEXT", "[laughing] Oh, you have to hear this. [sobbing] I thought I had lost everything, [laughs] and then it was right there in my pocket.")
REF_TXT = os.environ.get("B5_REF_TEXT", "Printing, in the only sense with which we are at present concerned, differs from most if not from all the arts and crafts represented in the Exhibition")
FACE = os.environ.get("B5_FACE", "synthetic_face.png"); PROMPT = os.environ.get("B5_PROMPT") or ("Close-up studio portrait of a woman with short dark hair talking directly to the camera, her mouth clearly visible and moving in sync with her voice, she laughs warmly then becomes emotional with teary eyes but keeps speaking, face always unobstructed, static camera.")
def stage_a(p="b5/audio"):
    return {"a1": {"class_type": "Drama3Loader", "inputs": {"model_name": os.environ.get("B5_MODEL", "drama3_emo_w4.safetensors"), "experts": os.environ.get("B5_EXPERTS", "in VRAM"), "expert_cache_gb": float(os.environ.get("B5_CACHE", "0")), "second_gpu": "none", "split_layer": 0}},
            "a2": {"class_type": "Drama3CodecLoader", "inputs": {"codec_name": "drama3_codec.safetensors"}},
            "a3": {"class_type": "LoadAudio", "inputs": {"audio": "public_ref.wav"}},
            "a4": {"class_type": "Drama3EncodeVoice", "inputs": {"codec": ["a2", 0], "audio": ["a3", 0], "transcript": REF_TXT}},
            "a5": {"class_type": "Drama3Generate", "inputs": {"model": ["a1", 0], "text": TEXT, "voices.voice0": ["a4", 0], "seed": 11, "temperature": 1.0, "top_p": 0.9, "top_k": 30, "max_frames": 600, "split_long_text": True}},
            "a6": {"class_type": "Drama3Decode", "inputs": {"codec": ["a2", 0], "codes": ["a5", 0]}},
            "a7": {"class_type": "SaveAudio", "inputs": {"audio": ["a6", 0], "filename_prefix": p}}}
def stage_b(audio_ref, length=124, w=576, h=768, steps=20):
    return {"1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_ref2va_pruned_bf16.safetensors", "weight_dtype": "default"}},
            "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
            "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
            "50": {"class_type": "LoadImage", "inputs": {"image": FACE}},
            "10": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"clip": ["2", 0], "prompt": PROMPT, "width": w, "height": h, "length": length, "ref_image_size": "match",
                   "vae": ["3", 0], "audio_vae": ["4", 0], "ref_images.ref_image_0": ["50", 0], "ref_audios.ref_audio_0": audio_ref}},
            "9": {"class_type": "MiniMaxH3AddGuide", "inputs": {"positive": ["10", 0], "audio_vae": ["4", 0], "latent": ["10", 1], "audio": audio_ref, "frame_idx": 0}},
            "11": {"class_type": "MiniMaxH3SigmaShift", "inputs": {"model": ["1", 0], "shift_video": 12.0, "shift_audio": 3.0}},
            "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
            "13": {"class_type": "BasicScheduler", "inputs": {"model": ["11", 0], "scheduler": "simple", "steps": steps, "denoise": 1.0}},
            "14": {"class_type": "BasicGuider", "inputs": {"model": ["11", 0], "conditioning": ["9", 0]}},
            "15": {"class_type": "RandomNoise", "inputs": {"noise_seed": int(os.environ.get("B5_SEED", "42"))}},
            "16": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["15", 0], "guider": ["14", 0], "sampler": ["12", 0], "sigmas": ["13", 0], "latent_image": ["10", 1]}},
            "17": {"class_type": "VAEDecode", "inputs": {"samples": ["16", 0], "vae": ["3", 0]}},
            "19": {"class_type": "CreateVideo", "inputs": {"images": ["17", 0], "fps": 24.0, "audio": audio_ref, "bit_depth": "auto", "color_space": "sRGB"}},
            "20": {"class_type": "SaveVideo", "inputs": {"video": ["19", 0], "filename_prefix": "b5/talking", "format": "auto", "codec": "auto"}}}
def post(wf):
    r = json.load(urllib.request.urlopen(urllib.request.Request(H + "/prompt", json.dumps({"prompt": wf}).encode(), {"Content-Type": "application/json"})))
    pid = r["prompt_id"]; t = time.time()
    while True:
        h = json.load(urllib.request.urlopen(f"{H}/history/{pid}"))
        if pid in h:
            s = h[pid]["status"]; print(s["status_str"], round(time.time() - t, 1), json.dumps(h[pid]["outputs"])[:400], flush=True)
            if s["status_str"] != "success": print(json.dumps(s["messages"])[-1500:]); sys.exit(1)
            return h[pid]["outputs"]
        time.sleep(3)
def free():
    urllib.request.urlopen(urllib.request.Request(H + "/free", json.dumps({"unload_models": True, "free_memory": True}).encode(), {"Content-Type": "application/json"}))
if sys.argv[1] == "export":
    a = stage_a(); b = stage_b(["a6", 0]); json.dump({**a, **b}, open("drama3_to_h3_ref2va_api.json", "w"), indent=1)
    json.dump(stage_a(), open("stageA_drama3_api.json", "w"), indent=1); json.dump(stage_b(["30", 0]) | {"30": {"class_type": "LoadAudio", "inputs": {"audio": "drama3_take.flac"}}}, open("stageB_h3_api.json", "w"), indent=1); print("exported")
else:
    o = post(stage_a()); fn = o["a7"]["audio"][0]; print("audio", fn)
    free(); time.sleep(5)
    src = os.path.expanduser(f"{COMFY}/output/{fn['subfolder']}/{fn['filename']}")
    os.system(f"cp '{src}' {COMFY}/input/drama3_take.flac")
    import subprocess; dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
    n = int(dur * 24); k = max(0, (n - 5 + 16) // 17); L = min(362, max(124, 17 * k + 5)); print("dur", dur, "length", L, flush=True)
    wf = stage_b(["30", 0], length=L); wf["30"] = {"class_type": "LoadAudio", "inputs": {"audio": "drama3_take.flac"}}
    post(wf); free()
