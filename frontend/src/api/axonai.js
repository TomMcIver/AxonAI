const BASE_URL = process.env.REACT_APP_API_URL || 'https://73edpnyeqs6gl3eh4gyfnwoji40ldhgo.lambda-url.ap-southeast-2.on.aws';

async function fetchAPI(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  console.log(`[AxonAI API] ${options.method || 'GET'} ${url}`);
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    console.log(`[AxonAI API] ${url} → ${response.status} ${response.statusText}`);
    if (!response.ok) {
      const errorText = await response.text().catch(() => '');
      console.error(`[AxonAI API] Error body:`, errorText);
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }
    const data = await response.json();
    console.log(`[AxonAI API] ${endpoint} response:`, data);
    return data;
  } catch (err) {
    console.error(`[AxonAI API] ${url} failed:`, err.message);
    throw err;
  }
}

// Health
export function getHealth() {
  return fetchAPI('/');
}

// Student endpoints
export function getStudentDashboard(studentId) {
  return fetchAPI(`/student/${studentId}/dashboard`);
}

export function getStudentMastery(studentId) {
  return fetchAPI(`/student/${studentId}/mastery`);
}

export function getStudentFlags(studentId) {
  return fetchAPI(`/student/${studentId}/flags`);
}

export function getStudentPedagogy(studentId) {
  return fetchAPI(`/student/${studentId}/pedagogy`);
}

export function getStudentConversations(studentId, limit = 20, offset = 0) {
  return fetchAPI(`/student/${studentId}/conversations?limit=${limit}&offset=${offset}`);
}

export function getStudentPredictions(studentId) {
  return fetchAPI(`/student/${studentId}/predictions`);
}

export function getStudentInsights(studentId) {
  return fetchAPI(`/student/${studentId}/insights`);
}

// Conversation messages
export function getConversationMessages(conversationId) {
  return fetchAPI(`/conversation/${conversationId}/messages`);
}

// Class endpoints
export function getClassOverview(classId) {
  return fetchAPI(`/class/${classId}/overview`);
}

export function getClassInterventions(classId) {
  return fetchAPI(`/class/${classId}/interventions`);
}

// Concepts / Knowledge Graph
export function getConcepts(subject) {
  return fetchAPI(`/concepts/${subject}`);
}

// Predictions
export function predictRisk(studentId) {
  return fetchAPI('/predict/risk', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId }),
  });
}

export function predictMastery(studentId, conceptId) {
  return fetchAPI('/predict/mastery', {
    method: 'POST',
    body: JSON.stringify({ student_id: studentId, concept_id: conceptId }),
  });
}

// Teacher AI insights — GPT-4o generated summaries
export const getTeacherAIInsights = async (studentId) => {
  try {
    const res = await fetch(`${BASE_URL}/student/${studentId}/ai-insights`);
    console.log(`[AxonAI API] /student/${studentId}/ai-insights → ${res.status}`);
    return res.ok ? res.json() : null;
  } catch (err) {
    console.error(`[AxonAI API] ai-insights failed:`, err.message);
    return null;
  }
};

// Wellbeing context
export const getStudentWellbeing = async (studentId) => {
  try {
    const res = await fetch(`${BASE_URL}/student/${studentId}/wellbeing`);
    console.log(`[AxonAI API] /student/${studentId}/wellbeing → ${res.status}`);
    return res.ok ? res.json() : null;
  } catch (err) {
    console.error(`[AxonAI API] wellbeing failed:`, err.message);
    return null;
  }
};

// Pedagogical memory (what approaches have worked)
export const getPedagogicalMemory = async (studentId) => {
  try {
    const res = await fetch(`${BASE_URL}/student/${studentId}/pedagogical-memory`);
    console.log(`[AxonAI API] /student/${studentId}/pedagogical-memory → ${res.status}`);
    return res.ok ? res.json() : null;
  } catch (err) {
    console.error(`[AxonAI API] pedagogical-memory failed:`, err.message);
    return null;
  }
};
