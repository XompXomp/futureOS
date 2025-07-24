# Health AI Chatbot Frontend: Architecture & Data Flow (2024)

---

## 1. Overview
A modular, privacy-focused AI chatbot frontend for health applications, supporting both text and real-time audio chat. Integrates two backends:
- **Unmute (Gemma):** Real-time, audio-first AI (WebSocket)
- **Llama Agent:** Text-based, context-aware AI (REST API)

---

## 2. Local Data Model (IndexedDB via Dexie)
- **PatientProfile**:
  - `uid`, `name`, `age`, `bloodType`, `allergies`,
  - `treatment`: `{ medicationList, dailyChecklist, appointment, recommendations, sleepHours, sleepQuality }`
- **Conversation**:
  - `cid`, `tags`, `conversation`: array of `{ sender: 'user' | 'ai', text }`
- **Memory**:
  - `id` (singleton), `episodes` (array), `procedural` (object), `semantic` (array)

---

## 3. UI Features
- **Chat interface**: Text and audio input, streaming AI replies.
- **Real-time audio streaming**: Uses Web Workers and AudioWorklets for low-latency playback of AI audio replies.
- **Live transcription**: Audio input is transcribed in real time, buffered, and flushed to chat and Llama on speech stop.
- **Patient profile debug display**: Always visible at the top of the UI, auto-updates live with any backend or local change.
- **Conversation and memory management**: All data is stored in IndexedDB for privacy and offline support.
- **Automatic updates**: Any updates from Llama or Unmute (profile, memory, conversation) are immediately reflected in the UI and DB.
- **Extra info injection**: Llama can provide extra info, which is injected into Unmute's prompt as system knowledge (never as user-provided info).
- **Voice selection**: The frontend can set the TTS voice for Unmute.
- **Debug logging**: Extensive debug logs for state and data flow tracing.

---

## 4. Backend Integration
### Unmute (Gemma)
- **WebSocket endpoint:** `ws://<unmute-server>:<port>/v1/realtime`
- **Sends:**
  - `session.update` (session config, voice, etc.)
  - `input_audio_buffer.append` (base64-encoded Opus audio chunks)
  - `conversation.item.input_text` (text input)
- **Receives:**
  - `response.text.delta` (AI text reply, streamed)
  - `response.audio.delta` (AI audio reply, streamed)
  - `conversation.item.input_audio_transcription.delta` (transcribed user speech, streamed)
  - `updatedPatientProfile`, `updatedConversation` (profile/conversation updates)

### Llama Agent
- **HTTP POST endpoint:** `http://<llama-server>:<port>/api/agent`
- **Sends (on every user prompt):**
  - `prompt`: User's input (already appended to conversation)
  - `patientProfile`: Current profile
  - `memory`: Current memory object
- **Receives:**
  - `updatedPatientProfile`, `updatedConversation`, `updatedMemory`
  - `extraInfo` (to be injected into Unmute's prompt)

---

## 5. Data Flow
1. **User sends message (text or audio):**
   - Appends to conversation history.
   - Sends to Unmute (WebSocket) and Llama (HTTP POST, with profile and memory).
   - Audio is streamed, transcribed, and buffered; transcription is flushed to chat and Llama on speech stop.
2. **AI replies:**
   - Unmute streams text/audio reply; both are displayed/played in real time.
   - Llama may return updated profile, memory, or extra info; all are saved and reflected live in the UI.
3. **Profile debug display:**
   - Always shows the current patient profile, auto-updating with any backend or local change.
4. **Extra info injection:**
   - If Llama returns `extraInfo`, it is sent to Unmute as a system message and treated as the AI's own knowledge.

---

## 6. LLM Prompt Logic
- The system prompt (see `unmute/unmute/llm/system_prompt.py`) instructs the AI to:
  - Treat extra info as its own knowledge (never thank the user, never disclaim, never say "I just learned this").
  - Be conversational, ask follow-ups, and use natural spoken language.
  - Handle transcription errors gracefully.
  - Only speak English or French (TTS limitation).
  - Provide a natural, human-like experience.

---

## 7. Extensibility & Developer Notes
- New AI agents can be added by exposing REST endpoints and following the same context/update pattern.
- The frontend is modular and can be extended with new memory types, user data, or backend endpoints.
- All state is managed in React and Dexie; UI auto-updates on any DB or backend change.
- Audio streaming uses Web Workers and AudioWorklets for low-latency playback.
- Debug logging is present throughout for tracing state and data flow.

---

**Summary:**
This app is a robust, modular, privacy-conscious AI chat frontend that coordinates between a real-time audio AI (Unmute/Gemma) and a flexible, context-aware Llama agent, with all data flows and updates managed through clear, well-defined endpoints and local storage. The UI is always in sync with the latest backend and local state, and is designed for extensibility and developer clarity.
