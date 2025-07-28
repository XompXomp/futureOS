import React, { useEffect, useState, useRef, RefObject } from 'react';
import './App.css';
import { getPatientProfile, getConversation, updatePatientProfile, updateConversation, PatientProfile, Conversation, getMemory, updateMemory, getLinks, updateLinks, getGeneral, updateGeneral } from './db';
import OpusRecorder from 'opus-recorder';

const WS_URL = 'ws://172.22.225.138:11000/v1/realtime';
const LLAMA_ENDPOINT = 'http://192.168.1.47:5100/api/agent'; // Correct endpoint for Llama agent

function base64DecodeOpus(base64String: string): Uint8Array {
  const binaryString = window.atob(base64String);
  const len = binaryString.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binaryString.charCodeAt(i);
  }
  return bytes;
}

const audioQueueRef: { current: Blob[] } = { current: [] };
let lastAudioUrl: string | null = null;
let isPlaying = false;

function playNextAudio(audioPlayerRef: RefObject<HTMLAudioElement | null>) {
  if (isPlaying || audioQueueRef.current.length === 0 || !audioPlayerRef.current) return;
  const audioBlob = audioQueueRef.current.shift();
  if (!audioBlob) return;
  const audioEl = audioPlayerRef.current;
  if (lastAudioUrl) {
    URL.revokeObjectURL(lastAudioUrl);
    lastAudioUrl = null;
  }
  lastAudioUrl = URL.createObjectURL(audioBlob);
  audioEl.src = lastAudioUrl;
  isPlaying = true;
  audioEl.onended = () => {
    isPlaying = false;
    playNextAudio(audioPlayerRef);
  };
  audioEl.onpause = () => {
    isPlaying = false;
  };
  audioEl.oncanplaythrough = () => {
    audioEl.play().catch((e: any) => {
      console.error('Audio playback error:', e);
    });
    audioEl.oncanplaythrough = null; // Remove handler after first use
  };
}

// Streaming audio playback setup
let audioContext: AudioContext | null = null;
let audioWorkletNode: any = null;
let decoderWorker: Worker | null = null;

function setupStreamingAudio() {
  console.log('[DEBUG] setupStreamingAudio called');
  if (!audioContext) {
    audioContext = new window.AudioContext();
    (window as any).audioContext = audioContext; // Expose for debugging
    console.log('[DEBUG] audioContext created and assigned to window:', audioContext);
  }
  if (!audioWorkletNode) {
    audioContext.audioWorklet
      .addModule('/audio-output-processor.js')
      .then(() => {
        audioWorkletNode = new window.AudioWorkletNode(audioContext!, 'audio-output-processor');
        audioWorkletNode.connect(audioContext!.destination);
        console.log('[DEBUG] AudioWorkletNode created and connected:', audioWorkletNode);
      });
  }
  if (!decoderWorker) {
    decoderWorker = new Worker('/decoderWorker.min.js');
    decoderWorker.onmessage = (event: MessageEvent) => {
      if (!audioWorkletNode) {
        console.log('[DEBUG] PCM frame received but AudioWorkletNode not ready');
        return;
      }
      if (event.data && event.data[0]) {
        console.log('[DEBUG] PCM frame received from decoder:', event.data[0]);
        audioWorkletNode.port.postMessage({ frame: event.data[0], type: 'audio', micDuration: 0 });
      } else {
        console.log('[DEBUG] Decoder worker message with no frame:', event.data);
      }
    };
    decoderWorker.postMessage({
      command: 'init',
      bufferLength: 960, // 20ms at 48kHz
      decoderSampleRate: 24000,
      outputBufferSampleRate: 48000,
      resampleQuality: 0,
    });
  }
}

