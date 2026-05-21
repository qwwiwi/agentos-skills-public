---
name: groq-voice
description: Transcribe voice messages (.ogg) via Groq Whisper API. When you see <media:audio> in a message, extract the file path and transcribe it using the included script.
---

# Groq Voice Transcription

When you receive a message containing `<media:audio>` tag, it means the user sent a voice message. The audio file path is in the `[media attached: PATH]` line.

## MANDATORY: Transcribe BEFORE responding

When you see `<media:audio>`, you MUST:

1. Extract the .ogg file path from the `[media attached: /path/to/file.ogg ...]` line
2. Run the transcription script:
```
exec 'bash ~/.claude/skills/groq-voice/transcribe.sh "/path/to/file.ogg"'
```
3. Use the transcript text to understand what the user said
4. Respond to the user's spoken message naturally
5. Do NOT mention the transcription process unless asked

## Important
- Always transcribe first, then respond to the content
- The script uses Groq Whisper API (fast, accurate, supports Russian)
- If transcription fails, tell the user you couldn't process their voice message
- Do NOT say "I can't listen to audio" — you CAN via this script
