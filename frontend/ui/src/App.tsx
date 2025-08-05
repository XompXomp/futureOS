import React, { useEffect, useState, useRef, RefObject } from 'react';
import './App.css';
import { getPatientProfile, getConversation, updatePatientProfile, updateConversation, PatientProfile, Conversation, Memory, getMemory, updateMemory, getLinks, updateLinks, getGeneral, updateGeneral, Updates, getUpdates, updateUpdates } from './db';
import OpusRecorder from 'opus-recorder';
// @ts-ignore
import msgpack from 'msgpack-lite';

// Type declaration for msgpack-lite if types are not available
declare module 'msgpack-lite' {
  export function decode(data: Uint8Array): any;
  export function encode(data: any): Uint8Array;
}

const LLAMA_ENDPOINT = 'http://172.22.225.47:5100/api/agent'; // Local backend endpoint
const LLAMA_STREAM_ENDPOINT = 'http://172.22.225.47:5100/api/agent/stream'; // New streaming endpoint
const UNMUTE_STT_ENDPOINT = 'ws://172.22.225.138:11004/api/asr-streaming'; // Direct STT endpoint

// === STT ADD-ON: Proxy endpoint for STT ===
const STT_PROXY_URL = 'ws://localhost:8080'; // STT proxy endpoint

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

// Track received chunk types for streaming state management
const receivedChunkTypesRef = { current: new Set<string>() };

// Streaming chunk handler for new API
function handleStreamingChunk(chunk: any, setConversation: any, updateConversation: any, setProfile: any, updatePatientProfile: any, setLinks: any, setGeneral: any, setUpdates: any, updateUpdates: any, setStreamingText: any, setIsStreaming: any, setStreamingError: any, setStreamingStatus: any, setLoading: any, setMemory: any, updateMemory: any) {
  console.log('[DEBUG] Streaming chunk received:', chunk);
  console.log('[DEBUG] Chunk type:', chunk.type);
  console.log('[DEBUG] Chunk data:', chunk.data);
  console.log('[DEBUG] Chunk data type:', typeof chunk.data);
  console.log('[DEBUG] Chunk data keys:', chunk.data ? Object.keys(chunk.data) : 'null');
  
  // Track this chunk type
  receivedChunkTypesRef.current.add(chunk.type);
  console.log('[DEBUG] Received chunk types so far:', Array.from(receivedChunkTypesRef.current));
  
  switch (chunk.type) {
    case 'streaming_started':
      console.log('Agent processing started:', chunk.data.message);
      setStreamingStatus(chunk.data.message);
      setIsStreaming(true);
      setStreamingText('');
      setStreamingError(null);
      // Reset chunk type tracking for new streaming session
      receivedChunkTypesRef.current.clear();
      console.log('[DEBUG] Reset chunk type tracking for new streaming session');
      break;
      
    case 'unmute_connecting':
      console.log('Connecting to voice assistant...');
      setStreamingStatus('Connecting to voice assistant...');
      // Reset chunk type tracking for new Unmute connection
      receivedChunkTypesRef.current.clear();
      console.log('[DEBUG] Reset chunk type tracking for new Unmute connection');
      break;
      
    case 'unmute_connected':
      console.log('Connected to voice assistant');
      setStreamingStatus('Connected to voice assistant');
      break;
      
    case 'unmute_streaming_started':
      console.log('Voice assistant is responding...');
      setStreamingStatus('Voice assistant is responding...');
      break;
      
    case 'text_chunk':
      // Handle real-time text chunks from Unmute
      const textChunk = chunk.data.text;
      console.log('Text chunk:', textChunk);
      
      // Add to streaming text buffer
      setStreamingText((prev: string) => prev + textChunk);
      
      // Update conversation in real-time
      setConversation((prev: Conversation | null) => {
        if (!prev) return prev;
        const lastMsg = prev.conversation[prev.conversation.length - 1];
        if (lastMsg && lastMsg.sender === 'ai') {
          // Update last assistant message
          const updated = {
            ...prev,
            cid: prev.cid || 'conv-001',
            conversation: [
              ...prev.conversation.slice(0, -1),
              { ...lastMsg, text: lastMsg.text + textChunk }
            ]
          };
          updateConversation(updated);
          return updated;
        } else {
          // Start new assistant message
          const updated = {
            ...prev,
            cid: prev.cid || 'conv-001',
            conversation: [...prev.conversation, { sender: 'ai' as 'ai', text: textChunk }]
          };
          updateConversation(updated);
          return updated;
        }
      });
      break;
      
    case 'audio_chunk':
      // Handle real-time audio chunks from Unmute
      const audioChunk = chunk.data.audio;
      console.log('Audio chunk received:', audioChunk.length, 'bytes');
      
      // Decode base64 audio and stream to player
      const audioData = base64DecodeOpus(audioChunk);
      setupStreamingAudio();
      if (decoderWorker) {
        decoderWorker.postMessage({ command: 'decode', pages: audioData }, [audioData.buffer]);
      }
      break;
      
    case 'text_complete':
      console.log('Text response complete');
      setStreamingStatus('Text response complete');
      break;
      
    case 'audio_complete':
      console.log('Audio response complete');
      setStreamingStatus('Audio response complete');
      break;
      
    case 'unmute_complete':
      console.log('Voice assistant response complete');
      setStreamingStatus('Voice assistant response complete');
      
      // Check if final_result has also been received before clearing streaming state
      const hasFinalResult = receivedChunkTypesRef.current.has('final_result');
      console.log('[DEBUG] unmute_complete received. Has final_result:', hasFinalResult);
      
      if (hasFinalResult) {
        console.log('[DEBUG] Both unmute_complete and final_result received, clearing streaming state');
        // Clear streaming state
        setIsStreaming(false);
        setStreamingText('');
        setStreamingStatus('');
        setLoading(false);
        
        // Clean up streaming connection
        if ((window as any).cleanupStreaming) {
          (window as any).cleanupStreaming();
          (window as any).cleanupStreaming = null;
        }
        
        // Reset chunk type tracking
        receivedChunkTypesRef.current.clear();
      } else {
        console.log('[DEBUG] unmute_complete received but final_result not yet received, keeping streaming state active');
      }
      break;
      
    case 'final_result':
      // Handle final result from agent workflow
      console.log('Agent processing complete');
      const result = chunk.data;
      console.log('[DEBUG] final_result - result:', result);
      console.log('[DEBUG] final_result - result.updatedPatientProfile:', result.updatedPatientProfile);
      
      if (result.updatedPatientProfile) {
        console.log('[DEBUG] Updating profile from final_result:', result.updatedPatientProfile);
        setProfile(result.updatedPatientProfile);
        updatePatientProfile(result.updatedPatientProfile);
      }
      if (result.updatedMemory) {
        // Append new memories to existing ones
        setMemory((prevMemories: any) => {
          const existingMemories = prevMemories || [];
          const newMemories = result.updatedMemory;
          return [...existingMemories, ...newMemories];
        });
        updateMemory(result.updatedMemory);
      }
      if (result.links) {
        setLinks(result.links);
      }
      if (result.general) {
        setGeneral(result.general);
      }
      if (result.Updates) {
        console.log('[DEBUG] Updating updates from final_result:', result.Updates);
        // Append new updates to existing ones
        setUpdates((prevUpdates: any) => {
          const existingUpdates = prevUpdates || [];
          const newUpdates = result.Updates;
          return [...existingUpdates, ...newUpdates];
        });
        updateUpdates(result.Updates);
      }
      if (result.function){
        console.log('[DEBUG] Updating function from final_result:', result.function);
        (window as any).processUICommand(result.function);
      }
      
      // Check if unmute_complete has also been received before clearing streaming state
      const hasUnmuteComplete = receivedChunkTypesRef.current.has('unmute_complete');
      console.log('[DEBUG] final_result received. Has unmute_complete:', hasUnmuteComplete);
      
      if (hasUnmuteComplete) {
        console.log('[DEBUG] Both final_result and unmute_complete received, clearing streaming state');
        // Clear streaming state
        setIsStreaming(false);
        setStreamingText('');
        setStreamingStatus('');
        setLoading(false);
        
        // Clean up streaming connection
        if ((window as any).cleanupStreaming) {
          (window as any).cleanupStreaming();
          (window as any).cleanupStreaming = null;
        }
        
        // Reset chunk type tracking
        receivedChunkTypesRef.current.clear();
      } else {
        console.log('[DEBUG] final_result received but unmute_complete not yet received, keeping streaming state active');
      }
      break;
      
    case 'error':
    case 'unmute_error':
    case 'unmute_timeout':
    case 'workflow_error':
      console.error('Error:', chunk.data.error || chunk.data.message);
      setStreamingError(chunk.data.error || chunk.data.message);
      setIsStreaming(false);
      setStreamingText('');
      setStreamingStatus('');
      setLoading(false);
      
      // Clean up streaming connection
      if ((window as any).cleanupStreaming) {
        (window as any).cleanupStreaming();
        (window as any).cleanupStreaming = null;
      }
      break;
      
    case 'keepalive':
      // Handle keepalive messages
      console.log('Keepalive received');
      break;
      
    default:
      console.log('Unknown streaming chunk type:', chunk.type);
  }
}

