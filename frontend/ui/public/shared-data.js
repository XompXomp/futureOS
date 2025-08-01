// Shared data that matches the IndexedDB structure
// This file can be imported by both the React app and local backend

const sharedPatientProfile = {
  uid: 'user-001',
  name: 'Jane Smith',
  age: 29,
  bloodType: 'A-',
  allergies: ['Peanuts'],
  treatment: [
    {
      name: 'Sleep',
      medicationList: ['Ibuprofen'],
      dailyChecklist: ['Take medication', 'Walk 30 minutes'],
      appointment: '2024-08-15T09:00:00',
      recommendations: ['Stay hydrated', 'Regular exercise'],
      sleepHours: 8,
      sleepQuality: 'Excellent',
      /*
      name: 'Fitness',
      medicationList: [],
      dailyChecklist: ['Track calories', 'Track protein', 'Exercise 30 minutes'],
      appointment: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(), // 1 week from now
      recommendations: ['Stay hydrated', 'Eat balanced meals', 'Get adequate rest'],
      dailyCals: 2000,
      dailyProtein: 150 */
    }
  ],
};

const sharedMemory = {
  id: 'memory',
  memory: [
    {
      datetime: '01_07_25_09_00',
      text: "Patient said they can't sleep"
    },
    {
      datetime: '02_07_25_22_15',
      text: 'Wakes up multiple times'
    },
    {
      datetime: '03_07_25_08_30',
      text: 'My sleep was disrupted multiple times tonight'
    },
    {
      datetime: '04_07_25_07_15',
      text: 'I am not energized in the morning'
    },
    {
      datetime: '05_07_25_14_20',
      text: 'I was sleepy the whole day'
    },
    {
      datetime: '06_07_25_03_45',
      text: 'I could not fall asleep until 3am'
    },
    {
      datetime: '07_07_25_06_30',
      text: 'I woke up at least 5 times last night'
    },
    {
      datetime: '08_07_25_02_15',
      text: 'I had nightmares and woke up sweating'
    },
    {
      datetime: '09_07_25_23_45',
      text: 'It takes a long time for me to fall asleep'
    }
  ],
};

const sharedLinks = {
  id: 'links',
  links: {
    Sleep: {
      'disturbed sleep': 0.6,
      'tired in morning': 0.3
    }
  },
};

const sharedGeneral = {
  id: 'general',
  general: {
    EmotionalCues: ["anxious", "tired"],
    Tone: "reflective",
    Engagement: "high",
    Hesitation: "minimal",
    NuancedFindings: ["User shows progress in managing stress"],
    trend_analysis:""
  },
};

const sharedUpdates = {
  id: 'updates',
  updates: [
    {
      datetime: '01_07_25_09_00',
      text: 'Initial consultation - Patient reports sleep disturbances'
    },
    {
      datetime: '01_07_25_14_30',
      text: 'Sleep hours changed from 7 to 9 hours'
    },
    {
      datetime: '01_07_25_15_45',
      text: 'Sleep quality changed from Poor to Excellent'
    },
    {
      datetime: '02_07_25_10_15',
      text: 'Melatonin added to prescriptions'
    },
    {
      datetime: '02_07_25_11_20',
      text: 'Appointment scheduled for 2025-08-15T09:00:00'
    },
    {
      datetime: '02_07_25_16_30',
      text: 'Daily checklist updated: Added "Take melatonin 30 min before bed"'
    },
    {
      datetime: '03_07_25_08_45',
      text: 'Patient reported improved sleep quality - reduced wake-ups from 5 to 2 times per night'
    },
    {
      datetime: '03_07_25_12_00',
      text: 'New recommendation added: "Avoid caffeine after 2 PM"'
    },
    {
      datetime: '03_07_25_14_20',
      text: 'Sleep tracking enabled - monitoring sleep patterns'
    },
    {
      datetime: '04_07_25_09_30',
      text: 'Follow-up appointment scheduled for 2025-08-22T10:00:00'
    },
    {
      datetime: '04_07_25_11_15',
      text: 'Patient reported feeling more rested in mornings'
    },
    {
      datetime: '04_07_25_16_45',
      text: 'Sleep hygiene recommendations updated: Added "Keep bedroom temperature at 65-67°F"'
    },
    {
      datetime: '05_07_25_10_00',
      text: 'Melatonin dosage adjusted from 3mg to 5mg'
    },
    {
      datetime: '05_07_25_13_30',
      text: 'New medication added: Magnesium supplement for muscle relaxation'
    },
    {
      datetime: '05_07_25_15_20',
      text: 'Patient achieved 8 hours of continuous sleep for first time in 3 months'
    },
    {
      datetime: '06_07_25_08_15',
      text: 'Sleep quality rating improved from Good to Excellent'
    },
    {
      datetime: '06_07_25_12_30',
      text: 'Daily exercise routine added to treatment plan: 30 min walk before dinner'
    },
    {
      datetime: '06_07_25_14_45',
      text: 'Stress management techniques recommended: Deep breathing exercises'
    },
    {
      datetime: '07_07_25_09_00',
      text: 'Patient reported significant improvement in daytime energy levels'
    },
    {
      datetime: '07_07_25_11_30',
      text: 'Sleep tracking data shows consistent 7-8 hour sleep pattern'
    },
    {
      datetime: '07_07_25_16_00',
      text: 'Treatment plan updated: Gradual reduction of melatonin dosage planned'
    }
  ],
};

const sharedConversation = {
  cid: 'conv-001',
  tags: ['greeting'],
  conversation: [
    { sender: 'user', text: 'Hello' },
    { sender: 'ai', text: 'Hello, how can I help you today?' },
  ],
};

// Export for Node.js (local backend)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    sharedPatientProfile,
    sharedMemory,
    sharedLinks,
    sharedGeneral,
    sharedUpdates,
    sharedConversation
  };
}

// Export for browser (React app)
if (typeof window !== 'undefined') {
  window.sharedData = {
    sharedPatientProfile,
    sharedMemory,
    sharedLinks,
    sharedGeneral,
    sharedUpdates,
    sharedConversation
  };
} 