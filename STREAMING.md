# Streaming-provider links (optional metadata)

The published JSON may store verified, publicly shareable Disney+ content IDs and links for episodes, shorts, specials and films. These are plain **links**, not embedded playback or a guarantee that a title is available in every region.

Episode records also include `original_aspect_ratio`. That describes the original episode format, not the viewer's current Disney+ Remastered Aspect Ratio setting or a second Disney+ content ID.

A record may optionally contain:

```json
"streaming": {
  "disney_plus": {
    "content_id": "verified-public-content-id",
    "url": "https://www.disneyplus.com/play/verified-public-content-id"
  }
}
```

Either `url` or `content_id` may be provided; both must agree if supplied. Values above are placeholders: **do not import them**. Use IDs copied from real Disney+ pages. Do not fabricate content IDs from season/episode numbers.

- Disney+ does not provide a documented public link parameter that forces original 4:3 versus remastered 16:9 playback.
- No supported public URL parameters are known for forcing audio language, subtitle language, timestamps or selected playback intervals.
- Keep scene timestamps as separate metadata if needed; don't append unverified query parameters to these URLs.
- Playback region availability, language tracks, and subtitle options change. They should not be hardcoded as universal guarantees.
- Affiliate signup tracking is **not** assumed compatible with episode deep links. Keep any approved affiliate signup links distinct from playback URLs and label them appropriately.
- Do not upload video clips or copyrighted subtitles as part of this metadata project without permission.

Disney+ content IDs have been imported for many records; see [DISNEY_PLUS_IDS.md](DISNEY_PLUS_IDS.md) for their source, matching decisions, and limitations. Consumers can add verified direct links individually through pull requests.

The public episode guide at `/episodes/` constructs `https://www.disneyplus.com/play/<content_id>` links when an ID is present. These convenience links are generated for the website only; the API still publishes the ID without asserting that the target currently plays or is available in a given region. A separately verified `streaming.disney_plus.url` may still be added to a record.
