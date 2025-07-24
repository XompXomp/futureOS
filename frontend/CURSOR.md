# Project Overview: Health AI Chatbot Frontend

## 1. Purpose
A privacy-conscious, real-time health chatbot frontend integrating two backends:
- **Unmute (audio-first, real-time AI, aka Gemma)**
- **Llama (text-based, context-aware AI)**

## 2. Key Features
- **Text and audio chat**: Users can interact via text or microphone.
- **Real-time audio streaming**: Audio replies are streamed and played in real time using Web Workers and AudioWorklets.
- **Live transcription**: Audio input is transcribed in real time, buffered, and flushed to chat and Llama on speech stop.
- **Patient profile debug display**: The current patient profile is always visible at the top of the UI and auto-updates live.
- **Conversation and memory management**: All data is stored in local IndexedDB (via Dexie) for privacy and offline support.
- **Automatic profile and memory updates**: Any updates from Llama or Unmute are immediately reflected in the UI and local DB.
- **Extra info injection**: Llama can provide extra info, which is injected into Unmute's prompt as system knowledge.
- **Voice selection**: The frontend can set the TTS voice for Unmute.

## 3. Data Model (IndexedDB)
- **PatientProfile**: uid, name, age, bloodType, allergies, treatment (medicationList, dailyChecklist, appointment, recommendations, sleepHours, sleepQuality)
- **Conversation**: cid, tags, conversation (array of {sender, text})
- **Memory**: id, episodes, procedural, semantic

## 4. Backend Integration
- **Unmute (Gemma)**: WebSocket (`ws://<unmute-server>:<port>/v1/realtime`)
  - Sends: session.update, input_audio_buffer.append, input_text
  - Receives: response.text.delta, response.audio.delta, conversation.item.input_audio_transcription.delta, updatedPatientProfile, updatedConversation
- **Llama**: HTTP POST (`http://<llama-server>:<port>/api/agent`)
  - Sends: prompt, patientProfile, memory
  - Receives: updatedPatientProfile, updatedMemory, extraInfo

## 5. UI Flow
- Patient profile is loaded and displayed at the top (auto-updates live).
- User sends text or audio:
  - Message is appended to conversation and sent to both Unmute (via WS) and Llama (via HTTP POST, with profile and memory).
  - Audio is streamed, transcribed, and buffered; transcription is flushed to chat and Llama on speech stop.
- AI replies (text/audio) are streamed from Unmute and displayed/played in real time.
- Any updates to patient profile, memory, or conversation from either backend are immediately reflected in the UI and DB.
- Extra info from Llama is injected into Unmute's prompt as system knowledge (never as user-provided info).

## 6. System Prompt (LLM Behavior)
- The LLM is instructed to treat extra info as its own knowledge, never thank the user, never disclaim, and always answer as if it already knew the info.
- See `unmute/unmute/llm/system_prompt.py` for full prompt logic and templates.

## 7. Extensibility
- Additional AI agents can be integrated by exposing REST endpoints and following the same context/update pattern.
- The frontend is modular and can be extended with new memory types, user data, or backend endpoints.

## 8. Developer Notes
- All state is managed in React and Dexie; UI auto-updates on any DB or backend change.
- Audio streaming uses Web Workers and AudioWorklets for low-latency playback.
- Debug logging is present throughout for tracing state and data flow.

---

For further details, see `info.md` for a full architecture and data flow summary.

