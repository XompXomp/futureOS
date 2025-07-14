// IndexedDB utility for careAI

const DB_NAME = "careAI";
const DB_VERSION = 1;

function openDB() {
  return new Promise((resolve, reject) => {
    const request = window.indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = function (event) {
      const db = event.target.result;
      if (!db.objectStoreNames.contains("patient_profile")) {
        db.createObjectStore("patient_profile", { keyPath: "id" });
      }
      if (!db.objectStoreNames.contains("conversation_history")) {
        const convoStore = db.createObjectStore("conversation_history", { keyPath: "id", autoIncrement: true });
        convoStore.createIndex("timestamp", "timestamp", { unique: false });
      }
    };
    request.onsuccess = function (event) {
      resolve(event.target.result);
    };
    request.onerror = function (event) {
      reject(event.target.error);
    };
  });
}

// Patient Profile
export async function savePatientProfile(profile) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("patient_profile", "readwrite");
    const store = tx.objectStore("patient_profile");
    store.put({ ...profile, id: "main" });
    tx.oncomplete = () => resolve();
    tx.onerror = (e) => reject(e.target.error);
  });
}

export async function getPatientProfile() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("patient_profile", "readonly");
    const store = tx.objectStore("patient_profile");
    const req = store.get("main");
    req.onsuccess = () => resolve(req.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

export async function initializePatientProfile() {
  const existing = await getPatientProfile();
  if (!existing) {
    const defaultProfile = {
      id: "main",
      name: "",
      age: "",
      treatment: {
        treatmentName: "",
        sleepHours: [],
        sleepRatings: [],
        recommendations: [],
        medications: []
      }
    };
    await savePatientProfile(defaultProfile);
    return defaultProfile;
  }
  return existing;
}

// Conversation History
export async function addConversationEntry(entry) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("conversation_history", "readwrite");
    const store = tx.objectStore("conversation_history");
    store.add(entry);
    tx.oncomplete = () => resolve();
    tx.onerror = (e) => reject(e.target.error);
  });
}

export async function getAllConversations() {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("conversation_history", "readonly");
    const store = tx.objectStore("conversation_history");
    const req = store.getAll();
    req.onsuccess = () => resolve(req.result);
    req.onerror = (e) => reject(e.target.error);
  });
}

export async function createConversationEntry(entry) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("conversation_history", "readwrite");
    const store = tx.objectStore("conversation_history");
    const req = store.add(entry);
    req.onsuccess = () => resolve(req.result); // returns the new entry's id
    req.onerror = (e) => reject(e.target.error);
  });
}

export async function updateConversationEntry(id, updatedEntry) {
  const db = await openDB();
  return new Promise((resolve, reject) => {
    const tx = db.transaction("conversation_history", "readwrite");
    const store = tx.objectStore("conversation_history");
    store.put({ ...updatedEntry, id });
    tx.oncomplete = () => resolve();
    tx.onerror = (e) => reject(e.target.error);
  });
} 