const App: React.FC = () => {
  const [input, setInput] = useState('');
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  // --- Add state for links and general ---
  const [links, setLinks] = useState<Record<string, any> | null>(null);
  const [general, setGeneral] = useState<any | null>(null);
  const [audioMode, setAudioMode] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);
  const audioChunksRef = useRef<Uint8Array[]>([]);
  const recorderRef = useRef<any>(null);
  // Track if a new user message was just added
  const justAddedUserMessageRef = { current: false };
  // (Reverted) No transcription buffer
  // Buffer for streaming transcription (audio only)
  const transcriptionBufferRef = useRef<string>("");
  const flushTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isRecordingRef = useRef(false);
  const profileRef = useRef<PatientProfile | null>(null);
  useEffect(() => {
    profileRef.current = profile;
    console.log('[DEBUG] profileRef.current updated:', profileRef.current);
  }, [profile]);

  useEffect(() => {
    console.log('[DEBUG] General state changed:', general);
  }, [general]);

  useEffect(() => {
    getPatientProfile().then(result => {
      console.log('[DEBUG] setProfile called with (initial load):', result ?? null);
      setProfile(result ?? null);
    });
    getConversation().then(result => setConversation(result ?? null));
    getLinks().then(result => {
      console.log('[DEBUG] setLinks called with (initial load):', result?.links ?? null);
      setLinks(result?.links ?? null);
    });
    getGeneral().then(result => {
      console.log('[DEBUG] setGeneral called with (initial load):', result?.general ?? null);
      setGeneral(result?.general ?? null);
    });
  }, []);

  // WebSocket connection
  useEffect(() => {
    const ws = new window.WebSocket(WS_URL, 'realtime');
    wsRef.current = ws;
    ws.onopen = () => {
      // Send session.update with required fields
      ws.send(JSON.stringify({
        type: 'session.update',
        session: {
          instructions: {
            type: 'constant',
            text: 'You are a helpful health assistant.'
          },
          voice: 'unmute-prod-website/developer-1.mp3', // Dev (news)
          allow_recording: true
        }
      }));
    };
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('[DEBUG] WebSocket message received:', data);
        // Handle text response from server (Unmute protocol: response.text.delta or unmute.response.text.delta.ready)
        if (
          (data.type === 'response.text.delta' && data.text) ||
          (data.type === 'unmute.response.text.delta.ready' && data.delta)
        ) {
          const text = data.text || data.delta;
          setConversation(prev => {
            if (!prev) return prev;
            const lastMsg = prev.conversation[prev.conversation.length - 1];
            if (lastMsg && lastMsg.sender === 'ai' && !justAddedUserMessageRef.current) {
              // Update last assistant message
              const updated = {
                ...prev,
                conversation: [
                  ...prev.conversation.slice(0, -1),
                  { ...lastMsg, text: lastMsg.text + text }
                ]
              };
              updateConversation(updated);
              return updated;
            } else {
              // Start new assistant message
              justAddedUserMessageRef.current = false;
              const updated = {
                ...prev,
                conversation: [...prev.conversation, { sender: 'ai' as 'ai', text }]
              };
              updateConversation(updated);
              return updated;
            }
          });
        }
        // --- BEGIN BUFFERED FLUSH TRANSCRIPTION LOGIC (NO CLEAR ON SPEECH_STARTED) ---
        // Do NOT clear the buffer on speech_started
        if (data.type === 'input_audio_buffer.speech_started') {
          console.log('[DEBUG] [speech_started] Begin new utterance (buffer NOT cleared).');
          isRecordingRef.current = true;
          if (flushTimeoutRef.current) {
            clearTimeout(flushTimeoutRef.current);
            flushTimeoutRef.current = null;
          }
        }

        if (data.type === 'conversation.item.input_audio_transcription.delta' && data.delta) {
          transcriptionBufferRef.current += (transcriptionBufferRef.current ? ' ' : '') + data.delta;
          console.log('[DEBUG] [delta] Appended:', data.delta, '| Buffer now:', transcriptionBufferRef.current);
        }

        if (data.type === 'input_audio_buffer.speech_stopped') {
          isRecordingRef.current = false;
          // Start a short timer to catch any late deltas
          if (flushTimeoutRef.current) clearTimeout(flushTimeoutRef.current);
          console.log('[DEBUG] flushTimeoutRef set, profile at creation:', profile, 'profileRef.current:', profileRef.current);
          flushTimeoutRef.current = setTimeout(() => {
            console.log('[DEBUG] [speech_stopped] Buffer before flush:', transcriptionBufferRef.current);
            const bufferedText = transcriptionBufferRef.current.trim();
            console.log('[DEBUG] profileRef.current at flush:', profileRef.current);
            console.log('[DEBUG] profile state at flush:', profile);
            if (bufferedText) {
              setConversation(prev => {
                if (!prev) return prev;
                console.log('[DEBUG] [flush] Adding user message to chat:', bufferedText);
                const updated = {
                  ...prev,
                  conversation: [...prev.conversation, { sender: 'user' as 'user', text: bufferedText }]
                };
                updateConversation(updated);
                return updated;
              });
              // --- SEND TO UNMUTE BACKEND ---
              if (wsRef.current && wsRef.current.readyState === 1) {
                wsRef.current.send(JSON.stringify({
                  type: 'conversation.item.input_text',
                  text: bufferedText,
                  patientProfile: profileRef.current,
                }));
              }
              // --- (Removed) SEND TO LLAMA ---
              // if (profileRef.current) {
              //   sendPromptToLlama(bufferedText);
              // } else {
              //   console.warn('[DEBUG] [flush] Not sending to Llama: patientProfile is null');
              // }
            } else {
              console.log('[DEBUG] [flush] Buffer empty, nothing to add to chat.');
            }
            transcriptionBufferRef.current = "";
            console.log('[DEBUG] [speech_stopped] Buffer cleared after flush.');
            flushTimeoutRef.current = null;
          }, 150); // 150ms buffer window
        }
        // --- END BUFFERED FLUSH TRANSCRIPTION LOGIC (NO CLEAR ON SPEECH_STARTED) ---
        // Streaming audio playback
        if (data.type === 'response.audio.delta' && data.delta) {
          setupStreamingAudio();
          const opusChunk = base64DecodeOpus(data.delta);
          if (decoderWorker) {
            decoderWorker.postMessage({ command: 'decode', pages: opusChunk }, [opusChunk.buffer]);
          }
        }
        // No need to handle response.audio.done for streaming playback
      } catch (e: any) {
        // Ignore parse errors
        console.error('WebSocket message handling error:', e);
      }
    };
    ws.onerror = () => {};
    ws.onclose = () => {};
    return () => {
      ws.close();
      // Clean up streaming audio resources
      if (audioContext) { audioContext.close(); audioContext = null; }
      if (decoderWorker) { decoderWorker.terminate(); decoderWorker = null; }
      audioWorkletNode = null;
    };
  }, []);

  // Send text input as a message
  const handleSendPrompt = async (prompt: string, options: { updates?: any, links?: any[], general?: any } = {}) => {
    console.log('handleSendPrompt called', {
      wsReadyState: wsRef.current?.readyState,
      hasProfile: !!profile,
      hasConversation: !!conversation,
      prompt
    });
    if (!profile || !conversation) {
      console.log('Not sending: missing profile or conversation', {
        wsReadyState: wsRef.current?.readyState,
        hasProfile: !!profile,
        hasConversation: !!conversation
      });
      return;
    }
    setLoading(true);
    const updatedConv = { ...conversation, conversation: [...conversation.conversation, { sender: 'user' as 'user', text: prompt }] };
    setConversation(updatedConv);
    await updateConversation(updatedConv);
    // Send to Gemma (Unmute) via WebSocket
    if (wsRef.current && wsRef.current.readyState === 1) {
      console.log('Sending message to backend', {
        type: 'conversation.item.input_text',
        text: prompt,
        patientProfile: profile
      });
      wsRef.current.send(JSON.stringify({
        type: 'conversation.item.input_text',
        text: prompt,
        patientProfile: profile,
      }));
    }
    // Send to Llama via REST
    const memory = await getMemory();
    // --- Build request payload with required fields ---
    const requestBody: any = {
      prompt,
      patientProfile: profile,
      memory: memory || { id: 'memory', memory: [] }
    };
    if (options.updates) requestBody.updates = options.updates;
    // Note: conversation, links, general are accessed via local backend bridge
    fetch('http://172.22.225.47:5100/api/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
      .then(res => res.json())
      .then(data => {
        if (data.updatedPatientProfile || data.patientProfile) {
          const newProfile = data.updatedPatientProfile || data.patientProfile;
          console.log('[DEBUG] setProfile called with (Llama/Unmute response):', newProfile);
          setProfile(newProfile);
          updatePatientProfile(newProfile);
        }
        if (data.updatedMemory || data.memory) {
          const newMemory = data.updatedMemory || data.memory;
          updateMemory(newMemory);
        }
        if (data.updates) {
          // handle updates if needed
          console.log('[DEBUG] Received updates from Llama:', data.updates);
        }
        if (data.links) {
          setLinks(data.links);
          console.log('[DEBUG] Received links from Llama:', data.links);
        }
        if (data.general) {
          setGeneral(data.general);
          console.log('[DEBUG] Received general from Llama:', data.general);
        }
        // Forward extraInfo from Llama to Unmute if present
        if (data.extraInfo) {
          console.log('[DEBUG] Received extraInfo from Llama:', data.extraInfo);
          if (wsRef.current && wsRef.current.readyState === 1) {
            console.log('[DEBUG] Forwarding extraInfo to Unmute');
            wsRef.current.send(JSON.stringify({
              type: 'llama.extra_info',
              extra_info: data.extraInfo
            }));
          }
        }
      })
      .catch(() => {});
    setInput('');
    setLoading(false);
  };

  // Audio recording logic (streaming)
  const handleAudioRecord = async () => {
    if (recording) {
      recorderRef.current?.stop();
      setRecording(false);
      return;
    }
    try {
      const recorder = new OpusRecorder({
        numberOfChannels: 1,
        encoderSampleRate: 24000,
        maxFramesPerPage: 2,
        streamPages: true,
      });
      recorder.ondataavailable = (opusChunk: Uint8Array) => {
        console.log('Audio chunk sent', opusChunk);
        if (wsRef.current && wsRef.current.readyState === 1) {
          // Encode the Opus chunk as base64 before sending
          const base64Audio = btoa(String.fromCharCode(...Array.from(opusChunk)));
          wsRef.current.send(JSON.stringify({
            type: 'input_audio_buffer.append',
            audio: base64Audio,
            patientProfile: profile,
          }));
        }
      };
      recorder.onstop = () => {
        if (wsRef.current && wsRef.current.readyState === 1) {
          wsRef.current.send(JSON.stringify({ type: 'input_audio_buffer.stop' }));
        }
        setRecording(false);
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (err) {
      alert('Audio recording error');
    }
  };

  // Stop recording when backend signals end of audio response
  useEffect(() => {
    if (!recording) return;
    const ws = wsRef.current;
    if (!ws) return;
    const stopHandler = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'response.audio.stop') {
          recorderRef.current?.stop();
        }
        // Handle updated patient profile and conversation from Llama
        if (data.updatedPatientProfile) {
          setProfile(data.updatedPatientProfile);
          updatePatientProfile(data.updatedPatientProfile);
        }
        if (data.updatedConversation) {
          setConversation(data.updatedConversation);
          updateConversation(data.updatedConversation);
        }
      } catch {}
    };
    ws.addEventListener('message', stopHandler);
    return () => {
      ws.removeEventListener('message', stopHandler);
    };
  }, [recording]);

  // Also handle updated patient profile and conversation on any message
  useEffect(() => {
    const ws = wsRef.current;
    if (!ws) return;
    const updateHandler = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        if (data.updatedPatientProfile) {
          setProfile(data.updatedPatientProfile);
          updatePatientProfile(data.updatedPatientProfile);
        }
        if (data.updatedConversation) {
          setConversation(data.updatedConversation);
          updateConversation(data.updatedConversation);
        }
      } catch {}
    };
    ws.addEventListener('message', updateHandler);
    return () => {
      ws.removeEventListener('message', updateHandler);
    };
  }, []);

  useEffect(() => {
    if (!audioPlayerRef.current) return;
    const audioEl = audioPlayerRef.current;
    const onEnded = () => {
      if (audioPlayerRef.current) playNextAudio(audioPlayerRef);
    };
    audioEl.addEventListener('ended', onEnded);
    return () => {
      audioEl.removeEventListener('ended', onEnded);
    };
  }, []);

  // Function to send prompt to Llama (must be inside App to access wsRef)
  async function sendPromptToLlama(prompt: string, options: { updates?: any, links?: any[], general?: any } = {}) {
    console.log('[DEBUG] sendPromptToLlama called, profileRef.current:', profileRef.current, 'profile:', profile);
    if (!profileRef.current) {
      console.warn('[DEBUG] sendPromptToLlama: patientProfile is null');
      return;
    }
    const memory = await getMemory();
    console.log('[DEBUG] Sending to Llama:', { prompt, patientProfile: profileRef.current, memory });
    // --- Build request payload with required fields ---
    const requestBody: any = {
      prompt,
      patientProfile: profileRef.current,
      memory: memory || { id: 'memory', memory: [] }
    };
    if (options.updates) requestBody.updates = options.updates;
    // Note: conversation, links, general are accessed via local backend bridge
    fetch('http://172.22.225.47:5100/api/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    })
      .then(res => res.json())
      .then(data => {
        console.log('[DEBUG] Llama response:', data);
        if (data.updatedPatientProfile || data.patientProfile) {
          const newProfile = data.updatedPatientProfile || data.patientProfile;
          console.log('[DEBUG] setProfile called with (Llama/Unmute response):', newProfile);
          setProfile(newProfile);
          updatePatientProfile(newProfile);
        }
        if (data.updatedMemory || data.memory) {
          const newMemory = data.updatedMemory || data.memory;
          updateMemory(newMemory);
        }
        if (data.updates) {
          // handle updates if needed
          console.log('[DEBUG] Received updates from Llama:', data.updates);
        }
        if (data.links) {
          setLinks(data.links);
          console.log('[DEBUG] Received links from Llama:', data.links);
        }
        if (data.general) {
          setGeneral(data.general);
          console.log('[DEBUG] Received general from Llama:', data.general);
        }
        if (data.extraInfo) {
          console.log('[DEBUG] Received extraInfo from Llama:', data.extraInfo);
          if (wsRef.current && wsRef.current.readyState === 1) {
            console.log('[DEBUG] Forwarding extraInfo to Unmute');
            wsRef.current.send(JSON.stringify({
              type: 'llama.extra_info',
              extra_info: data.extraInfo
            }));
          }
        }
      })
      .catch(err => console.error('[DEBUG] Llama error:', err));
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: 16 }}>
      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        {/* Left side - Chatbot */}
        <div style={{ flex: 1, maxWidth: 600 }}>
          <h2>AI Health Chatbot</h2>
          <div style={{ minHeight: 300, background: '#f7f7f7', padding: 12, borderRadius: 8, marginBottom: 12 }}>
            {conversation?.conversation.map((msg, idx) => (
              <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '8px 0' }}>
                <span style={{
                  display: 'inline-block',
                  background: msg.sender === 'user' ? '#3182ce' : '#fff',
                  color: msg.sender === 'user' ? '#fff' : '#222',
                  borderRadius: 16,
                  padding: '8px 14px',
                  maxWidth: '75%',
                }}>{msg.text}</span>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={handleAudioRecord}
              disabled={loading || !profile}
              style={{ background: recording ? '#e53e3e' : '#3182ce', color: '#fff', border: 'none', borderRadius: '50%', width: 40, height: 40, fontSize: 18 }}
              aria-label={recording ? 'Stop recording' : 'Record audio'}
            >
              {recording ? '■' : '🎤'}
            </button>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && input.trim() && !loading) handleSendPrompt(input.trim()); }}
              disabled={loading}
              placeholder="Type your message..."
              style={{ flex: 1, padding: '8px 12px', borderRadius: 16, border: '1px solid #ccc' }}
            />
            <button onClick={() => input.trim() && !loading && handleSendPrompt(input.trim())} disabled={loading || !input.trim()} style={{ background: '#3182ce', color: '#fff', border: 'none', borderRadius: '50%', width: 40, height: 40, fontSize: 18 }}>
              ➤
            </button>
          </div>
        </div>

        {/* Right side - Patient Profile, Links, and General */}
        <div style={{ width: 400, flexShrink: 0 }}>
          {profile && (
            <div style={{ background: '#eef', padding: 12, borderRadius: 8, marginBottom: 12 }}>
              <h4>Patient Profile</h4>
              <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0 }}>
                {JSON.stringify(profile, null, 2)}
              </pre>
            </div>
          )}
          <div style={{ background: '#efe', padding: 12, borderRadius: 8, marginBottom: 12 }}>
            <h4>Links</h4>
            {links ? (
              <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0 }}>{JSON.stringify(links, null, 2)}</pre>
            ) : (
              <p style={{ fontSize: 12, color: '#666', margin: 0, fontStyle: 'italic' }}>No links available</p>
            )}
          </div>
          <div style={{ background: '#ffe', padding: 12, borderRadius: 8, marginBottom: 12 }}>
            <h4>General</h4>
            {general ? (
              <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0 }}>{JSON.stringify(general, null, 2)}</pre>
            ) : (
              <p style={{ fontSize: 12, color: '#666', margin: 0, fontStyle: 'italic' }}>No general information available</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
