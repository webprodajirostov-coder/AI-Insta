# Affiliate UGC MVP

A deliberately tiny experiment inside AI-Insta.

Flow:

reference image + prompt
→ OdiRouter image-to-video
→ mp4
→ optional ffmpeg assembly

This experiment is isolated from the production AI-Insta pipeline.

## First test

Put the Elena reference image at:

experiments/affiliate_ugc/character/elena.png

The OdiRouter API key is read from the existing `ODIROUTER_API_KEY` environment variable. Never commit the key.

Install dependencies:

```bash
pip install requests python-dotenv
```

Run:

```bash
python experiments/affiliate_ugc/generate_video.py \
  --image experiments/affiliate_ugc/character/elena.png \
  --prompt-file experiments/affiliate_ugc/prompts/01_hook.txt \
  --output experiments/affiliate_ugc/output/01_hook.mp4 \
  --duration 5
```

The model can be overridden with `ODIROUTER_VIDEO_MODEL` or `--model`.

## Assemble clips

```bash
python experiments/affiliate_ugc/assemble.py \
  --output experiments/affiliate_ugc/output/final.mp4 \
  experiments/affiliate_ugc/output/01_hook.mp4 \
  experiments/affiliate_ugc/output/02_product.mp4 \
  experiments/affiliate_ugc/output/03_usage.mp4 \
  experiments/affiliate_ugc/output/04_result.mp4
```

No UI, database, agent layer, analytics or publishing is part of this MVP.
