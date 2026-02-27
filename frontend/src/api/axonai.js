const BASE_URL = process.env.REACT_APP_API_URL || 'https://73edpnyeqs6gl3eh4gyfnwoji40ldhgo.lambda-url.ap-southeast-2.on.aws';

async function fetchAPI(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
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

// Conversation messages
export function getConversationMessages(conversationId) {
  return fetchAPI(`/conversation/${conversationId}/messages`);
}

// Class endpoints
export function getClassOverview(classId) {
  return fetchAPI(`/class/${classId}/overview`);
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