const App: React.FC = () => {
  const [input, setInput] = useState('');
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [profile, setProfile] = useState<PatientProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  // --- Add state for links, general, updates, and memory ---
  const [links, setLinks] = useState<Record<string, any> | null>(null);
  const [general, setGeneral] = useState<any | null>(null);
  const [updates, setUpdates] = useState<any | null>(null);
  const [memory, setMemory] = useState<any | null>(null);
  const [audioMode, setAudioMode] = useState(false);
  const [showProactiveSleepPrompt, setShowProactiveSleepPrompt] = useState(false);
  
  // --- Add streaming state variables ---
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingError, setStreamingError] = useState<string | null>(null);
  const [streamingStatus, setStreamingStatus] = useState<string>('');
  
  // --- Add UI state variables ---
  const [darkMode, setDarkMode] = useState(false);
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
  
  // === STT ADD-ON: STT-related state and refs ===
  const [speechDetected, setSpeechDetected] = useState(false);  // Track when speech is detected
  const sttWsRef = useRef<WebSocket | null>(null);  // Direct STT WebSocket
  // Track sentence buffer and timing
  const currentSentenceBufferRef = useRef<string>("");
  const sentenceTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const conversationRef = useRef<Conversation | null>(null);
  
  // Keep conversation ref in sync with state
  useEffect(() => {
    conversationRef.current = conversation;
  }, [conversation]);
  useEffect(() => {
    profileRef.current = profile;
    console.log('[DEBUG] profileRef.current updated:', profileRef.current);
  }, [profile]);

  // === STT ADD-ON: Cleanup STT connection on component unmount ===
  useEffect(() => {
    return () => {
      // Cleanup STT WebSocket connection when component unmounts
      closeSTTConnection();
      
      // Clear any remaining recording timeout
      if ((window as any).recordingTimeoutId) {
        clearTimeout((window as any).recordingTimeoutId);
        (window as any).recordingTimeoutId = null;
      }
    };
  }, []);

  useEffect(() => {
    console.log('[DEBUG] General state changed:', general);
  }, [general]);

  useEffect(() => {
    console.log('[DEBUG] Links state changed:', links);
  }, [links]);

  useEffect(() => {
    console.log('[DEBUG] Memory state changed:', memory);
  }, [memory]);

  useEffect(() => {     
    // Initialize database with sample data first
    import('./db').then(({ initializeSampleData }) => {
      initializeSampleData().then(() => {
        console.log('[DEBUG] Database initialized with sample data');
        
        // Now load the data
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
        getUpdates().then(result => {
          console.log('[DEBUG] setUpdates called with (initial load):', result?.updates ?? null);
          setUpdates(result?.updates ?? null);
        });
        getMemory().then(result => {
          console.log('[DEBUG] setMemory called with (initial load):', result?.memory ?? null);
          setMemory(result?.memory ?? null);
        });
      }).catch(error => {
        console.error('[DEBUG] Database initialization error:', error);
      });
    });
  }, []);

  // Loading timeout reference for streaming
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Polling mechanism for local backend updates
  useEffect(() => {
    const pollForUpdates = async () => {
      try {
        // First, check for explicit updates
        const response = await fetch('http://localhost:8002/api/latest-update');
        if (response.ok) {
          const update = await response.json();
          if (update.type && update.data) {
            console.log('[DEBUG] Received update from local backend:', update);
            
            switch (update.type) {
              case 'patientProfile':
                console.log('[DEBUG] Updating patient profile from local backend:', update.data);
                setProfile(update.data);
                updatePatientProfile(update.data);
                break;
              case 'links':
                console.log('[DEBUG] Updating links from local backend:', update.data);
                console.log('[DEBUG] Current links state before update:', links);
                setLinks(update.data);
                updateLinks({ id: 'links', links: update.data });
                console.log('[DEBUG] Links state should now be:', update.data);
                break;
              case 'general':
                console.log('[DEBUG] Updating general insights from local backend:', update.data);
                setGeneral(update.data);
                updateGeneral({ id: 'general', general: update.data });
                break;
              case 'function':
                console.log('[DEBUG] Received function call from local backend:', update.data);
                processUICommand(update.data);
                break;
              default:
                console.log('[DEBUG] Unknown update type from local backend:', update.type);
            }
          }
        }

        // Also check current backend state to catch any missed updates
        try {
          const memoryLinksResponse = await fetch('http://localhost:8002/memory-links');
          if (memoryLinksResponse.ok) {
            const backendData = await memoryLinksResponse.json();
            console.log('[DEBUG] Current backend links state:', backendData.links);
            console.log('[DEBUG] Current frontend links state:', links);
            
            // Update if backend has data and frontend is either empty or has different data
            // This ensures external updates are reflected, even if frontend was cleared or has existing data
            if (backendData.links) { // Check if backend has any links data
              const frontendLinksKeys = Object.keys(links || {}); // Use empty object if links is null
              const backendLinksKeys = Object.keys(backendData.links);
              
              // Check if backend has different data than frontend
              const hasDifferentData = backendLinksKeys.some(key => {
                const backendValue = backendData.links[key];
                const frontendValue = (links || {})[key]; // Use empty object if links is null
                return JSON.stringify(backendValue) !== JSON.stringify(frontendValue);
              }) || frontendLinksKeys.length !== backendLinksKeys.length; // Also check if number of keys differs
              
              if (hasDifferentData) {
                console.log('[DEBUG] Backend has different links data, updating frontend');
                setLinks(backendData.links);
                updateLinks({ id: 'links', links: backendData.links });
              }
            }
          }
        } catch (error) {
          console.log('[DEBUG] Failed to check backend state (this is normal if local backend is not running):', error);
        }
      } catch (error) {
        console.log('[DEBUG] Polling for updates failed (this is normal if local backend is not running):', error);
      }
    };

    // Poll every 2 seconds for updates from local backend
    const pollInterval = setInterval(pollForUpdates, 2000);
    
    // Initial poll
    pollForUpdates();

    return () => {
      clearInterval(pollInterval);
    };
  }, []); // Removed [links] dependency to prevent race conditions

  // === STT ADD-ON: STT WebSocket connection management ===
  // Remove the automatic WebSocket connection - we'll create it on demand
  
  // Function to create and setup STT WebSocket connection
  const createSTTConnection = () => {
    if (sttWsRef.current && sttWsRef.current.readyState === WebSocket.OPEN) {
      console.log('[DEBUG] STT WebSocket already connected');
      return;
    }
    
    console.log('[DEBUG] Creating new STT WebSocket connection');
    const sttWs = new window.WebSocket(STT_PROXY_URL);
    sttWsRef.current = sttWs;
    
    sttWs.onopen = () => {
      console.log('[DEBUG] STT WebSocket connected');
      // Try sending authentication token as a message
      try {
        const authMessage = {
          type: "Auth",
          token: "public_token"
        };
        const encoded = msgpack.encode(authMessage);
        sttWs.send(encoded);
        console.log('[DEBUG] Sent authentication message');
      } catch (e) {
        console.log('[DEBUG] Could not send auth message:', e);
      }
    };
    
    sttWs.onmessage = (event) => {
      try {
        // STT uses MessagePack format
        let data;
        if (event.data instanceof Blob) {
          // Handle binary MessagePack data
          event.data.arrayBuffer().then(buffer => {
            try {
              const uint8Array = new Uint8Array(buffer);
              data = msgpack.decode(uint8Array);
              console.log('[DEBUG] STT MessagePack decoded:', data);
              handleSTTMessage(data);
            } catch (e) {
              console.error('[DEBUG] Failed to decode MessagePack:', e);
            }
          });
        } else {
          // Handle text messages (if any)
          console.log('[DEBUG] STT text message:', event.data);
        }
      } catch (e: any) {
        console.error('STT WebSocket message handling error:', e);
      }
    };
    
    sttWs.onerror = (error) => {
      console.error('[DEBUG] STT WebSocket error:', error);
    };
    
    sttWs.onclose = () => {
      console.log('[DEBUG] STT WebSocket closed');
      sttWsRef.current = null;
    };
  };
  
  // Function to close STT WebSocket connection
  const closeSTTConnection = () => {
    if (sttWsRef.current && sttWsRef.current.readyState === WebSocket.OPEN) {
      console.log('[DEBUG] Closing STT WebSocket connection');
      sttWsRef.current.close();
      sttWsRef.current = null;
    }
  };

  // === STT ADD-ON: Handle STT messages - detect sentence completion and send to LLM ===
  const handleSTTMessage = (data: any) => {
    console.log('[DEBUG] Processing STT message:', data);
    console.log('[DEBUG] Message type:', data.type);
    console.log('[DEBUG] Full message data:', JSON.stringify(data, null, 2));
    
    if (data.type === 'Word' && data.text) {
      // Clear any existing sentence timeout
      if (sentenceTimeoutRef.current) {
        clearTimeout(sentenceTimeoutRef.current);
        sentenceTimeoutRef.current = null;
      }
      
      // Add word to sentence buffer
      currentSentenceBufferRef.current += (currentSentenceBufferRef.current ? ' ' : '') + data.text;
      
      // Don't add to conversation display yet - wait for sentence completion
      
      // Set timeout to detect sentence completion and send to LLM
      sentenceTimeoutRef.current = setTimeout(() => {
        const completedSentence = currentSentenceBufferRef.current.trim();
        if (completedSentence && profileRef.current && conversationRef.current) {
          console.log('[DEBUG] Sentence completed, sending to LLM:', completedSentence);
          
          // Close STT WebSocket connection before sending to workflow
          closeSTTConnection();
          
          // Add completed sentence to conversation display
          setConversation(prev => {
            if (!prev) return prev;
            const updated = {
              ...prev,
              conversation: [...prev.conversation, { sender: 'user' as 'user', text: completedSentence }]
            };
            updateConversation(updated);
            return updated;
          });
          
          // Send to LLM using existing handleSendPrompt function
          handleSendPrompt(completedSentence);
          
          // Clear buffer
          currentSentenceBufferRef.current = "";
        } else if (completedSentence) {
          console.log('[DEBUG] Sentence completed but profile/conversation not ready, retrying in 1 second');
          // Retry in 1 second if profile/conversation not ready
          setTimeout(() => {
            if (profileRef.current && conversationRef.current) {
              // Close STT WebSocket connection before sending to workflow
              closeSTTConnection();
              
              // Add completed sentence to conversation display
              setConversation(prev => {
                if (!prev) return prev;
                const updated = {
                  ...prev,
                  conversation: [...prev.conversation, { sender: 'user' as 'user', text: completedSentence }]
                };
                updateConversation(updated);
                return updated;
              });
              
              handleSendPrompt(completedSentence);
              currentSentenceBufferRef.current = "";
            }
          }, 1000);
        }
      }, 2000); // 2 seconds timeout
      
      console.log('[DEBUG] STT Word added to conversation:', data.text);
      setSpeechDetected(true);
      
    } else if (data.type === 'Marker') {
      // Ignore markers (like Unmute backend does)
      console.log('[DEBUG] STT Marker received - ignoring');
      
    } else if (data.type === 'EndWord') {
      console.log('[DEBUG] STT Word ended at time:', data.stop_time);
      
    } else if (data.type === 'Step') {
      // Just log step data for debugging
      console.log('[DEBUG] STT Step received:', data.step_idx, 'pause prediction:', data.prs);
      
      // Check if speech has stopped (for UI feedback only)
      if (data.prs && data.prs.length > 0) {
        const pausePrediction = data.prs[0];
        if (pausePrediction > 0.95) {
          setSpeechDetected(false);
        }
      }
      
    } else if (data.type === 'Ready') {
      console.log('[DEBUG] STT Ready message received');
    } else if (data.type === 'Error') {
      console.error('[DEBUG] STT Error:', data.message);
    } else {
      console.log('[DEBUG] Unknown message type:', data.type);
    }
  };

  // Send text input as a message
  const handleSendPrompt = async (prompt: string, options: { updates?: any, links?: any[], general?: any } = {}) => {
    console.log('handleSendPrompt called', {
      hasProfile: !!profileRef.current,
      hasConversation: !!conversationRef.current,
      prompt
    });
    if (!profileRef.current || !conversationRef.current) {
      console.log('Not sending: missing profile or conversation', {
        hasProfile: !!profileRef.current,
        hasConversation: !!conversationRef.current
      });
      return;
    }
    setLoading(true);
    const updatedConv = { 
      ...conversationRef.current, 
      cid: conversationRef.current.cid || 'conv-001', // Ensure cid exists
      conversation: [...conversationRef.current.conversation, { sender: 'user' as 'user', text: prompt }] 
    };
    setConversation(updatedConv);
    await updateConversation(updatedConv);
    
    // Set a timeout to prevent loading state from getting stuck
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }
    loadingTimeoutRef.current = setTimeout(() => {
      console.log('[DEBUG] Loading timeout reached, setting loading to false');
      setLoading(false);
    }, 30000); // 30 second timeout
    
    // Send to Llama via new streaming API
    await sendPromptToLlamaStream(prompt, options);
    setInput('');
    // Don't set loading to false here - let the streaming response completion handle it
  };



  // === STT ADD-ON: Audio recording logic using Web Audio API for raw PCM ===
  const handleAudioRecord = async () => {
    console.log('[DEBUG] handleAudioRecord called, current recording state:', recording);
    
    if (recording) {
      console.log('[DEBUG] Stopping recording manually');
      
      // Clear the auto-stop timeout
      if ((window as any).recordingTimeoutId) {
        clearTimeout((window as any).recordingTimeoutId);
        (window as any).recordingTimeoutId = null;
      }
      
      // Stop Web Audio API recording
      if (recorderRef.current) {
        const processor = recorderRef.current as any;
        if (processor.disconnect) {
          processor.disconnect();
        }
        // Clear the ref
        recorderRef.current = null;
      }
      setRecording(false);
      setSpeechDetected(false);
      
      // Close STT WebSocket connection when manually stopping recording
      closeSTTConnection();
      return;
    }
    
    try {
      console.log('[DEBUG] Starting recording');
      // Create STT WebSocket connection when recording starts
      createSTTConnection();
      
      // Use Web Audio API to get raw PCM data
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new AudioContext({ sampleRate: 24000 });
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(1024, 1, 1);
      
      processor.onaudioprocess = (event) => {
        if (sttWsRef.current && sttWsRef.current.readyState === 1) {
          // Get raw PCM data
          const inputData = event.inputBuffer.getChannelData(0);
          const pcmData = Array.from(inputData); // Convert to regular array
          
          // Send PCM data to STT
          const message = {
            type: 'Audio',
            pcm: pcmData
          };
          const encoded = msgpack.encode(message);
          sttWsRef.current.send(encoded);
          console.log('Sent PCM data to STT, length:', pcmData.length);
        }
      };
      
      source.connect(processor);
      processor.connect(audioContext.destination);
      recorderRef.current = processor;
      setRecording(true);
      setSpeechDetected(true);
      
      const onEnded = () => {
        console.log('[DEBUG] onEnded called');
        
        // Clear the auto-stop timeout
        if ((window as any).recordingTimeoutId) {
          clearTimeout((window as any).recordingTimeoutId);
          (window as any).recordingTimeoutId = null;
        }
        
        if (processor) {
          processor.disconnect();
          source.disconnect();
          stream.getTracks().forEach(track => track.stop());
        }
        setRecording(false);
        setSpeechDetected(false);
        
        // Close STT WebSocket connection when recording stops
        closeSTTConnection();
      };
      
      // Store the timeout ID so we can clear it if user manually stops
      const timeoutId = setTimeout(() => {
        console.log('[DEBUG] Auto-stop timeout triggered');
        if (recording) {
          onEnded();
        }
      }, 10000);
      
      // Store timeout ID in ref so we can clear it
      (window as any).recordingTimeoutId = timeoutId;
      
    } catch (error) {
      console.error('Audio recording error:', error);
      alert('Audio recording error');
      setRecording(false);
      setSpeechDetected(false);
    }
  };

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

  // Function to send prompt to Llama
  // Function to process UI commands from Llama
  const processUICommand = (command: string | any) => {
    console.log('[DEBUG] Processing UI command:', command);
    
    // Handle Function objects (e.g., {"ProactiveAdd":"Sleep"})
    if (typeof command === 'object' && command !== null) {
      if (command.ProactiveAdd === "Sleep") {
        console.log('[DEBUG] ProactiveAdd Sleep detected, showing prompt');
        setShowProactiveSleepPrompt(true);
        return;
      }
    }
    
    // Handle string commands
    if (typeof command === 'string') {
      if (command.startsWith('setMode(') && command.endsWith(')')) {
        const mode = command.slice(8, -1); // Extract value between parentheses
        if (mode === 'dark') {
          if (darkMode) {
            console.log('[DEBUG] Dark mode already set, skipping');
          } else {
            setDarkMode(true);
            console.log('[DEBUG] Set dark mode: true');
          }
        } else if (mode === 'light') {
          if (!darkMode) {
            console.log('[DEBUG] Light mode already set, skipping');
          } else {
            setDarkMode(false);
            console.log('[DEBUG] Set dark mode: false');
          }
        }
      }
      
      if (command.startsWith('addFitness(') && command.endsWith(')')) {
        console.log('[DEBUG] Adding fitness treatment');
        addFitnessTreatment();
      }
      
      if (command.startsWith('removeFitness(') && command.endsWith(')')) {
        console.log('[DEBUG] Removing fitness treatment');
        removeFitnessTreatment();
      }
      
      if (command.startsWith('addSleep(') && command.endsWith(')')) {
        console.log('[DEBUG] Adding sleep treatment');
        addSleepTreatment();
      }
      
      if (command.startsWith('removeSleep(') && command.endsWith(')')) {
        console.log('[DEBUG] Removing sleep treatment');
        removeSleepTreatment();
      }
    }
  };

  // Function to add fitness treatment
  const addFitnessTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot add fitness treatment: no profile available');
      return;
    }
    
    // Check if fitness treatment already exists
    const fitnessExists = profile.treatment.some(treatment => treatment.name === 'Fitness');
    if (fitnessExists) {
      console.log('[DEBUG] Fitness treatment already exists, skipping add');
      return;
    }
    
    const fitnessTreatment = {
      name: 'Fitness',
      medicationList: [],
      dailyChecklist: ['Track calories', 'Track protein', 'Exercise 30 minutes'],
      appointment: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week from now
      recommendations: ['Stay hydrated', 'Eat balanced meals', 'Get adequate rest'],
      dailyCals: 2000,
      dailyProtein: 150
    };

    const updatedProfile = {
      ...profile,
      treatment: [...profile.treatment, fitnessTreatment]
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Added fitness treatment:', fitnessTreatment);
    
    // Automatically sync to local backend after adding treatment
    await syncToLocalBackend();
  };

  // Function to remove fitness treatment
  const removeFitnessTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot remove fitness treatment: no profile available');
      return;
    }
    
    // Check if fitness treatment exists
    const fitnessExists = profile.treatment.some(treatment => treatment.name === 'Fitness');
    if (!fitnessExists) {
      console.log('[DEBUG] Fitness treatment does not exist, skipping remove');
      return;
    }
    
    const updatedProfile = {
      ...profile,
      treatment: profile.treatment.filter(treatment => treatment.name !== 'Fitness')
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Removed fitness treatment');
    
    // Automatically sync to local backend after removing treatment
    await syncToLocalBackend();
  };

  // Function to add sleep treatment
  const addSleepTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot add sleep treatment: no profile available');
      return;
    }
    
    // Check if sleep treatment already exists
    const sleepExists = profile.treatment.some(treatment => treatment.name === 'Sleep');
    if (sleepExists) {
      console.log('[DEBUG] Sleep treatment already exists, skipping add');
      return;
    }
    
    const sleepTreatment = {
      name: 'Sleep',
      medicationList: ['Ibuprofen'],
      dailyChecklist: ['Take medication', 'Walk 30 minutes'],
      appointment: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week from now
      recommendations: ['Stay hydrated', 'Regular exercise'],
      sleepHours: 8,
      sleepQuality: 'Excellent'
    };

    const updatedProfile = {
      ...profile,
      treatment: [...profile.treatment, sleepTreatment]
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Added sleep treatment:', sleepTreatment);
    
    // Automatically sync to local backend after adding treatment
    await syncToLocalBackend();
  };

  // Function to remove sleep treatment
  const removeSleepTreatment = async () => {
    if (!profile) {
      console.log('[DEBUG] Cannot remove sleep treatment: no profile available');
      return;
    }
    
    // Check if sleep treatment exists
    const sleepExists = profile.treatment.some(treatment => treatment.name === 'Sleep');
    if (!sleepExists) {
      console.log('[DEBUG] Sleep treatment does not exist, skipping remove');
      return;
    }
    
    const updatedProfile = {
      ...profile,
      treatment: profile.treatment.filter(treatment => treatment.name !== 'Sleep')
    };

    setProfile(updatedProfile);
    updatePatientProfile(updatedProfile);
    console.log('[DEBUG] Removed sleep treatment');
    
    // Automatically sync to local backend after removing treatment
    await syncToLocalBackend();
  };

  // Make function globally accessible for testing
  (window as any).processUICommand = processUICommand;

  // Test function to manually trigger local backend updates
  const testLocalBackendUpdate = async () => {
    try {
      console.log('[DEBUG] Testing local backend update...');
      
      // Test updating patient profile recommendations
      const response = await fetch('http://localhost:8002/api/healthcare-updates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: 'recommendations',
          data: ['New recommendation 1', 'New recommendation 2', 'Stay active']
        })
      });
      
      if (response.ok) {
        console.log('[DEBUG] Successfully sent test update to local backend');
      } else {
        console.error('[DEBUG] Failed to send test update to local backend');
      }
    } catch (error) {
      console.error('[DEBUG] Error testing local backend update:', error);
    }
  };

  // Make test function globally accessible
  (window as any).testLocalBackendUpdate = testLocalBackendUpdate;

  // Function to check current patient profile from local backend
  const checkLocalBackendProfile = async () => {
    try {
      console.log('[DEBUG] Checking local backend patient profile...');
      
      const response = await fetch('http://localhost:8002/api/patient-profile');
      
      if (response.ok) {
        const profile = await response.json();
        console.log('[DEBUG] Current local backend patient profile:', profile);
        return profile;
      } else {
        console.error('[DEBUG] Failed to get patient profile from local backend');
        return null;
      }
    } catch (error) {
      console.error('[DEBUG] Error checking local backend profile:', error);
      return null;
    }
  };

  // Make check function globally accessible
  (window as any).checkLocalBackendProfile = checkLocalBackendProfile;

  // Function to refresh data from shared-data.js
  const refreshDataFromShared = async () => {
    try {
      console.log('[DEBUG] Refreshing data from shared-data.js...');
      
      // Re-initialize the database with fresh data from shared-data.js
      const { initializeSampleData } = await import('./db');
      await initializeSampleData();
      
      // Reload all data from the refreshed database
      const newProfile = await getPatientProfile();
      const newConversation = await getConversation();
      const newLinks = await getLinks();
      const newGeneral = await getGeneral();
      const newUpdates = await getUpdates();
      const newMemory = await getMemory(); // Fetches memory from IndexedDB
      
      // Update all state variables
      setProfile(newProfile ?? null);
      setConversation(newConversation ?? null);
      setLinks(newLinks?.links ?? null);
      setGeneral(newGeneral?.general ?? null);
      setUpdates(newUpdates?.updates ?? null);
      setMemory(newMemory?.memory ?? null); // Now properly updating memory state
      
      console.log('[DEBUG] Data refreshed successfully');
      console.log('[DEBUG] New memory entries:', newMemory?.memory?.length || 0);
      
      return { newProfile, newConversation, newLinks, newGeneral, newUpdates, newMemory };
    } catch (error) {
      console.error('[DEBUG] Error refreshing data:', error);
      throw error;
    }
  };

  // Make refresh function globally accessible
  (window as any).refreshDataFromShared = refreshDataFromShared;
  
  // Make processUICommand globally accessible
  (window as any).processUICommand = processUICommand;

  // Function to sync data to local backend
  const syncToLocalBackend = async () => {
    try {
      const currentProfile = await getPatientProfile();
      const currentMemory = await getMemory();
      const currentLinks = await getLinks();
      const currentGeneral = await getGeneral();
      const currentUpdates = await getUpdates();
      
      console.log('[DEBUG] Syncing to backend - currentLinks:', currentLinks);
      
      const response = await fetch('http://localhost:8002/api/sync-from-frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patientProfile: currentProfile,
          memory: currentMemory,
          links: currentLinks, // This is already the correct structure { id: 'links', links: {...} }
          general: currentGeneral,
          updates: currentUpdates
        })
      });
      
      if (response.ok) {
        console.log('[DEBUG] Successfully synced data to local backend');
      } else {
        console.error('[DEBUG] Failed to sync data to local backend');
      }
    } catch (error) {
      console.error('[DEBUG] Error syncing to local backend:', error);
    }
  };

  // Make sync function globally accessible
  (window as any).syncToLocalBackend = syncToLocalBackend;
  
  // Global function to clear links (for console use)
  (window as any).clearLinks = async () => {
    console.log('[DEBUG] Clearing links via global function');
    setLinks(null);
    const { updateLinks } = await import('./db');
    await updateLinks({ id: 'links', links: {} });
    console.log('[DEBUG] Links cleared from frontend and IndexedDB');
    
    // Also clear from backend
    try {
      const response = await fetch('http://localhost:8002/api/sync-from-frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          links: { id: 'links', links: {} }
        })
      });
      if (response.ok) {
        console.log('[DEBUG] Successfully cleared links from backend');
      } else {
        console.error('[DEBUG] Failed to clear links from backend');
      }
    } catch (error) {
      console.error('[DEBUG] Error clearing links from backend:', error);
    }
  };
  
  // Global function to set links to any value (for console use)
  (window as any).setLinksValue = async (newLinks: Record<string, any>) => {
    console.log('[DEBUG] Setting links via global function:', newLinks);
    setLinks(newLinks);
    const { updateLinks } = await import('./db');
    await updateLinks({ id: 'links', links: newLinks });
    console.log('[DEBUG] Links set in frontend and IndexedDB');
  };
  
  // Global function to completely reset everything (for when IndexedDB is cleared)
  (window as any).resetEverything = async () => {
    console.log('[DEBUG] Resetting everything - clearing all data');
    
    // Clear frontend state
    setLinks(null);
    setGeneral(null);
    setUpdates(null);
    setMemory(null);
    
    // Clear backend
    try {
      const response = await fetch('http://localhost:8002/api/sync-from-frontend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          links: { id: 'links', links: {} },
          general: { id: 'general', general: {} },
          updates: { id: 'updates', updates: {} },
          memory: { id: 'memory', memory: {} }
        })
      });
      if (response.ok) {
        console.log('[DEBUG] Successfully reset backend data');
      } else {
        console.error('[DEBUG] Failed to reset backend data');
      }
    } catch (error) {
      console.error('[DEBUG] Error resetting backend data:', error);
    }
    
    console.log('[DEBUG] Everything reset - refresh the page to reload from shared-data.js');
  };

  // Global function to force reload from shared data (for testing)
  (window as any).reloadFromSharedData = async () => {
    console.log('[DEBUG] Force reloading from shared data');
    const { initializeSampleData } = await import('./db');
    await initializeSampleData();
    console.log('[DEBUG] Shared data reloaded - refresh the page to see changes');
  };

  // Auto-sync effect: whenever links state changes, sync to backend
  useEffect(() => {
    if (links !== null) { // Only sync if links has been initialized
      console.log('[DEBUG] Links state changed, auto-syncing to backend:', links);
      syncToLocalBackend();
    } else {
      console.log('[DEBUG] Links state is null (cleared), not syncing to backend');
    }
  }, [links]);

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
    fetch(LLAMA_ENDPOINT, {
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
          // Note: No longer forwarding to Unmute WebSocket since we removed it
        }
      })
      .catch(err => console.error('[DEBUG] Llama error:', err));
  }

  // New streaming API function
  async function sendPromptToLlamaStream(prompt: string, options: { updates?: any, links?: any[], general?: any } = {}) {
    console.log('[DEBUG] sendPromptToLlamaStream called');
    if (!profileRef.current) {
      console.warn('[DEBUG] sendPromptToLlamaStream: patientProfile is null');
      return;
    }
    
    const memory = await getMemory();
    
    // Get the last 10 conversations from the current conversation
    const conversation = conversationRef.current;
    const last10Conversations = conversation?.conversation?.slice(-10) || [];
    
    const requestBody: any = {
      prompt,
      patientProfile: profileRef.current,
      memory: memory || { id: 'memory', memory: [] },
      conversation: {
        cid: conversation?.cid || 'conv-001',
        tags: conversation?.tags || [],
        conversation: last10Conversations
      }
    };
    if (options.updates) requestBody.updates = options.updates;

    try {
      // Use fetch with streaming response instead of EventSource
      const response = await fetch(LLAMA_STREAM_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('No response body');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      // Store cleanup function
      const cleanupTimeout = () => {
        reader.cancel();
      };
      (window as any).cleanupStreaming = cleanupTimeout;

      // Read streaming response
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          console.log('[DEBUG] Streaming complete');
          cleanupTimeout();
          break;
        }

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = line.slice(6); // Remove 'data: ' prefix
              if (data.trim()) {
                const parsedChunk = JSON.parse(data);
                handleStreamingChunk(
                  parsedChunk, 
                  setConversation, 
                  updateConversation, 
                  setProfile, 
                  updatePatientProfile, 
                  setLinks, 
                  setGeneral, 
                  setUpdates, 
                  updateUpdates,
                  setStreamingText, 
                  setIsStreaming, 
                  setStreamingError, 
                  setStreamingStatus, 
                  setLoading,
                  setMemory,
                  updateMemory
                );
              }
            } catch (error) {
              console.error('[DEBUG] Error parsing streaming chunk:', error);
            }
          }
        }
      }

    } catch (error) {
      console.error('[DEBUG] Error setting up streaming:', error);
      setStreamingError('Failed to start streaming');
      setIsStreaming(false);
      setLoading(false);
    }
  }

  return (
    <div style={{
      maxWidth: 2000,
      margin: '0 auto',
      padding: 16,
      backgroundColor: darkMode ? '#1a1a1a' : '#ffffff',
      color: darkMode ? '#ffffff' : '#000000',
      minHeight: '100vh'
    }}>
      <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start' }}>
        {/* Left side - Chatbot */}
        <div style={{ flex: 1, maxWidth: 700 }}>
          <h2>AI Health Chatbot</h2>
          <div style={{
            height: 400,
            background: darkMode ? '#2d2d2d' : '#f7f7f7',
            padding: 12,
            borderRadius: 8,
            marginBottom: 12,
            overflowY: 'auto',
            border: darkMode ? '1px solid #404040' : '1px solid #ddd'
          }}>
            {conversation?.conversation.map((msg, idx) => (
              <div key={idx} style={{ textAlign: msg.sender === 'user' ? 'right' : 'left', margin: '8px 0' }}>
                <span style={{
                  display: 'inline-block',
                  background: msg.sender === 'user' ? '#3182ce' : (darkMode ? '#404040' : '#fff'),
                  color: msg.sender === 'user' ? '#fff' : (darkMode ? '#ffffff' : '#222'),
                  borderRadius: 16,
                  padding: '8px 14px',
                  maxWidth: '75%',
                }}>{msg.text}</span>
              </div>
            ))}
          </div>
          {/* Streaming status display */}
          {(isStreaming || streamingStatus || streamingError) && (
            <div style={{
              background: darkMode ? '#2d2d2d' : '#f0f8ff',
              padding: 8,
              borderRadius: 4,
              marginBottom: 8,
              border: darkMode ? '1px solid #404040' : '1px solid #ddd',
              fontSize: 12
            }}>
              {streamingError && (
                <div style={{ color: '#e53e3e', marginBottom: 4 }}>
                  ❌ Error: {streamingError}
                </div>
              )}
              {streamingStatus && (
                <div style={{ color: darkMode ? '#90cdf4' : '#3182ce', marginBottom: 4 }}>
                  🔄 {streamingStatus}
                </div>
              )}
              {isStreaming && (
                <div style={{ color: darkMode ? '#9ae6b4' : '#38a169' }}>
                  ⚡ Streaming in progress...
                </div>
              )}
            </div>
          )}
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={handleAudioRecord}
              disabled={!profile || (loading && !recording)}
              style={{ 
                background: recording ? '#e53e3e' : speechDetected ? '#f6ad55' : '#3182ce', 
                color: '#fff', 
                border: 'none', 
                borderRadius: '50%', 
                width: 40, 
                height: 40, 
                fontSize: 18 
              }}
              aria-label={recording ? 'Stop recording' : 'Record audio'}
            >
              {recording ? '■' : speechDetected ? '🎤' : '🎤'}
            </button>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && input.trim() && !loading) handleSendPrompt(input.trim()); }}
              disabled={loading}
              placeholder="Type your message..."
              style={{
                flex: 1,
                padding: '8px 12px',
                borderRadius: 16,
                border: '1px solid #ccc',
                backgroundColor: darkMode ? '#404040' : '#ffffff',
                color: darkMode ? '#ffffff' : '#000000'
              }}
            />
            <button onClick={() => input.trim() && !loading && handleSendPrompt(input.trim())} disabled={loading || !input.trim()} style={{ background: '#3182ce', color: '#fff', border: 'none', borderRadius: '50%', width: 40, height: 40, fontSize: 18 }}>
              ➤
            </button>
          </div>
          
          {/* Proactive Sleep Prompt */}
          {showProactiveSleepPrompt && (
            <div style={{
              background: darkMode ? '#2d2d2d' : '#fff3cd',
              border: '1px solid #ffeaa7',
              borderRadius: 8,
              padding: 16,
              marginTop: 12,
              textAlign: 'center'
            }}>
              <h4 style={{ margin: '0 0 12px 0', color: darkMode ? '#ffffff' : '#856404' }}>
                Sleep Treatment Recommendation
              </h4>
              <p style={{ margin: '0 0 16px 0', color: darkMode ? '#ffffff' : '#856404' }}>
                Based on your sleep patterns, would you like to add a sleep treatment plan?
              </p>
              <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
                <button
                  onClick={async () => {
                    console.log('[DEBUG] Yes button clicked, current links:', links);
                    addSleepTreatment();
                    // Clear the Sleep section in links since they've been used
                    const updatedLinks = { ...links };
                    console.log('[DEBUG] Updated links before deletion:', updatedLinks);
                    if (updatedLinks && updatedLinks.Sleep) {
                      delete updatedLinks.Sleep;
                      console.log('[DEBUG] Updated links after deletion:', updatedLinks);
                      setLinks(updatedLinks);
                      // Update IndexedDB
                      const { updateLinks } = await import('./db');
                      await updateLinks({ id: 'links', links: updatedLinks });
                      console.log('[DEBUG] IndexedDB updated with new links');
                      
                      // Explicitly sync the cleared links to backend
                      try {
                        const response = await fetch('http://localhost:8002/api/sync-from-frontend', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            links: { id: 'links', links: updatedLinks }
                          })
                        });
                        if (response.ok) {
                          console.log('[DEBUG] Successfully cleared links from backend');
                        } else {
                          console.error('[DEBUG] Failed to clear links from backend');
                        }
                      } catch (error) {
                        console.error('[DEBUG] Error clearing links from backend:', error);
                      }
                    } else {
                      console.log('[DEBUG] No Sleep section found in links or links is null');
                    }
                    setShowProactiveSleepPrompt(false);
                  }}
                  style={{
                    background: '#28a745',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    padding: '8px 16px',
                    cursor: 'pointer'
                  }}
                >
                  Yes, Add Sleep Treatment
                </button>
                <button
                  onClick={async () => {
                    console.log('[DEBUG] No button clicked, clearing Sleep links');
                    // Clear the Sleep section in links
                    const updatedLinks = { ...links };
                    if (updatedLinks && updatedLinks.Sleep) {
                      delete updatedLinks.Sleep;
                      console.log('[DEBUG] Updated links after Sleep deletion:', updatedLinks);
                      setLinks(updatedLinks);
                      // Update IndexedDB
                      const { updateLinks } = await import('./db');
                      await updateLinks({ id: 'links', links: updatedLinks });
                      console.log('[DEBUG] IndexedDB updated with cleared links');
                      
                      // Explicitly sync the cleared links to backend
                      try {
                        const response = await fetch('http://localhost:8002/api/sync-from-frontend', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            links: { id: 'links', links: updatedLinks }
                          })
                        });
                        if (response.ok) {
                          console.log('[DEBUG] Successfully cleared links from backend');
                        } else {
                          console.error('[DEBUG] Failed to clear links from backend');
                        }
                      } catch (error) {
                        console.error('[DEBUG] Error clearing links from backend:', error);
                      }
                    } else {
                      console.log('[DEBUG] No Sleep section found in links or links is null');
                    }
                    setShowProactiveSleepPrompt(false);
                  }}
                  style={{
                    background: '#dc3545',
                    color: '#fff',
                    border: 'none',
                    borderRadius: 6,
                    padding: '8px 16px',
                    cursor: 'pointer'
                  }}
                >
                  No, Dismiss
                </button>
              </div>
            </div>
          )}
        </div>
        {/* Right side - Patient Profile and other info */}
        <div style={{
          width: 1000,
          flexShrink: 0,
          display: 'flex',
          gap: 12
        }}>
          <div style={{
            flex: 0.5
          }}>
            {/* Links, General */}
                         <div style={{
               background: darkMode ? '#2d2d2d' : '#eef',
               padding: 12,
               borderRadius: 8,
               marginBottom: 12,
               border: darkMode ? '1px solid #404040' : 'none'
             }}>
               <h4>Links</h4>
               {links ? (
                 <div style={{ fontSize: 12, color: darkMode ? '#ffffff' : '#000000' }}>
                   {Object.entries(links as Record<string, any>).map(([key, value]) => (
                     <div key={key} style={{ 
                       marginBottom: 8, 
                       padding: 8, 
                       borderRadius: 4,
                       background: darkMode ? '#404040' : '#f0f8ff',
                       borderLeft: '3px solid #3182ce'
                     }}>
                       <strong style={{ color: '#3182ce' }}>{key}:</strong>
                       <div style={{ marginTop: 4 }}>
                         {typeof value === 'object' ? (
                           Object.entries(value).map(([subKey, subValue]) => (
                             <div key={subKey} style={{ marginLeft: 8, marginBottom: 2 }}>
                               <span style={{ color: darkMode ? '#90cdf4' : '#2b6cb0' }}>{subKey}:</span> {String(subValue)}
                             </div>
                           ))
                         ) : (
                           <span>{String(value)}</span>
                         )}
                       </div>
                     </div>
                   ))}
                 </div>
               ) : (
                 <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No links available</p>
               )}
             </div>
                         <div style={{
               background: darkMode ? '#2d2d2d' : '#efe',
               padding: 12,
               borderRadius: 8,
               marginBottom: 12,
               border: darkMode ? '1px solid #404040' : 'none'
             }}>
               <h4>General</h4>
               {general ? (
                 <div style={{ fontSize: 12, color: darkMode ? '#ffffff' : '#000000' }}>
                   {Object.entries(general as Record<string, any>).map(([key, value]) => (
                     <div key={key} style={{ 
                       marginBottom: 8, 
                       padding: 8, 
                       borderRadius: 4,
                       background: darkMode ? '#404040' : '#f0fff0',
                       borderLeft: '3px solid #38a169'
                     }}>
                       <strong style={{ color: '#38a169' }}>{key}:</strong>
                       <div style={{ marginTop: 4 }}>
                         {Array.isArray(value) ? (
                           value.map((item, idx) => (
                             <div key={idx} style={{ marginLeft: 8, marginBottom: 2 }}>
                               • {String(item)}
                             </div>
                           ))
                         ) : typeof value === 'object' ? (
                           Object.entries(value).map(([subKey, subValue]) => (
                             <div key={subKey} style={{ marginLeft: 8, marginBottom: 2 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>{subKey}:</span> {String(subValue)}
                             </div>
                           ))
                         ) : (
                           <span>{String(value)}</span>
                         )}
                       </div>
                     </div>
                   ))}
                 </div>
               ) : (
                 <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No general information available</p>
               )}
             </div>
          </div>
          {/* Updates */}
          <div style={{
            flex: 0.7
          }}>
                         <div style={{
               height: 300,
               background: darkMode ? '#2d2d2d' : '#ffe',
               padding: 12,
               borderRadius: 8,
               marginBottom: 12,
               border: darkMode ? '1px solid #404040' : 'none',
               overflowY: 'auto'
             }}>
               <h4>Updates</h4>
               {updates ? (
                 <div style={{ fontSize: 12, color: darkMode ? '#ffffff' : '#000000' }}>
                   {Array.isArray(updates) ? (
                     updates.map((update, idx) => (
                       <div key={idx} style={{ 
                         marginBottom: 8, 
                         padding: 8, 
                         borderRadius: 4,
                         background: darkMode ? '#404040' : '#fffbf0',
                         borderLeft: '3px solid #d69e2e'
                       }}>
                         {update.datetime && (
                           <div style={{ fontSize: 10, color: darkMode ? '#999' : '#666', marginBottom: 4 }}>
                             {update.datetime}
                           </div>
                         )}
                         <div style={{ wordBreak: 'break-word' }}>
                           {update.text || String(update)}
                         </div>
                       </div>
                     ))
                   ) : (
                     <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0 }}>{JSON.stringify(updates, null, 2)}</pre>
                   )}
                 </div>
               ) : (
                 <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No updates available</p>
               )}
             </div>
                         <div style={{
               height: 300,
               background: darkMode ? '#2d2d2d' : '#fef',
               padding: 12,
               borderRadius: 8,
               marginBottom: 12,
               border: darkMode ? '1px solid #404040' : 'none',
               overflowY: 'auto'
             }}>
               <h4>Memory</h4>
               {memory ? (
                 <div style={{ fontSize: 12, color: darkMode ? '#ffffff' : '#000000' }}>
                   {Array.isArray(memory) ? (
                     memory.map((item, idx) => (
                       <div key={idx} style={{ 
                         marginBottom: 8, 
                         padding: 8, 
                         borderRadius: 4,
                         background: darkMode ? '#404040' : '#f0f0ff',
                         borderLeft: '3px solid #805ad5'
                       }}>
                         {item.datetime && (
                           <div style={{ fontSize: 10, color: darkMode ? '#999' : '#666', marginBottom: 4 }}>
                             {item.datetime}
                           </div>
                         )}
                         <div style={{ wordBreak: 'break-word' }}>
                           {item.text || String(item)}
                         </div>
                       </div>
                     ))
                   ) : (
                     <pre style={{ fontSize: 12, whiteSpace: 'pre-wrap', margin: 0 }}>{JSON.stringify(memory, null, 2)}</pre>
                   )}
                 </div>
               ) : (
                 <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No memory available</p>
               )}
             </div>
          </div>
          {/* Patient Profile */}
          <div style={{
            flex: 1
          }}>
                         {profile && (
               <div style={{
                 background: darkMode ? '#2d2d2d' : '#eef',
                 padding: 12,
                 borderRadius: 8,
                 marginBottom: 12,
                 border: darkMode ? '1px solid #404040' : 'none'
               }}>
                 <h4>Patient Profile</h4>
                 <div style={{ fontSize: 12, color: darkMode ? '#ffffff' : '#000000' }}>
                   <div style={{ 
                     marginBottom: 8, 
                     padding: 8, 
                     borderRadius: 4,
                     background: darkMode ? '#404040' : '#f0f8ff',
                     borderLeft: '3px solid #3182ce'
                   }}>
                     <strong style={{ color: '#3182ce' }}>Basic Info:</strong>
                     <div style={{ marginTop: 4, marginLeft: 8 }}>
                       <div><span style={{ color: darkMode ? '#90cdf4' : '#2b6cb0' }}>Name:</span> {profile.name}</div>
                       <div><span style={{ color: darkMode ? '#90cdf4' : '#2b6cb0' }}>Age:</span> {profile.age}</div>
                       <div><span style={{ color: darkMode ? '#90cdf4' : '#2b6cb0' }}>Blood Type:</span> {profile.bloodType}</div>
                       {profile.allergies && profile.allergies.length > 0 && (
                         <div>
                           <span style={{ color: darkMode ? '#90cdf4' : '#2b6cb0' }}>Allergies:</span> {profile.allergies.join(', ')}
                         </div>
                       )}
                     </div>
                   </div>
                   
                   {profile.treatment && profile.treatment.length > 0 && (
                     <div style={{ 
                       marginBottom: 8, 
                       padding: 8, 
                       borderRadius: 4,
                       background: darkMode ? '#404040' : '#f0fff0',
                       borderLeft: '3px solid #38a169'
                     }}>
                       <strong style={{ color: '#38a169' }}>Treatments:</strong>
                       {profile.treatment.map((treatment, idx) => (
                         <div key={idx} style={{ marginTop: 8, marginLeft: 8 }}>
                           <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{treatment.name}</div>
                           {treatment.medicationList && treatment.medicationList.length > 0 && (
                             <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Medications:</span> {treatment.medicationList.join(', ')}
                             </div>
                           )}
                           {treatment.appointment && (
                             <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Appointment:</span> {treatment.appointment}
                             </div>
                           )}
                           {treatment.dailyChecklist && treatment.dailyChecklist.length > 0 && (
                             <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Daily Checklist:</span>
                               {treatment.dailyChecklist.map((item, itemIdx) => (
                                 <div key={itemIdx} style={{ marginLeft: 8 }}>• {item}</div>
                               ))}
                             </div>
                           )}
                           {treatment.recommendations && treatment.recommendations.length > 0 && (
                             <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Recommendations:</span>
                               {treatment.recommendations.map((rec, recIdx) => (
                                 <div key={recIdx} style={{ marginLeft: 8 }}>• {rec}</div>
                               ))}
                             </div>
                           )}
                           {treatment.sleepHours && (
                              <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Sleep Hours:</span> {treatment.sleepHours}
                              </div>
                           )}
                           {treatment.sleepQuality && (
                              <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Sleep Quality:</span> {treatment.sleepQuality}
                              </div>
                           )}
                           {treatment.dailyCals && (
                              <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Daily Calories:</span> {treatment.dailyCals}
                              </div>
                           )}
                           {treatment.dailyProtein && (
                              <div style={{ marginBottom: 4 }}>
                               <span style={{ color: darkMode ? '#9ae6b4' : '#2f855a' }}>Daily Protein:</span> {treatment.dailyProtein}
                              </div>
                           )}
                         </div>
                       ))}
                     </div>
                   )}
                 </div>
               </div>
             )}
          </div>
          {/* Last 10 Conversations */}
          <div style={{
            flex: 0.5
          }}>
            <div style={{
              background: darkMode ? '#2d2d2d' : '#fdf',
              padding: 12,
              borderRadius: 8,
              marginBottom: 12,
              border: darkMode ? '1px solid #404040' : 'none'
            }}>
               <h4>Last 3 Conversations</h4>
               {conversation?.conversation?.slice(-6) ? (
                 <div style={{ fontSize: 12, color: darkMode ? '#ffffff' : '#000000' }}>
                   {conversation.conversation.slice(-6).map((msg, idx) => (
                    <div key={idx} style={{ 
                      marginBottom: 8, 
                      padding: 4, 
                      borderRadius: 4,
                      background: msg.sender === 'user' ? (darkMode ? '#404040' : '#e6f3ff') : (darkMode ? '#333333' : '#f0f0f0'),
                      borderLeft: `3px solid ${msg.sender === 'user' ? '#3182ce' : '#38a169'}`
                    }}>
                      <strong style={{ color: msg.sender === 'user' ? '#3182ce' : '#38a169' }}>
                        {msg.sender === 'user' ? 'User' : 'AI'}:
                      </strong>
                      <div style={{ marginTop: 2, wordBreak: 'break-word' }}>
                        {msg.text}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ fontSize: 12, color: darkMode ? '#999' : '#666', margin: 0, fontStyle: 'italic' }}>No conversations available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;